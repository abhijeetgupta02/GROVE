#!/usr/bin/env python3
"""
Category-aware evaluation using IoP (Intersection over Pred) as the match criterion.

Question answered: "How many predicted boxes are validated (covered) by a GT box?"
  IoP = intersection(GT, Pred) / area(Pred)
  If IoP >= theta, the GT box "covers" the pred box.

This is computed BOTH class-agnostic and class-aware (category must match).
"""

import json, os, re, csv
from collections import defaultdict, Counter
import openpyxl

# ── Paths / system manifest (CLI-driven, package-relative defaults) ──────────
import argparse
from eval_config import GT_JSON_DEFAULT, RESULTS_DIR, discover_systems

_parser = argparse.ArgumentParser(
    description="Category-aware GT-covers-prediction containment evaluation."
)
_parser.add_argument("--gt", default=str(GT_JSON_DEFAULT),
                     help="Path to the COCO ground-truth JSON.")
_parser.add_argument("--predictions-dir", default=None,
                     help="Directory of prediction workbooks "
                          "(defaults to the bundled predictions/ directory).")
_parser.add_argument("--out-dir", default=str(RESULTS_DIR / "grounding"),
                     help="Directory for the gt_covers_pred_comparison.csv output.")
_args = _parser.parse_args()

GT_JSON = _args.gt
OUT_DIR = _args.out_dir
EXPERIMENTS = discover_systems(_args.predictions_dir)
os.makedirs(OUT_DIR, exist_ok=True)

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

CANONICAL_CATS = ["Fall_Hazard", "PPE_Violation", "Housekeeping_Storage",
                  "Electrocution_Hazard", "CaughtInBetween_hazard",
                  "StruckBy_Hazard", "Other"]


def map_pred_category(raw_cat):
    if not raw_cat:
        return "UNMAPPED"
    s = raw_cat.lower().strip()

    direct = {
        "fall_hazard": "Fall_Hazard", "fall hazard": "Fall_Hazard",
        "ppe_violation": "PPE_Violation", "ppe violation": "PPE_Violation",
        "electrocution_hazard": "Electrocution_Hazard", "electrocution hazard": "Electrocution_Hazard",
        "electrical hazard": "Electrocution_Hazard",
        "housekeeping_storage": "Housekeeping_Storage", "housekeeping storage": "Housekeeping_Storage",
        "housekeeping": "Housekeeping_Storage",
        "caughtinbetween_hazard": "CaughtInBetween_hazard",
        "caught in between hazard": "CaughtInBetween_hazard",
        "struckby_hazard": "StruckBy_Hazard", "struck by hazard": "StruckBy_Hazard",
        "struck-by hazard": "StruckBy_Hazard",
        "other": "Other",
    }
    if s in direct:
        return direct[s]

    ppe_kw = ["ppe", "personal protective", "hard hat", "helmet", "safety glasses",
              "gloves", "high-visibility", "hi-vis", "reflective vest", "safety vest",
              "protective equipment", "safety gear", "goggles", "face shield",
              "ear protection", "hearing protection", "respirator", "safety boots",
              "steel toe", "safety harness worn", "missing ppe"]
    for kw in ppe_kw:
        if kw in s:
            return "PPE_Violation"

    fall_kw = ["fall from height", "fall hazard", "fall protection", "guardrail",
               "unprotected edge", "scaffold", "ladder", "elevated work", "roof",
               "working at height", "fall arrest", "safety net", "leading edge",
               "1926.501", "1926.502", "1926.451", "1926.1053"]
    for kw in fall_kw:
        if kw in s:
            return "Fall_Hazard"

    elec_kw = ["electr", "wiring", "exposed wire", "power line",
               "energized", "lockout", "tagout", "arc flash", "voltage"]
    for kw in elec_kw:
        if kw in s:
            return "Electrocution_Hazard"

    house_kw = ["housekeeping", "clutter", "debris", "obstruct", "blocked",
                "tripping", "slip", "trip", "walkway", "aisle", "storage",
                "stacking", "material storage", "disorganiz", "untidy",
                "messy", "clean", "poor housekeeping"]
    for kw in house_kw:
        if kw in s:
            return "Housekeeping_Storage"

    caught_kw = ["caught", "pinch", "crush", "machine guard", "rotating",
                 "moving part", "conveyor", "equipment guard", "nip point"]
    for kw in caught_kw:
        if kw in s:
            return "CaughtInBetween_hazard"

    struck_kw = ["struck", "falling object", "overhead", "dropped",
                 "flying object", "projectile"]
    for kw in struck_kw:
        if kw in s:
            return "StruckBy_Hazard"

    return "UNMAPPED"


# ── Geometry helpers ──────────────────────────────────────────────────────────
def normalize(name):
    s = os.path.basename(str(name).strip())
    s = re.sub(r"\.rf\.[a-zA-Z0-9]{6,}\.[a-zA-Z0-9]+$", "", s)
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

def iop(gt_box, pred_box):
    """IoP = intersection / pred_area. Measures how much of pred is covered by GT."""
    return intersection_area(gt_box, pred_box) / (box_area(pred_box) + 1e-9)

def iog(gt_box, pred_box):
    """IoG = intersection / gt_area. Measures how much of GT is covered by pred."""
    return intersection_area(gt_box, pred_box) / (box_area(gt_box) + 1e-9)

def iou_fn(a, b):
    i = intersection_area(a, b)
    u = box_area(a) + box_area(b) - i
    return i / (u + 1e-9)


# ── Load GT ──────────────────────────────────────────────────────────────────
with open(GT_JSON, encoding="utf-8") as f:
    coco = json.load(f)

cat_id_to_canonical = {c["id"]: CAT_MAP_GT.get(c["name"], "Other") for c in coco["categories"]}
img_id_to_name = {img["id"]: normalize(img["file_name"]) for img in coco["images"]}

gt_by_img = defaultdict(list)
for ann in coco["annotations"]:
    name = img_id_to_name[ann["image_id"]]
    box = coco_to_xyxy(ann["bbox"])
    cat = cat_id_to_canonical[ann["category_id"]]
    gt_by_img[name].append((box, cat))


# ── Load predictions WITH categories ─────────────────────────────────────────
def load_predictions_with_cats(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["Full_Results"]
    rows = list(ws.iter_rows(values_only=True))
    header = list(rows[0])
    name_col = header.index("image_name")
    hazards_col = header.index("hazards_json")

    pred_by_img = defaultdict(list)
    n_total = 0; n_no_box = 0

    for row in rows[1:]:
        if row[name_col] is None:
            continue
        norm = normalize(str(row[name_col]))
        hazards_raw = row[hazards_col]
        if hazards_raw is None or str(hazards_raw).strip() in ("", "[]"):
            continue
        try:
            hazards = json.loads(str(hazards_raw))
        except json.JSONDecodeError:
            continue
        for h in hazards:
            if h.get("hazard", "").upper() in ("NO_HAZARD", "COMPLIANT"):
                continue
            if h.get("category", "").upper() in ("COMPLIANT",):
                continue
            n_total += 1
            bb = h.get("bbox_xyxy")
            if bb and isinstance(bb, list) and len(bb) == 4 and all(v is not None for v in bb):
                try:
                    box = [float(v) for v in bb]
                    if box[2] > box[0] and box[3] > box[1]:
                        raw_cat = h.get("category", "") or h.get("hazard", "") or ""
                        mapped = map_pred_category(raw_cat)
                        pred_by_img[norm].append((box, mapped))
                    else:
                        n_no_box += 1
                except (ValueError, TypeError):
                    n_no_box += 1
            else:
                n_no_box += 1
    wb.close()
    return pred_by_img, n_total, n_no_box


# ── MAIN EVALUATION ──────────────────────────────────────────────────────────
os.makedirs(OUT_DIR, exist_ok=True)
theta = 0.3

master_rows = []

print("=" * 90)
print("  EVALUATION: GT Covering Pred (IoP = intersection / pred_area)")
print("  Match criterion: IoP >= 0.3 means 'GT covers this pred box'")
print("=" * 90)

for exp_name, xlsx_path in EXPERIMENTS:
    pred_by_img, n_total_hazards, n_no_box = load_predictions_with_cats(xlsx_path)

    shared = set(gt_by_img.keys()) & set(pred_by_img.keys())
    gt_only = set(gt_by_img.keys()) - set(pred_by_img.keys())

    # ── Counters ──
    total_gt = 0; total_pred = 0

    # Agnostic (IoP-based)
    ag_pred_covered = 0        # pred boxes where max IoP >= theta (any GT covers them)
    ag_iop_vals = []           # IoP values for covered preds
    ag_iou_vals = []

    # Category-aware (IoP-based, same category only)
    ca_pred_covered = 0
    ca_iop_vals = []
    ca_iou_vals = []

    # Per pred-category tracking
    cat_pred_n = defaultdict(int)
    cat_ag_pred_cov = defaultdict(int)
    cat_ca_pred_cov = defaultdict(int)

    # Also track GT side: which GT boxes have at least one pred covered by them
    ag_gt_has_match = defaultdict(set)  # img → set of GT indices that matched
    ca_gt_has_match = defaultdict(set)

    # Count GT boxes on gt_only images
    for img in gt_only:
        for (box, cat) in gt_by_img[img]:
            total_gt += 1

    for img in shared:
        gt_boxes = gt_by_img[img]
        pred_boxes = pred_by_img[img]

        total_gt += len(gt_boxes)
        total_pred += len(pred_boxes)

        for (pb, pcat) in pred_boxes:
            cat_pred_n[pcat] += 1

        # ── For each PRED box, check which GT boxes cover it (IoP) ──
        for pi, (pb, pcat) in enumerate(pred_boxes):

            # --- AGNOSTIC ---
            # Compute IoP of each GT box against this pred box
            all_iops = []
            for gi, (gb, gcat) in enumerate(gt_boxes):
                val = iop(gb, pb)
                all_iops.append((val, gi, gcat, gb))

            best_iop_ag = max(v for v, _, _, _ in all_iops) if all_iops else 0

            if best_iop_ag >= theta:
                ag_pred_covered += 1
                cat_ag_pred_cov[pcat] += 1
                # Record the IoP and IoU of the best match
                best_entry = max(all_iops, key=lambda x: x[0])
                ag_iop_vals.append(best_entry[0])
                ag_iou_vals.append(iou_fn(best_entry[3], pb))
                ag_gt_has_match[img].add(best_entry[1])

            # --- CATEGORY-AWARE ---
            same_cat_iops = []
            for gi, (gb, gcat) in enumerate(gt_boxes):
                if gcat == pcat:
                    val = iop(gb, pb)
                    same_cat_iops.append((val, gi, gb))

            best_iop_ca = max(v for v, _, _ in same_cat_iops) if same_cat_iops else 0

            if best_iop_ca >= theta:
                ca_pred_covered += 1
                cat_ca_pred_cov[pcat] += 1
                best_entry = max(same_cat_iops, key=lambda x: x[0])
                ca_iop_vals.append(best_entry[0])
                ca_iou_vals.append(iou_fn(best_entry[2], pb))
                ca_gt_has_match[img].add(best_entry[1])

    # Count how many GT boxes contributed at least one match
    ag_gt_matched = sum(len(v) for v in ag_gt_has_match.values())
    ca_gt_matched = sum(len(v) for v in ca_gt_has_match.values())

    # ── Compute rates ──
    def safe_div(a, b): return a / b if b else 0
    def safe_mean(lst): return sum(lst) / len(lst) if lst else 0

    ag_rate = safe_div(ag_pred_covered, total_pred)
    ca_rate = safe_div(ca_pred_covered, total_pred)
    ag_miop = safe_mean(ag_iop_vals)
    ca_miop = safe_mean(ca_iop_vals)
    ag_miou = safe_mean(ag_iou_vals)
    ca_miou = safe_mean(ca_iou_vals)

    # ── Print ──
    print(f"\n{'='*80}")
    print(f"  {exp_name}")
    print(f"{'='*80}")
    print(f"  Total GT boxes: {total_gt}  |  Total pred boxes: {total_pred}")
    print(f"  Shared images: {len(shared)}  |  GT-only: {len(gt_only)}")
    print()

    print(f"  PRED VALIDATION RATE (IoP >= {theta}): 'How many preds are validated by GT?'")
    print(f"  {'Metric':<35} {'Agnostic':>15} {'Cat-Aware':>15} {'Gap':>8}")
    print(f"  {'-'*73}")
    print(f"  {'Preds covered by GT':<35} {ag_pred_covered:>5}/{total_pred} ({ag_rate:>.1%}){ca_pred_covered:>6}/{total_pred} ({ca_rate:>.1%}){ag_pred_covered - ca_pred_covered:>+7}")
    print(f"  {'Mean IoP (of covered preds)':<35} {ag_miop:>14.1%}  {ca_miop:>14.1%}")
    print(f"  {'Mean IoU (of covered preds)':<35} {ag_miou:>14.1%}  {ca_miou:>14.1%}")
    print(f"  {'GT boxes that matched >= 1 pred':<35} {ag_gt_matched:>15} {ca_gt_matched:>15}")

    print(f"\n  --- Per Pred Category: How many preds of each type are validated by GT? ---")
    print(f"  {'Pred Category':<28} {'Preds':>5} {'Ag Cov':>8} {'Ag%':>7} {'CA Cov':>8} {'CA%':>7} {'Gap':>5}")
    for cat in CANONICAL_CATS + ["UNMAPPED"]:
        n = cat_pred_n.get(cat, 0)
        if n == 0:
            continue
        ag = cat_ag_pred_cov.get(cat, 0)
        ca = cat_ca_pred_cov.get(cat, 0)
        print(f"  {cat:<28} {n:>5} {ag:>8} {ag/n:>6.0%}  {ca:>8} {ca/n:>6.0%}  {ag-ca:>+5}")

    # Worked example: show one image in detail
    if exp_name == "exp01_modular_qwen":
        example_img = "108.jpg"
        if example_img in shared:
            print(f"\n  --- WORKED EXAMPLE: {example_img} ---")
            gt_boxes = gt_by_img[example_img]
            pred_boxes = pred_by_img[example_img]
            print(f"  GT boxes ({len(gt_boxes)}):")
            for i, (gb, gc) in enumerate(gt_boxes):
                print(f"    GT[{i}] {gc:<25} box={[round(v,1) for v in gb]}")
            print(f"  Pred boxes ({len(pred_boxes)}):")
            for i, (pb, pc) in enumerate(pred_boxes):
                print(f"    P[{i}] {pc:<25} box={[round(v,1) for v in pb]}")
            print(f"\n  IoP matrix (rows=preds, cols=GT): IoP = intersection / pred_area")
            print(f"  {'':>30}", end="")
            for i in range(len(gt_boxes)):
                print(f"  GT[{i}] {gt_boxes[i][1][:12]:>12}", end="")
            print(f"  {'Best IoP':>10}  {'Best GT cat':>20}  {'Pred cat':>20}  {'Match?':>7}")
            for pi, (pb, pc) in enumerate(pred_boxes):
                print(f"  P[{pi}] {pc[:27]:<28}", end="")
                best_v = 0; best_gi = 0
                for gi, (gb, gc) in enumerate(gt_boxes):
                    v = iop(gb, pb)
                    print(f"  {v:>17.4f}", end="")
                    if v > best_v:
                        best_v = v; best_gi = gi
                best_gc = gt_boxes[best_gi][1]
                match = "YES" if pc == best_gc else "NO"
                verdict_ag = "covered" if best_v >= theta else "NOT covered"
                print(f"  {best_v:>10.4f}  {best_gc:>20}  {pc:>20}  {match:>7}  ({verdict_ag})")

    master_rows.append({
        "experiment": exp_name,
        "total_gt": total_gt,
        "total_pred": total_pred,
        "ag_pred_covered": ag_pred_covered,
        "ag_pred_rate": f"{ag_rate:.4f}",
        "ca_pred_covered": ca_pred_covered,
        "ca_pred_rate": f"{ca_rate:.4f}",
        "pred_gap": ag_pred_covered - ca_pred_covered,
        "ag_mean_iop": f"{ag_miop:.4f}",
        "ca_mean_iop": f"{ca_miop:.4f}",
        "ag_mean_iou": f"{ag_miou:.4f}",
        "ca_mean_iou": f"{ca_miou:.4f}",
        "ag_gt_matched": ag_gt_matched,
        "ca_gt_matched": ca_gt_matched,
    })

# ── Write master CSV ─────────────────────────────────────────────────────────
master_path = os.path.join(OUT_DIR, "gt_covers_pred_comparison.csv")
with open(master_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(master_rows[0].keys()))
    w.writeheader()
    for row in master_rows:
        w.writerow(row)

print(f"\n\n{'='*80}")
print(f"Master CSV: {master_path}")
print(f"{'='*80}")
