"""Dataset adapters for appendix experiments.

The main paper code uses the local ``All_Images`` folder.  This module adds a
small Ultralytics YOLO-format adapter for the Construction-PPE appendix dataset
without changing the existing prompt or result schema.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from PIL import Image


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".avif"}

CONSTRUCTION_PPE_CLASS_NAMES = {
    0: "helmet",
    1: "gloves",
    2: "vest",
    3: "boots",
    4: "goggles",
    5: "none",
    6: "Person",
    7: "no_helmet",
    8: "no_goggle",
    9: "no_gloves",
    10: "no_boots",
}

# Closest paper category for labels that are actual safety violations.  Worn
# PPE and person boxes are object/PPE labels, not hazards, so they are kept in
# the manifest but excluded from hazard-identification ground truth.
CONSTRUCTION_PPE_TO_PAPER_CATEGORY = {
    5: "PPE_Violation",
    7: "PPE_Violation",
    8: "PPE_Violation",
    9: "PPE_Violation",
    10: "PPE_Violation",
}

CONSTRUCTION_PPE_OBJECT_ONLY_CLASS_IDS = {0, 1, 2, 3, 4, 6}


def list_image_files(image_dir: Path) -> list[Path]:
    """Return sorted image files directly under ``image_dir``."""

    if not image_dir.is_dir():
        return []
    return sorted(
        [child for child in image_dir.iterdir() if child.is_file() and child.suffix.lower() in IMAGE_EXTS],
        key=lambda path: path.name.lower(),
    )


def construction_ppe_split_dirs(dataset_root: Path, split: str) -> tuple[Path, Path]:
    """Return image and label directories for an Ultralytics YOLO split."""

    root = Path(dataset_root)
    image_dir = root / "images" / split
    label_dir = root / "labels" / split
    return image_dir, label_dir


def list_construction_ppe_images(dataset_root: Path, split: str = "test") -> list[Path]:
    """Return image paths for a Construction-PPE split."""

    image_dir, _ = construction_ppe_split_dirs(dataset_root, split)
    images = list_image_files(image_dir)
    if not images:
        raise FileNotFoundError(
            f"No images found for Construction-PPE split '{split}' in {image_dir}. "
            "Expected the Ultralytics layout: images/{split} and labels/{split}."
        )
    return images


def select_by_ordinal(
    image_paths: list[Path],
    start: int = 1,
    end: int = 9999,
    max_images: int | None = None,
) -> list[Path]:
    """Select images by 1-based sorted order for datasets with nonnumeric names."""

    selected = [path for idx, path in enumerate(image_paths, start=1) if start <= idx <= end]
    if max_images is not None:
        selected = selected[:max_images]
    return selected


def label_path_for_image(image_path: Path, dataset_root: Path, split: str) -> Path:
    """Return the YOLO label path matching an image path."""

    image_dir, label_dir = construction_ppe_split_dirs(dataset_root, split)
    try:
        rel = image_path.relative_to(image_dir)
    except ValueError:
        rel = Path(image_path.name)
    return label_dir / rel.with_suffix(".txt")


def yolo_xywhn_to_xyxy(box: list[float], width: int, height: int) -> list[float]:
    """Convert YOLO normalized xywh to pixel xyxy."""

    x_center, y_center, box_width, box_height = box
    x1 = (x_center - box_width / 2.0) * width
    y1 = (y_center - box_height / 2.0) * height
    x2 = (x_center + box_width / 2.0) * width
    y2 = (y_center + box_height / 2.0) * height
    return [
        max(0.0, min(float(width), x1)),
        max(0.0, min(float(height), y1)),
        max(0.0, min(float(width), x2)),
        max(0.0, min(float(height), y2)),
    ]


def parse_construction_ppe_label_file(
    image_path: Path,
    dataset_root: Path,
    split: str,
) -> list[dict[str, Any]]:
    """Parse one YOLO label file into paper-category-aware rows."""

    label_path = label_path_for_image(image_path, dataset_root, split)
    if not label_path.exists():
        return []

    with Image.open(image_path) as img:
        width, height = img.size

    rows: list[dict[str, Any]] = []
    with label_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            try:
                class_id = int(float(parts[0]))
                yolo_box = [float(value) for value in parts[1:5]]
            except ValueError:
                continue

            class_name = CONSTRUCTION_PPE_CLASS_NAMES.get(class_id, str(class_id))
            mapped_category = CONSTRUCTION_PPE_TO_PAPER_CATEGORY.get(class_id)
            if mapped_category:
                eval_scope = "hazard_identification_and_grounding"
            elif class_id in CONSTRUCTION_PPE_OBJECT_ONLY_CLASS_IDS:
                eval_scope = "object_or_worn_ppe_not_hazard"
            else:
                eval_scope = "unmapped_not_evaluated"

            rows.append(
                {
                    "image_name": image_path.name,
                    "image_path": str(image_path),
                    "relative_image_path": os.path.relpath(image_path, dataset_root).replace(os.sep, "/"),
                    "label_path": str(label_path),
                    "line_number": line_number,
                    "image_width_px": width,
                    "image_height_px": height,
                    "raw_class_id": class_id,
                    "raw_class_name": class_name,
                    "canonical_category": mapped_category or "",
                    "eval_scope": eval_scope,
                    "bbox_xyxy": yolo_xywhn_to_xyxy(yolo_box, width, height),
                    "bbox_yolo_xywhn": yolo_box,
                }
            )
    return rows


def load_construction_ppe_ground_truth(
    dataset_root: Path,
    split: str = "test",
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Load image rows, hazard GT boxes, and all raw label rows for a split."""

    image_paths = list_construction_ppe_images(dataset_root, split)
    image_rows = [
        {
            "image_name": path.name,
            "image_path": str(path),
            "relative_image_path": os.path.relpath(path, dataset_root).replace(os.sep, "/"),
        }
        for path in image_paths
    ]
    gt_boxes = {path.name: [] for path in image_paths}
    all_label_rows: list[dict[str, Any]] = []

    for image_path in image_paths:
        for row in parse_construction_ppe_label_file(image_path, dataset_root, split):
            all_label_rows.append(row)
            if row["canonical_category"]:
                gt_boxes[image_path.name].append(
                    {
                        "bbox_xyxy": row["bbox_xyxy"],
                        "category": row["canonical_category"],
                        "raw_category": row["raw_class_name"],
                        "annotation_id": f"{image_path.name}:{row['line_number']}",
                    }
                )

    return image_rows, gt_boxes, all_label_rows
