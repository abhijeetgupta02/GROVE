#!/usr/bin/env python3
"""
Shared configuration for the GROVE evaluation scripts.

Centralises the paths and the system manifest used by every evaluation
script (``identification_eval.py``, ``grounding_eval.py``,
``cataware_gt_covers_pred.py``) so that the supplementary package is fully
self-contained and runs from relative paths with no machine-specific
configuration.

Layout assumed (relative to the repository root that contains this package):

    GROVE_supplementary/
    |-- data/
    |   |-- annotations.coco.json      <- ground truth (COCO, 247 boxes)
    |   `-- images/                    <- 203 evaluation images
    |-- predictions/
    |   |-- grove/                     <- GROVE pipeline predictions
    |   |-- single_pass/               <- 11 single-pass baseline predictions
    |   `-- modular_ablation/          <- modular-backbone ablation predictions
    `-- code/evaluation/               <- this directory

Every prediction workbook is an ``.xlsx`` file with a ``Full_Results`` sheet
whose columns include ``image_name`` and ``hazards_json``; the grounding
scripts additionally read the per-hazard ``bbox_xyxy`` field inside
``hazards_json``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ── Package-relative paths ───────────────────────────────────────────────────
# code/evaluation/eval_config.py -> package root is two levels up.
PACKAGE_ROOT = Path(__file__).resolve().parents[2]

# Reuse the single authoritative hazard taxonomy shipped with the inference
# code (code/inference/shared/hazard_taxonomy.py) so that evaluation and
# inference share one category-mapping source of truth. This is the same
# mapper used to produce the metrics reported in the paper.
sys.path.insert(0, str(PACKAGE_ROOT / "code" / "inference"))
from shared.hazard_taxonomy import (  # noqa: E402
    map_gt_category,
    map_pred_category,
    normalize_image_name,
)

DATA_DIR = PACKAGE_ROOT / "data"
PREDICTIONS_DIR = PACKAGE_ROOT / "predictions"
RESULTS_DIR = PACKAGE_ROOT / "results"

GT_JSON_DEFAULT = DATA_DIR / "annotations.coco.json"

# ── Ground-truth category name -> canonical 7-class taxonomy ─────────────────
# Shared by every evaluation script. The raw COCO category names come from the
# source annotation export; they are collapsed to the seven OSHA-aligned
# categories reported in the paper.
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

CANONICAL_CATS = sorted(set(CAT_MAP.values()))


def discover_systems(predictions_dir: Path | str | None = None) -> list[tuple[str, str]]:
    """Return an ordered ``[(experiment_name, xlsx_path), ...]`` manifest.

    The GROVE row is listed first, then the single-pass baselines, then the
    modular-backbone ablation runs. Experiment names are derived from the file
    stem so that output CSV rows map cleanly onto the paper's model labels
    (see ``MODEL_IDENTIFIERS.md``).
    """
    base = Path(predictions_dir) if predictions_dir else PREDICTIONS_DIR
    systems: list[tuple[str, str]] = []

    grove = base / "grove" / "grove_qwen35_9b_run1.xlsx"
    if grove.exists():
        systems.append(("GROVE", str(grove)))

    for group, prefix in (("single_pass", ""), ("modular_ablation", "modular_")):
        group_dir = base / group
        if not group_dir.is_dir():
            continue
        for xlsx in sorted(group_dir.glob("*_run1.xlsx")):
            name = prefix + xlsx.name[: -len("_run1.xlsx")]
            systems.append((name, str(xlsx)))

    return systems
