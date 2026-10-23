"""
Canonical seven-category hazard taxonomy and helpers.

These mappings mirror the paper evaluation scripts in
`EAAI Eval Scripts/`, but are kept in shared code so inference,
Excel export, folder generation, and evaluation use the same labels.
"""
import json
import os
import re
from collections import defaultdict


CANONICAL_CATEGORIES = [
    "Fall_Hazard",
    "StruckBy_Hazard",
    "Electrocution_Hazard",
    "CaughtInBetween_hazard",
    "PPE_Violation",
    "Housekeeping_Storage",
    "Other",
]

DISPLAY_LABELS = {
    "Fall_Hazard": "Fall Hazard",
    "StruckBy_Hazard": "Struck-By Hazard",
    "Electrocution_Hazard": "Electrocution Hazard",
    "CaughtInBetween_hazard": "Caught-In/Between Hazard",
    "PPE_Violation": "PPE Violation",
    "Housekeeping_Storage": "Housekeeping/Storage",
    "Other": "Other",
}

DISPLAY_TO_CANONICAL = {
    v.lower(): k for k, v in DISPLAY_LABELS.items()
}

GT_CATEGORY_MAP = {
    "Electrical Hazard": "Electrocution_Hazard",
    "Equipment and Machine Safety": "CaughtInBetween_hazard",
    "Fall from Height": "Fall_Hazard",
    "Falling Hazard": "Fall_Hazard",
    "Falling Object": "StruckBy_Hazard",
    "Falling Object Hazard": "StruckBy_Hazard",
    "Housekeeping": "Housekeeping_Storage",
    "Slip and Trip": "Housekeeping_Storage",
    "Slip and Trip Hazard": "Housekeeping_Storage",
    "PPE Violation": "PPE_Violation",
    "PPE Deficiency": "PPE_Violation",
    "Signage and Communication": "Other",
    "Other": "Other",
    "Hazards": "Other",
}


def normalize_image_name(name):
    """Normalize raw and Roboflow image names to a common local filename."""
    s = os.path.basename(str(name).strip())
    s = re.sub(r"\.rf\.[a-zA-Z0-9]{6,}\.[a-zA-Z0-9]+$", "", s)
    s = re.sub(r"_(png|jpg|jpeg|webp)$", r".\1", s, flags=re.IGNORECASE)
    base, ext = os.path.splitext(s)
    return base + ext.lower() if ext else s


def display_label(canonical):
    return DISPLAY_LABELS.get(canonical, canonical or "")


def map_gt_category(raw_cat):
    return GT_CATEGORY_MAP.get(str(raw_cat).strip(), "Other")


def map_pred_category(raw_cat):
    """Map a free-text prediction category into the canonical taxonomy."""
    if not raw_cat:
        return "UNMAPPED"

    s = str(raw_cat).lower().strip()
    s = s.replace("&", "and")
    s = re.sub(r"[/_-]+", " ", s)
    s = re.sub(r"\s+", " ", s)

    direct = {
        "fall hazard": "Fall_Hazard",
        "fall from height": "Fall_Hazard",
        "fall protection": "Fall_Hazard",
        "ppe violation": "PPE_Violation",
        "ppe deficiency": "PPE_Violation",
        "personal protective equipment": "PPE_Violation",
        "electrocution hazard": "Electrocution_Hazard",
        "electrical hazard": "Electrocution_Hazard",
        "electrical safety": "Electrocution_Hazard",
        "housekeeping storage": "Housekeeping_Storage",
        "housekeeping": "Housekeeping_Storage",
        "material storage": "Housekeeping_Storage",
        "slip and trip hazard": "Housekeeping_Storage",
        "caughtinbetween hazard": "CaughtInBetween_hazard",
        "caught in between hazard": "CaughtInBetween_hazard",
        "caught in between": "CaughtInBetween_hazard",
        "equipment and machine safety": "CaughtInBetween_hazard",
        "equipment use": "CaughtInBetween_hazard",
        "machine guarding": "CaughtInBetween_hazard",
        "struckby hazard": "StruckBy_Hazard",
        "struck by hazard": "StruckBy_Hazard",
        "struck by": "StruckBy_Hazard",
        "falling object hazard": "StruckBy_Hazard",
        "falling object": "StruckBy_Hazard",
        "other": "Other",
        "signage and communication": "Other",
        "general safety": "Other",
        "general safety and health": "Other",
    }
    if s in direct:
        return direct[s]

    ppe_kw = [
        "ppe", "personal protective", "hard hat", "helmet", "safety glasses",
        "gloves", "high visibility", "hi vis", "reflective vest", "safety vest",
        "protective equipment", "safety gear", "goggles", "face shield",
        "ear protection", "hearing protection", "respirator", "safety boots",
        "steel toe", "missing ppe", "clothing",
    ]
    if any(kw in s for kw in ppe_kw):
        return "PPE_Violation"

    fall_kw = [
        "fall from height", "fall hazard", "fall protection", "guardrail",
        "unprotected edge", "scaffold", "ladder", "elevated work", "roof",
        "working at height", "fall arrest", "safety net", "leading edge",
        "floor opening",
    ]
    if any(kw in s for kw in fall_kw):
        return "Fall_Hazard"

    elec_kw = [
        "electr", "wiring", "exposed wire", "power line", "energized",
        "lockout", "tagout", "arc flash", "voltage",
    ]
    if any(kw in s for kw in elec_kw):
        return "Electrocution_Hazard"

    house_kw = [
        "housekeeping", "clutter", "debris", "obstruct", "blocked",
        "tripping", "slip", "trip", "walkway", "aisle", "storage",
        "stacking", "material storage", "disorganiz", "untidy",
        "messy", "poor housekeeping",
    ]
    if any(kw in s for kw in house_kw):
        return "Housekeeping_Storage"

    caught_kw = [
        "caught", "pinch", "crush", "machine guard", "rotating",
        "moving part", "conveyor", "equipment guard", "nip point",
        "equipment and machine",
    ]
    if any(kw in s for kw in caught_kw):
        return "CaughtInBetween_hazard"

    struck_kw = [
        "struck", "falling object", "overhead", "dropped", "flying object",
        "projectile",
    ]
    if any(kw in s for kw in struck_kw):
        return "StruckBy_Hazard"

    return "UNMAPPED"


def canonicalize_hazards(hazards):
    """Return hazards with a canonical_category field added."""
    out = []
    for hazard in hazards or []:
        h = dict(hazard)
        raw_cat = h.get("category") or h.get("hazard") or ""
        canonical = map_pred_category(raw_cat)
        h["canonical_category"] = canonical
        h["category_display"] = display_label(canonical) if canonical != "UNMAPPED" else "UNMAPPED"
        out.append(h)
    return out


def labels_from_hazards(hazards, display=True):
    """Return a pipe-separated unique label string for predicted hazards."""
    seen = []
    for hazard in hazards or []:
        if str(hazard.get("hazard", "")).upper() in {"NO_HAZARD", "COMPLIANT"}:
            continue
        canonical = hazard.get("canonical_category") or map_pred_category(
            hazard.get("category") or hazard.get("hazard") or ""
        )
        if canonical == "UNMAPPED":
            continue
        if canonical not in seen:
            seen.append(canonical)
    values = [display_label(c) if display else c for c in seen]
    return " | ".join(values)


def load_gt_labels_from_coco(coco_path):
    """Return normalized image name -> canonical category set from COCO GT."""
    with open(coco_path, "r", encoding="utf-8") as f:
        coco = json.load(f)

    cat_id_to_canonical = {
        c["id"]: map_gt_category(c.get("name", "Other"))
        for c in coco.get("categories", [])
    }
    img_id_to_name = {
        img["id"]: normalize_image_name(img.get("file_name", ""))
        for img in coco.get("images", [])
    }

    labels = defaultdict(set)
    for ann in coco.get("annotations", []):
        name = img_id_to_name.get(ann.get("image_id"))
        if not name:
            continue
        labels[name].add(cat_id_to_canonical.get(ann.get("category_id"), "Other"))

    for img in coco.get("images", []):
        labels.setdefault(normalize_image_name(img.get("file_name", "")), set())

    return labels
