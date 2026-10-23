#!/usr/bin/env python3
"""
Hazard IDENTIFICATION evaluation — image-level classification.

For each image, compare the SET of predicted hazard categories against the SET
of GT categories. Count TP, FP, FN per image, then micro-average.

No bounding boxes involved — purely category-level.
"""

import json, os, re, csv
from collections import defaultdict, Counter
import openpyxl

# ── Paths / system manifest (CLI-driven, package-relative defaults) ──────────
import argparse
from eval_config import (
    GT_JSON_DEFAULT, RESULTS_DIR, discover_systems,
    map_gt_category, map_pred_category,
)

_parser = argparse.ArgumentParser(
    description="Hazard identification evaluation (image-level, micro-averaged)."
)
_parser.add_argument("--gt", default=str(GT_JSON_DEFAULT),
                     help="Path to the COCO ground-truth JSON.")
_parser.add_argument("--predictions-dir", default=None,
                     help="Directory of prediction workbooks "
                          "(defaults to the bundled predictions/ directory).")
_parser.add_argument("--out-dir", default=str(RESULTS_DIR / "identification"),
                     help="Directory for the identification_results.csv output.")
_args = _parser.parse_args()

GT_JSON = _args.gt
OUT_DIR = _args.out_dir
EXPERIMENTS = discover_systems(_args.predictions_dir)
os.makedirs(OUT_DIR, exist_ok=True)

# ── GT category name → canonical 7-class taxonomy ────────────────────────────
# Same mapping used in grounding_eval.py and cataware scripts
CAT_MAP_GT = {
    "Electrical Hazard": "Electrocution_Hazard",
    "Equipment and Machine Safety": "CaughtInBetween_hazard",
    "Fall from Height": "Fall_Hazard",
    "Falling Object Hazard": "StruckBy_Hazard",
    "Housekeeping": "Housekeeping_Storage",
    "Slip and Trip Hazard": "Housekeeping_Storage",
    "PPE Deficiency": "PPE_Violation",
    "Signage and Communication": "Other",
    "Other": "Other",
    "Hazards": "Other",
}

CANONICAL_CATS = sorted(set(CAT_MAP_GT.values()))
# ['CaughtInBetween_hazard', 'Electrocution_Hazard', 'Fall_Hazard',
#  'Housekeeping_Storage', 'Other', 'PPE_Violation', 'StruckBy_Hazard']


# ── Pred category mapper ──────────────────────────────────────────────────────
# map_pred_category is imported from the shared hazard taxonomy
# (code/inference/shared/hazard_taxonomy.py) via eval_config, so evaluation and
# inference use one category-mapping source of truth. This is the same mapper
# used to produce the metrics reported in the paper.


# ── Image name normalizer ────────────────────────────────────────────────────
def normalize(name):
    s = os.path.basename(str(name).strip())
    s = re.sub(r"\.rf\.[a-zA-Z0-9]{6,}\.[a-zA-Z0-9]+$", "", s)
    s = re.sub(r"_(png|jpg|jpeg|webp)$", r".\1", s, flags=re.IGNORECASE)
    base, ext = os.path.splitext(s)
    return base + ext.lower() if ext else s


# ── Load GT: per-image set of canonical categories ────────────────────────────
with open(GT_JSON, encoding="utf-8") as f:
    coco = json.load(f)

coco_cat_map = {c["id"]: c["name"] for c in coco["categories"]}
img_id_to_name = {img["id"]: normalize(img["file_name"]) for img in coco["images"]}

gt_by_img = defaultdict(set)  # norm_name → set of canonical categories
for ann in coco["annotations"]:
    name = img_id_to_name[ann["image_id"]]
    raw_cat = coco_cat_map[ann["category_id"]]
    canonical = map_gt_category(raw_cat)
    gt_by_img[name].add(canonical)

# Also include images with 0 annotations as empty sets (shouldn't exist here, but safe)
for img in coco["images"]:
    name = normalize(img["file_name"])
    if name not in gt_by_img:
        gt_by_img[name] = set()

print(f"GT loaded: {len(gt_by_img)} images")
gt_cat_totals = Counter()
for cats in gt_by_img.values():
    for c in cats:
        gt_cat_totals[c] += 1
print(f"GT category instance counts (image-level):")
for cat in CANONICAL_CATS:
    print(f"  {cat:<30}: {gt_cat_totals[cat]}")
total_gt_instances = sum(gt_cat_totals.values())
print(f"  TOTAL: {total_gt_instances}")


# ── Load predictions: per-image set of mapped categories ──────────────────────
def load_pred_categories(xlsx_path):
    """Returns pred_by_img: norm_name → set of mapped canonical categories."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["Full_Results"]
    rows = list(ws.iter_rows(values_only=True))
    header = list(rows[0])
    name_col = header.index("image_name")
    hazards_col = header.index("hazards_json")

    pred_by_img = defaultdict(set)
    all_raw = []

    for row in rows[1:]:
        if row[name_col] is None:
            continue
        norm = normalize(str(row[name_col]))
        hazards_raw = row[hazards_col]
        if hazards_raw is None or str(hazards_raw).strip() in ("", "[]"):
            # Model predicted no hazards for this image → empty set (no categories)
            pred_by_img[norm]  # ensure key exists with empty set
            continue
        try:
            hazards = json.loads(str(hazards_raw))
        except json.JSONDecodeError:
            pred_by_img[norm]
            continue
        for h in hazards:
            # Skip explicit no-hazard markers
            if h.get("hazard", "").upper() in ("NO_HAZARD", "COMPLIANT"):
                continue
            if h.get("category", "").upper() in ("COMPLIANT",):
                continue
            raw_cat = h.get("category", "") or h.get("hazard", "") or ""
            all_raw.append(raw_cat)
            mapped = map_pred_category(raw_cat)
            if mapped != "UNMAPPED":
                pred_by_img[norm].add(mapped)
            # UNMAPPED categories are NOT added to the set — they can't match any GT

    wb.close()
    return pred_by_img, all_raw


# ── Evaluate each experiment ──────────────────────────────────────────────────
master_rows = []

print(f"\n{'='*90}")
print(f"  HAZARD IDENTIFICATION EVALUATION (Image-Level, Micro-Averaged)")
print(f"  GT: {len(gt_by_img)} images, {total_gt_instances} category instances across 7 classes")
print(f"{'='*90}")

for exp_name, xlsx_path in EXPERIMENTS:
    pred_by_img, all_raw = load_pred_categories(xlsx_path)

    # How many pred images match GT images?
    shared = set(gt_by_img.keys()) & set(pred_by_img.keys())
    gt_only = set(gt_by_img.keys()) - set(pred_by_img.keys())
    pred_only = set(pred_by_img.keys()) - set(gt_by_img.keys())

    # Global TP, FP, FN
    total_tp = 0; total_fp = 0; total_fn = 0

    # Per-category TP, FP, FN
    cat_tp = defaultdict(int)
    cat_fp = defaultdict(int)
    cat_fn = defaultdict(int)

    # Images in GT that have no predictions → all GT cats are FN
    for img in gt_only:
        gt_cats = gt_by_img[img]
        total_fn += len(gt_cats)
        for c in gt_cats:
            cat_fn[c] += 1

    # Shared images: set comparison
    for img in shared:
        gt_cats = gt_by_img[img]
        pred_cats = pred_by_img[img]

        tp = gt_cats & pred_cats       # correctly identified
        fp = pred_cats - gt_cats       # predicted but not in GT
        fn = gt_cats - pred_cats       # in GT but not predicted

        total_tp += len(tp)
        total_fp += len(fp)
        total_fn += len(fn)

        for c in tp:
            cat_tp[c] += 1
        for c in fp:
            cat_fp[c] += 1
        for c in fn:
            cat_fn[c] += 1

    # Images only in predictions (pred_only) — all pred cats are FP
    # (These are images that don't appear in GT at all — shouldn't happen
    #  since GT has all 105 images, but handle it anyway)
    for img in pred_only:
        pred_cats = pred_by_img[img]
        total_fp += len(pred_cats)
        for c in pred_cats:
            cat_fp[c] += 1

    # Micro-averaged metrics
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    # Count raw pred categories
    mapped_counter = Counter(map_pred_category(r) for r in all_raw)

    print(f"\n{'#'*70}")
    print(f"  {exp_name}")
    print(f"{'#'*70}")
    print(f"  Shared images: {len(shared)} | GT-only: {len(gt_only)} | Pred-only: {len(pred_only)}")
    print(f"  Total raw hazard entries: {len(all_raw)}")
    print(f"  Mapped pred distribution: {dict(mapped_counter.most_common())}")
    print()
    print(f"  ┌─────────────────────────────────────────────┐")
    print(f"  │  MICRO-AVERAGED IDENTIFICATION METRICS      │")
    print(f"  │  TP = {total_tp:>4}   FP = {total_fp:>4}   FN = {total_fn:>4}          │")
    print(f"  │  Precision = {precision:.1%}                        │")
    print(f"  │  Recall    = {recall:.1%}                        │")
    print(f"  │  F1        = {f1:.1%}                        │")
    print(f"  └─────────────────────────────────────────────┘")

    print(f"\n  Per-Category Breakdown:")
    print(f"  {'Category':<28} {'GT imgs':>7} {'TP':>5} {'FP':>5} {'FN':>5} {'Prec':>7} {'Recall':>7} {'F1':>7}")
    for cat in CANONICAL_CATS:
        tp_c = cat_tp.get(cat, 0)
        fp_c = cat_fp.get(cat, 0)
        fn_c = cat_fn.get(cat, 0)
        gt_c = gt_cat_totals.get(cat, 0)
        p_c = tp_c / (tp_c + fp_c) if (tp_c + fp_c) else 0
        r_c = tp_c / (tp_c + fn_c) if (tp_c + fn_c) else 0
        f1_c = 2 * p_c * r_c / (p_c + r_c) if (p_c + r_c) else 0
        print(f"  {cat:<28} {gt_c:>7} {tp_c:>5} {fp_c:>5} {fn_c:>5} {p_c:>6.0%}  {r_c:>6.0%}  {f1_c:>6.0%}")

    # Store for CSV
    row = {
        "experiment": exp_name,
        "TP": total_tp, "FP": total_fp, "FN": total_fn,
        "precision": f"{precision:.4f}",
        "recall": f"{recall:.4f}",
        "f1": f"{f1:.4f}",
        "total_gt_instances": total_gt_instances,
        "shared_images": len(shared),
        "gt_only_images": len(gt_only),
    }
    for cat in CANONICAL_CATS:
        tp_c = cat_tp.get(cat, 0)
        fp_c = cat_fp.get(cat, 0)
        fn_c = cat_fn.get(cat, 0)
        p_c = tp_c / (tp_c + fp_c) if (tp_c + fp_c) else 0
        r_c = tp_c / (tp_c + fn_c) if (tp_c + fn_c) else 0
        f1_c = 2 * p_c * r_c / (p_c + r_c) if (p_c + r_c) else 0
        row[f"tp_{cat}"] = tp_c
        row[f"fp_{cat}"] = fp_c
        row[f"fn_{cat}"] = fn_c
        row[f"prec_{cat}"] = f"{p_c:.4f}"
        row[f"recall_{cat}"] = f"{r_c:.4f}"
        row[f"f1_{cat}"] = f"{f1_c:.4f}"

    master_rows.append(row)

# ── Write CSV ─────────────────────────────────────────────────────────────────
csv_path = os.path.join(OUT_DIR, "identification_results.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(master_rows[0].keys()))
    w.writeheader()
    for row in master_rows:
        w.writerow(row)

print(f"\n\n{'='*70}")
print(f"Results saved to: {csv_path}")
print(f"{'='*70}")

# ── Final summary table ──────────────────────────────────────────────────────
print(f"\n{'='*90}")
print(f"  SUMMARY TABLE — All Experiments")
print(f"{'='*90}")
print(f"  {'Experiment':<24} {'Prec':>7} {'Recall':>7} {'F1':>7} {'TP':>5} {'FP':>5} {'FN':>5}")
print(f"  {'-'*66}")
# Sort by F1 descending
sorted_rows = sorted(master_rows, key=lambda r: float(r["f1"]), reverse=True)
for row in sorted_rows:
    print(f"  {row['experiment']:<24} {float(row['precision']):>6.1%}  {float(row['recall']):>6.1%}  {float(row['f1']):>6.1%} {row['TP']:>5} {row['FP']:>5} {row['FN']:>5}")
