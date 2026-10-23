"""
SiteCortex — Data Schema & Export
===================================
Handles JSONL writing, Excel export, and result validation.
"""
import os
import re
import json
import shutil
import pandas as pd
from datetime import datetime

from shared.hazard_taxonomy import (
    canonicalize_hazards,
    display_label,
    labels_from_hazards,
    load_gt_labels_from_coco,
    normalize_image_name,
)


def _image_id_from_name(filename):
    """Extract numeric ID from filename like '42.webp' -> '042'."""
    stem = os.path.splitext(filename)[0]
    match = re.match(r"(\d+)", stem)
    if match:
        return match.group(1).zfill(3)
    return stem


def new_result_record(image_path, experiment_id, model_tag, run_number=1):
    """Create a blank result record with all schema fields initialized."""
    filename = os.path.basename(image_path)

    return {
        "image_id": _image_id_from_name(filename),
        "image_name": filename,
        "image_path": image_path,
        "experiment_id": experiment_id,
        "model_tag": model_tag,
        "run_number": run_number,
        "timestamp": datetime.now().isoformat(),
        "caption_time_sec": None,
        "hazard_analysis_time_sec": None,
        "grounding_time_sec": None,
        "total_inference_time_sec": None,
        "gpu_mem_before_mb": None,
        "gpu_mem_after_mb": None,
        "gpu_mem_peak_mb": None,
        "caption_text": None,
        "caption_word_count": None,
        "raw_vlm_response": None,
        "is_safe_pred": None,
        "n_hazards_pred": 0,
        "hazards_json": "[]",
        "hazard_label": "",
        "canonical_hazard_label": "",
        "gt_hazard_label": "",
        "gt_canonical_hazard_label": "",
        "gt_has_hazard": None,
        "n_boxes_pred": 0,
        "grounding_coverage_pct": 0.0,
        "n_gdino_boxes": 0,
        "n_detr_fallback_boxes": 0,
        "n_vlm_native_boxes": 0,
        "path_a_grounded_phrases": "[]",
        "n_high_confidence": 0,
        "n_medium_confidence": 0,
        "has_valid_category": False,
        "has_valid_risk_level": False,
        "has_valid_mitigation": False,
        "structured_compliance_pct": 0.0,
        "image_width_px": None,
        "image_height_px": None,
        "image_format": None,
        "image_filesize_kb": None,
        "error": None,
        "retry_count": 0,
    }


def append_jsonl(filepath, record):
    """Append a single record to a JSONL file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_jsonl(filepath):
    """Load all records from a JSONL file."""
    records = []
    if not os.path.exists(filepath):
        return records
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def get_processed_ids(filepath):
    """Return set of (image_id, run_number) already in the JSONL."""
    processed = set()
    for rec in load_jsonl(filepath):
        key = (rec.get("image_id", ""), rec.get("run_number", 1))
        processed.add(key)
    return processed


def _augment_records_for_labels(records, gt_json_path=None):
    """Add predicted/GT category label columns before Excel export."""
    gt_labels = {}
    if gt_json_path and os.path.exists(gt_json_path):
        gt_labels = load_gt_labels_from_coco(gt_json_path)

    augmented = []
    for rec in records:
        row = dict(rec)
        try:
            hazards = json.loads(row.get("hazards_json") or "[]")
        except json.JSONDecodeError:
            hazards = []
        hazards = canonicalize_hazards(hazards)

        row["hazards_json"] = json.dumps(hazards, ensure_ascii=False)
        row["canonical_hazard_label"] = labels_from_hazards(hazards, display=False)
        row["hazard_label"] = labels_from_hazards(hazards, display=True)

        if gt_labels:
            gt_set = sorted(gt_labels.get(normalize_image_name(row.get("image_name", "")), set()))
            row["gt_canonical_hazard_label"] = " | ".join(gt_set)
            row["gt_hazard_label"] = " | ".join(display_label(c) for c in gt_set)
            row["gt_has_hazard"] = bool(gt_set)

        augmented.append(row)
    return augmented


def export_category_review_folders(jsonl_path, output_dir, gt_json_path=None):
    """
    Create review folders directly from a result JSONL.

    Each image is copied into predicted/<category>/ using the annotated image
    when available, otherwise the raw image. If GT labels are available, a
    parallel ground_truth/<category>/ tree is also created.
    """
    records = _augment_records_for_labels(load_jsonl(jsonl_path), gt_json_path=gt_json_path)
    if not records:
        return

    os.makedirs(output_dir, exist_ok=True)

    def copy_for_labels(src_path, labels, root, image_name):
        labels = labels or "NO_HAZARD"
        for label in [x.strip() for x in str(labels).split("|") if x.strip()] or ["NO_HAZARD"]:
            safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("_") or "NO_HAZARD"
            dest_dir = os.path.join(root, safe_label)
            os.makedirs(dest_dir, exist_ok=True)
            if src_path and os.path.exists(src_path):
                shutil.copy2(src_path, os.path.join(dest_dir, image_name))

    for rec in records:
        image_name = rec.get("image_name") or os.path.basename(rec.get("image_path", "image"))
        pred_src = rec.get("annotated_image_path") or rec.get("image_path")
        copy_for_labels(pred_src, rec.get("hazard_label"), os.path.join(output_dir, "predicted"), image_name)
        if gt_json_path:
            copy_for_labels(rec.get("image_path"), rec.get("gt_hazard_label"), os.path.join(output_dir, "ground_truth"), image_name)

    print(f"Category review folders exported: {output_dir}")


def export_to_excel(jsonl_path, excel_path, summary_columns=None, gt_json_path=None,
                    category_review_dir=None):
    """Convert JSONL results to a formatted Excel file."""
    records = _augment_records_for_labels(load_jsonl(jsonl_path), gt_json_path=gt_json_path)
    if not records:
        print("No records to export.")
        return

    df = pd.DataFrame(records)

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Full_Results", index=False)

        if summary_columns:
            cols = [c for c in summary_columns if c in df.columns]
            if cols:
                df[cols].to_excel(writer, sheet_name="Summary", index=False)

        if "n_hazards_pred" in df.columns:
            stats = {
                "Total Images": len(df),
                "Unique Images": df["image_id"].nunique() if "image_id" in df.columns else len(df),
                "Images with Hazards": int((df["n_hazards_pred"] > 0).sum()),
                "Images Compliant": int((df["n_hazards_pred"] == 0).sum()),
                "Total Hazards Found": int(df["n_hazards_pred"].sum()),
                "Avg Hazards per Image": round(float(df["n_hazards_pred"].mean()), 2),
                "Total Boxes Drawn": int(df["n_boxes_pred"].sum()),
                "Avg Grounding Coverage %": round(float(df["grounding_coverage_pct"].mean()), 1),
                "Errors": int(df["error"].notna().sum()),
            }
            if "total_inference_time_sec" in df.columns and df["total_inference_time_sec"].notna().any():
                stats["Avg Inference Time (s)"] = round(float(df["total_inference_time_sec"].mean()), 2)
            stats_df = pd.DataFrame(list(stats.items()), columns=["Metric", "Value"])
            stats_df.to_excel(writer, sheet_name="Aggregate_Stats", index=False)

    print(f"Excel exported: {excel_path} ({len(records)} records)")

    if category_review_dir:
        export_category_review_folders(jsonl_path, category_review_dir, gt_json_path=gt_json_path)
