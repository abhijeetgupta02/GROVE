#!/usr/bin/env python3
"""Grounding evaluation against new COCO GT for all experiments."""

import json, os, re, csv
from collections import defaultdict
import openpyxl

# ── Paths / system manifest (CLI-driven, package-relative defaults) ──────────
import argparse
from eval_config import GT_JSON_DEFAULT, RESULTS_DIR, discover_systems

THRESHOLDS = [0.1, 0.3]

_parser = argparse.ArgumentParser(
    description="Spatial grounding evaluation (IoG / IoP / IoU coverage)."
)
_parser.add_argument("--gt", default=str(GT_JSON_DEFAULT),
                     help="Path to the COCO ground-truth JSON.")
_parser.add_argument("--predictions-dir", default=None,
                     help="Directory of prediction workbooks "
                          "(defaults to the bundled predictions/ directory).")
_parser.add_argument("--out-dir", default=str(RESULTS_DIR / "grounding"),
                     help="Directory for the master_grounding_summary.csv output.")
_args = _parser.parse_args()

GT_JSON = _args.gt
OUT_DIR = _args.out_dir
EXPERIMENTS = discover_systems(_args.predictions_dir)
os.makedirs(OUT_DIR, exist_ok=True)

CAT_MAP = {
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

# ── Helpers ───────────────────────────────────────────────────────────────────
def normalize(name):
    """Normalize image name: strip Roboflow hash, fix underscore extension."""
    s = os.path.basename(str(name).strip())
    # Remove Roboflow .rf.<hash>.<ext> suffix
    s = re.sub(r"\.rf\.[a-zA-Z0-9]{6,}\.[a-zA-Z0-9]+$", "", s)
    # Fix underscore before extension (e.g. 3_jpeg -> 3.jpeg)
    s = re.sub(r"_(png|jpg|jpeg|webp)$", r".\1", s, flags=re.IGNORECASE)
    base, ext = os.path.splitext(s)
    return base + ext.lower() if ext else s

def coco_to_xyxy(bbox):
    x, y, w, h = [float(v) for v in bbox]
    return [x, y, x + w, y + h]

def intersection_area(a, b):
    ix1 = max(a[0], b[0]); iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2]); iy2 = min(a[3], b[3])
    return max(0, ix2 - ix1) * max(0, iy2 - iy1)

def box_area(b):
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])

def iog(gt_box, pred_box):
    """Intersection over GT area."""
    return intersection_area(gt_box, pred_box) / (box_area(gt_box) + 1e-9)

def iop(gt_box, pred_box):
    """Intersection over Pred area."""
    return intersection_area(gt_box, pred_box) / (box_area(pred_box) + 1e-9)

def iou_fn(gt_box, pred_box):
    """Standard IoU."""
    i = intersection_area(gt_box, pred_box)
    u = box_area(gt_box) + box_area(pred_box) - i
    return i / (u + 1e-9)

# ── Load GT ──────────────────────────────────────────────────────────────────
with open(GT_JSON, encoding="utf-8") as f:
    coco = json.load(f)

cat_id_to_canonical = {c["id"]: CAT_MAP.get(c["name"], "Other") for c in coco["categories"]}
img_id_to_name = {img["id"]: normalize(img["file_name"]) for img in coco["images"]}

gt_by_img = defaultdict(list)   # norm_name → list of (xyxy, canonical_cat)
for ann in coco["annotations"]:
    name = img_id_to_name[ann["image_id"]]
    box = coco_to_xyxy(ann["bbox"])
    cat = cat_id_to_canonical[ann["category_id"]]
    gt_by_img[name].append((box, cat))

print(f"GT loaded: {len(coco['images'])} images, {len(coco['annotations'])} annotations")
print(f"GT categories: {dict(cat_id_to_canonical)}")
print(f"Unique GT image names: {len(gt_by_img)}")

# Also check what the GT extra.name field normalizes to
gt_extra_names = set()
for img in coco["images"]:
    if "extra" in img and "name" in img["extra"]:
        gt_extra_names.add(normalize(img["extra"]["name"]))
    gt_extra_names.add(normalize(img["file_name"]))
print(f"GT names (from file_name normalize): sample = {sorted(list(gt_by_img.keys()))[:10]}")

# ── Load predictions from XLSX ────────────────────────────────────────────────
def load_predictions_from_xlsx(xlsx_path):
    """Load predictions from an xlsx file. Returns pred_by_img dict and stats."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["Full_Results"]
    
    rows = list(ws.iter_rows(values_only=True))
    header = list(rows[0])
    
    # Find column indices
    name_col = header.index("image_name")
    hazards_col = header.index("hazards_json")
    
    pred_by_img = defaultdict(list)   # norm_name → list of xyxy boxes
    n_total_hazard_rows = 0
    n_no_box_rows = 0
    n_images = 0
    
    for row in rows[1:]:
        if row[name_col] is None:
            continue
        n_images += 1
        norm = normalize(str(row[name_col]))
        hazards_raw = row[hazards_col]
        
        if hazards_raw is None or str(hazards_raw).strip() in ("", "[]"):
            continue
        
        try:
            hazards = json.loads(str(hazards_raw))
        except json.JSONDecodeError:
            continue
            
        for h in hazards:
            # Skip NO_HAZARD / COMPLIANT entries
            if h.get("hazard", "").upper() in ("NO_HAZARD", "COMPLIANT"):
                continue
            if h.get("category", "").upper() in ("COMPLIANT",):
                continue
            
            n_total_hazard_rows += 1
            bb = h.get("bbox_xyxy")
            if bb and isinstance(bb, list) and len(bb) == 4 and all(v is not None for v in bb):
                try:
                    box = [float(v) for v in bb]
                    # Sanity: box must have positive area
                    if box[2] > box[0] and box[3] > box[1]:
                        pred_by_img[norm].append(box)
                    else:
                        n_no_box_rows += 1
                except (ValueError, TypeError):
                    n_no_box_rows += 1
            else:
                n_no_box_rows += 1
    
    wb.close()
    return pred_by_img, n_total_hazard_rows, n_no_box_rows, n_images

# ── Compute metrics ───────────────────────────────────────────────────────────
os.makedirs(OUT_DIR, exist_ok=True)

# Master summary across all experiments
all_results = []

for exp_name, xlsx_path in EXPERIMENTS:
    print(f"\n{'#'*70}")
    print(f"  Evaluating: {exp_name}")
    print(f"  File: {os.path.basename(xlsx_path)}")
    print(f"{'#'*70}")
    
    pred_by_img, n_total_hazard_rows, n_no_box_rows, n_images = load_predictions_from_xlsx(xlsx_path)
    
    print(f"  Predictions loaded: {n_images} images, {sum(len(v) for v in pred_by_img.values())} boxes")
    print(f"  Total hazard rows: {n_total_hazard_rows}, no-box rows: {n_no_box_rows}")
    
    # Debug: check image name matching
    shared_names = set(gt_by_img.keys()) & set(pred_by_img.keys())
    gt_only = set(gt_by_img.keys()) - set(pred_by_img.keys())
    pred_only = set(pred_by_img.keys()) - set(gt_by_img.keys())
    
    print(f"  Shared images: {len(shared_names)}")
    print(f"  GT-only images (no preds): {len(gt_only)}")
    print(f"  Pred-only images (no GT): {len(pred_only)}")
    
    if len(shared_names) < 10:
        print(f"  WARNING: Very few shared images!")
        print(f"    Sample GT names: {sorted(list(gt_by_img.keys()))[:5]}")
        print(f"    Sample Pred names: {sorted(list(pred_by_img.keys()))[:5]}")
    
    for theta in THRESHOLDS:
        total_gt = 0; gt_covered = 0
        total_pred = 0; pred_covering = 0
        iop_vals = []; iou_vals = []
        cat_gt = defaultdict(int); cat_covered = defaultdict(int)

        # Images with GT but no preds: GT boxes are all misses
        for img in gt_only:
            for (box, cat) in gt_by_img[img]:
                total_gt += 1
                cat_gt[cat] += 1

        for img in shared_names:
            gt_boxes = gt_by_img[img]
            pred_boxes = pred_by_img[img]
            total_gt += len(gt_boxes)
            total_pred += len(pred_boxes)
            
            for (gb, cat) in gt_boxes:
                cat_gt[cat] += 1

            # GT Coverage Recall: each GT box covered by any pred with IoG >= theta
            for (gb, cat) in gt_boxes:
                scores = [iog(gb, pb) for pb in pred_boxes]
                if scores and max(scores) >= theta:
                    gt_covered += 1
                    cat_covered[cat] += 1

            # Pred Covering Rate + Mean Tightness + IoU
            for pb in pred_boxes:
                scores_iog = [iog(gb, pb) for (gb, _) in gt_boxes]
                scores_iou = [iou_fn(gb, pb) for (gb, _) in gt_boxes]
                if scores_iog and max(scores_iog) >= theta:
                    pred_covering += 1
                    best_gt_idx = scores_iog.index(max(scores_iog))
                    iop_vals.append(iop(gt_boxes[best_gt_idx][0], pb))
                    iou_vals.append(max(scores_iou))

        gt_cov_recall = gt_covered / total_gt if total_gt else 0
        pred_cov_rate = pred_covering / total_pred if total_pred else 0
        mean_tight = sum(iop_vals) / len(iop_vals) if iop_vals else 0
        mean_iou = sum(iou_vals) / len(iou_vals) if iou_vals else 0
        no_box_rate = n_no_box_rows / n_total_hazard_rows if n_total_hazard_rows else 0

        print(f"\n  {'='*55}")
        print(f"    θ = {theta}")
        print(f"  {'='*55}")
        print(f"    Total GT boxes       : {total_gt}  (across {len(gt_by_img)} GT images)")
        print(f"    Total pred boxes     : {total_pred}")
        print(f"    Shared images        : {len(shared_names)}")
        print(f"    GT-only images (FN)  : {len(gt_only)}")
        print(f"    GT Coverage Recall   : {gt_covered}/{total_gt} = {gt_cov_recall:.1%}")
        print(f"    Pred Covering Rate   : {pred_covering}/{total_pred} = {pred_cov_rate:.1%}")
        print(f"    Mean Tightness (IoP) : {mean_tight:.1%}")
        print(f"    Mean IoU (covering)  : {mean_iou:.1%}")
        print(f"    No-box hazard rows   : {n_no_box_rows}/{n_total_hazard_rows} = {no_box_rate:.1%}")
        print(f"\n    Per-category GT Coverage Recall (θ={theta}):")
        for cat in sorted(cat_gt.keys()):
            n = cat_gt[cat]; c = cat_covered.get(cat, 0)
            print(f"      {cat:<30}: {c}/{n} = {c/n:.1%}" if n else f"      {cat}: 0 GT boxes")

        # Write per-experiment CSV
        exp_out = os.path.join(OUT_DIR, exp_name)
        os.makedirs(exp_out, exist_ok=True)
        
        with open(os.path.join(exp_out, f"grounding_summary_theta{theta}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["metric", "value"])
            w.writerow(["experiment", exp_name])
            w.writerow(["theta", theta])
            w.writerow(["total_gt_boxes", total_gt])
            w.writerow(["gt_boxes_covered", gt_covered])
            w.writerow(["gt_coverage_recall", f"{gt_cov_recall:.4f}"])
            w.writerow(["total_pred_boxes", total_pred])
            w.writerow(["pred_boxes_covering", pred_covering])
            w.writerow(["pred_covering_rate", f"{pred_cov_rate:.4f}"])
            w.writerow(["mean_tightness_iop", f"{mean_tight:.4f}"])
            w.writerow(["mean_iou_covering", f"{mean_iou:.4f}"])
            w.writerow(["no_box_hazard_rows", n_no_box_rows])
            w.writerow(["total_hazard_rows", n_total_hazard_rows])
            w.writerow(["no_box_rate", f"{no_box_rate:.4f}"])
            w.writerow(["shared_images", len(shared_names)])
            w.writerow(["gt_only_images", len(gt_only)])

        with open(os.path.join(exp_out, f"per_category_theta{theta}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["category", "gt_count", "covered", "gt_coverage_recall"])
            for cat in sorted(cat_gt.keys()):
                n = cat_gt[cat]; c = cat_covered.get(cat, 0)
                w.writerow([cat, n, c, f"{c/n:.4f}" if n else "0"])

        # Collect for master summary
        row = {
            "experiment": exp_name,
            "theta": theta,
            "total_gt_boxes": total_gt,
            "gt_boxes_covered": gt_covered,
            "gt_coverage_recall": f"{gt_cov_recall:.4f}",
            "total_pred_boxes": total_pred,
            "pred_boxes_covering": pred_covering,
            "pred_covering_rate": f"{pred_cov_rate:.4f}",
            "mean_tightness_iop": f"{mean_tight:.4f}",
            "mean_iou_covering": f"{mean_iou:.4f}",
            "no_box_hazard_rows": n_no_box_rows,
            "total_hazard_rows": n_total_hazard_rows,
            "no_box_rate": f"{no_box_rate:.4f}",
            "shared_images": len(shared_names),
            "gt_only_images": len(gt_only),
        }
        # Add per-category recall
        for cat in sorted(cat_gt.keys()):
            n = cat_gt[cat]; c = cat_covered.get(cat, 0)
            row[f"recall_{cat}"] = f"{c/n:.4f}" if n else "N/A"
        
        all_results.append(row)

# ── Write master summary CSV ─────────────────────────────────────────────────
# Collect all possible category columns
all_cat_cols = sorted(set(k for r in all_results for k in r.keys() if k.startswith("recall_")))

summary_path = os.path.join(OUT_DIR, "master_grounding_summary.csv")
with open(summary_path, "w", newline="") as f:
    base_cols = [
        "experiment", "theta",
        "gt_coverage_recall", "pred_covering_rate", "mean_tightness_iop", "mean_iou_covering",
        "no_box_rate", "no_box_hazard_rows", "total_hazard_rows",
        "total_gt_boxes", "gt_boxes_covered", "total_pred_boxes", "pred_boxes_covering",
        "shared_images", "gt_only_images",
    ]
    all_cols = base_cols + all_cat_cols
    w = csv.DictWriter(f, fieldnames=all_cols, extrasaction="ignore")
    w.writeheader()
    for row in all_results:
        w.writerow(row)

print(f"\n{'='*70}")
print(f"Master summary written to: {summary_path}")
print(f"Per-experiment CSVs written to: {OUT_DIR}/<experiment>/")
print(f"{'='*70}")
