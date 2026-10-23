#!/usr/bin/env python3
"""Fallback ablation from the saved GROVE predictions (no new inference).

Scores the reported GROVE predictions twice: as reported, and with every box
supplied by the DETR + OpenCLIP fallback removed (GroundingDINO-only grounding).
Hazard records are unchanged, so identification F1 is unchanged; only the
localization metrics can move.

Usage (from code/evaluation):
    python fallback_ablation.py
"""
import json
import os
import re
from collections import defaultdict

import openpyxl

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GT = os.path.join(ROOT, "data", "annotations.coco.json")
XLSX = os.path.join(ROOT, "predictions", "grove", "grove_qwen35_9b_run1.xlsx")


def normalize(name):
    s = os.path.basename(str(name).strip())
    s = re.sub(r"\.rf\.[a-zA-Z0-9]{6,}\.[a-zA-Z0-9]+$", "", s)
    s = re.sub(r"_(png|jpg|jpeg|webp)$", r".\1", s, flags=re.IGNORECASE)
    base, ext = os.path.splitext(s)
    return base + ext.lower() if ext else s


def inter(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def area(b):
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def iog(g, p):
    return inter(g, p) / (area(g) + 1e-9)


def iou(g, p):
    i = inter(g, p)
    return i / (area(g) + area(p) - i + 1e-9)


coco = json.load(open(GT, encoding="utf-8"))
names = {im["id"]: normalize(im["file_name"]) for im in coco["images"]}
gt = defaultdict(list)
for a in coco["annotations"]:
    x, y, w, h = [float(v) for v in a["bbox"]]
    gt[names[a["image_id"]]].append([x, y, x + w, y + h])
n_gt = sum(len(v) for v in gt.values())


def load(drop_fallback):
    ws = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)["Full_Results"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = list(rows[0])
    ni, hi = hdr.index("image_name"), hdr.index("hazards_json")
    recs = []  # (image, box or None, grounding source)
    for r in rows[1:]:
        if r[ni] is None or r[hi] in (None, "", "[]"):
            continue
        try:
            hz = json.loads(str(r[hi]))
        except json.JSONDecodeError:
            continue
        for h in hz:
            if str(h.get("hazard", "")).upper() in ("NO_HAZARD", "COMPLIANT"):
                continue
            if str(h.get("category", "")).upper() == "COMPLIANT":
                continue
            src = str(h.get("grounding_source") or "")
            bb = h.get("bbox_xyxy")
            box = None
            if bb and isinstance(bb, list) and len(bb) == 4 and all(v is not None for v in bb):
                b = [float(v) for v in bb]
                if b[2] > b[0] and b[3] > b[1]:
                    box = b
            if drop_fallback and src.startswith("DETR"):
                box = None
            recs.append((normalize(r[ni]), box, src))
    return recs


def score(recs):
    boxes = defaultdict(list)
    for img, b, _ in recs:
        if b is not None:
            boxes[img].append(b)
    cov_iog = sum(1 for img, gl in gt.items() for g in gl
                  if any(iog(g, p) >= 0.3 for p in boxes.get(img, [])))
    cov_iou = sum(1 for img, gl in gt.items() for g in gl
                  if any(iou(g, p) >= 0.5 for p in boxes.get(img, [])))
    no_box = sum(1 for r in recs if r[1] is None)
    return len(recs), no_box, cov_iog, cov_iou


rows = [("GROVE (full)", load(False)), ("GroundingDINO only (no fallback)", load(True))]
print(f"Reference boxes: {n_gt}")
print(f"{'Configuration':<36}{'records':>8}{'no box':>14}{'cov IoG>=0.3':>20}{'cov IoU>=0.5':>20}")
for label, recs in rows:
    n, nb, ci, cu = score(recs)
    print(f"{label:<36}{n:>8}{f'{nb} ({nb / n:.1%})':>14}"
          f"{f'{ci / n_gt:.4f} ({ci}/{n_gt})':>20}{f'{cu / n_gt:.4f} ({cu}/{n_gt})':>20}")
