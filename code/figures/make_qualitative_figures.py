#!/usr/bin/env python3
"""Regenerate the qualitative figures (Figures 2 and 3) from the saved predictions.

No inference is run. The script reads the reference annotations, the saved GROVE
predictions and the saved single-pass Llama 3.2 Vision 11B predictions, and draws
the boxes exactly as stored.

Usage (from the repository root):
    python code/figures/make_qualitative_figures.py --images /path/to/evaluation/images --out figures/

The evaluation images are not redistributed in this repository (see README); pass the
folder that holds them with --images.
"""
import argparse
import json
import os
import re
import sys
import textwrap
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code", "inference"))
from shared.hazard_taxonomy import map_gt_category, map_pred_category  # noqa: E402

LABEL = {"Fall_Hazard": "Fall", "StruckBy_Hazard": "Struck-by", "Electrocution_Hazard": "Electrocution",
         "CaughtInBetween_hazard": "Caught-in/Between", "PPE_Violation": "PPE",
         "Housekeeping_Storage": "Housekeeping/Storage", "Other": "Other", "UNMAPPED": "Other"}
ORDER = ["Fall", "Struck-by", "Electrocution", "Caught-in/Between", "PPE", "Housekeeping/Storage", "Other"]
GREEN, ORANGE, BLUE, RED, INK, MUTED = "#1a7f5a", "#d9600f", "#2260b8", "#c23b2e", "#1f2328", "#5b636d"
RISK = {"High": "#c23b2e", "Medium": "#b07a06", "Low": "#6b7480"}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8.0,
                     "axes.titleweight": "bold", "savefig.dpi": 400})


def norm(n):
    s = os.path.basename(str(n).strip())
    s = re.sub(r"\.rf\.[a-zA-Z0-9]{6,}\.[a-zA-Z0-9]+$", "", s)
    s = re.sub(r"_(png|jpg|jpeg|webp|avif)$", r".\1", s, flags=re.I)
    b, e = os.path.splitext(s)
    return b + e.lower()


def load_gt(path):
    coco = json.load(open(path, encoding="utf-8"))
    cat = {c["id"]: map_gt_category(c["name"]) for c in coco["categories"]}
    names = {im["id"]: norm(im["file_name"]) for im in coco["images"]}
    gt = defaultdict(list)
    for a in coco["annotations"]:
        x, y, w, h = [float(v) for v in a["bbox"]]
        gt[names[a["image_id"]]].append(([x, y, x + w, y + h], cat[a["category_id"]]))
    return gt


def load_pred(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        recs = []
        for h in json.loads(d.get("hazards_json") or "[]"):
            if str(h.get("hazard", "")).upper() in ("NO_HAZARD", "COMPLIANT"):
                continue
            if str(h.get("category", "")).upper() == "COMPLIANT":
                continue
            bb = h.get("bbox_xyxy")
            box = [float(v) for v in bb] if bb and len(bb) == 4 and all(v is not None for v in bb) else None
            recs.append(dict(text=str(h.get("hazard", "")), cat=map_pred_category(h.get("category", "") or ""),
                             box=box, src=str(h.get("grounding_source") or ""), risk=str(h.get("risk_level") or "")))
        out[norm(d["image_name"])] = recs
    return out


def draw_box(ax, b, color, dashed=False, lw=1.5):
    ax.add_patch(patches.Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec=color, lw=lw,
                                   ls=(0, (4, 2.5)) if dashed else "solid", joinstyle="miter"))


def badge(ax, x, y, text, color, size=7.0):
    return ax.text(x, y, text, color="white", fontsize=size, fontweight="bold", ha="center", va="center",
                   zorder=6, bbox=dict(boxstyle="circle,pad=0.28", fc=color, ec="white", lw=0.8))


def tag(ax, x, y, text, color):
    return ax.text(x, y, text, color="white", fontsize=6.4, fontweight="bold", ha="left", va="top", zorder=6,
                   bbox=dict(boxstyle="square,pad=0.22", fc=color, ec="none"))


def _extent(fig, ax, t):
    """Data-coordinate extent (x0, y0, x1, y1) of a text artist, including its bbox patch."""
    r = fig.canvas.get_renderer()
    bb = t.get_bbox_patch().get_window_extent(r) if t.get_bbox_patch() else t.get_window_extent(r)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def place_tags(fig, ax, boxes, color, W, H):
    """Place one tag per distinct label, inside a corner of its first box, without overlaps or clipping."""
    placed, done = [], set()
    m = 0.008 * W
    # small boxes are obstacles: a tag must not hide another hazard's box
    obstacles = [(b[0] - m, b[1] - m, b[2] - b[0] + 2 * m, b[3] - b[1] + 2 * m) for b, _ in boxes
                 if (b[2] - b[0]) * (b[3] - b[1]) < 0.05 * W * H]
    for b, lab in sorted(boxes, key=lambda bl: (bl[0][1], bl[0][0])):
        if lab in done:
            continue
        done.add(lab)
        t = tag(ax, 0, 0, lab, color)
        fig.canvas.draw()
        x0, y0, x1, y1 = _extent(fig, ax, t)
        w, h = x1 - x0, y1 - y0
        inside = [(b[0] + m, b[1] + m), (b[2] - w - m, b[1] + m), (b[0] + m, b[3] - h - m),
                  (b[2] - w - m, b[3] - h - m)] + [(b[0] + m, b[1] + m + k * (h + m)) for k in range(1, 6)]
        outside = [(b[0], b[1] - h - m), (b[0], b[3] + m), (b[2] - w, b[1] - h - m), (b[2] - w, b[3] + m)]
        small = (b[2] - b[0]) < 1.1 * w or (b[3] - b[1]) < 2.5 * h
        cands = outside + inside if small else inside + outside
        for x, y in cands:
            x = min(max(x, m), W - w - m)
            y = min(max(y, m), H - h - m)
            others = placed + [o for o in obstacles if not (o[0] <= b[0] and o[1] <= b[1] and
                                                             o[0] + o[2] >= b[2] and o[1] + o[3] >= b[3])]
            if not any(x < px + pw and px < x + w and y < py + ph and py < y + h for px, py, pw, ph in others):
                break
        placed.append((x, y, w, h))
        pad = (x0 - 0, y0 - 0)
        t.set_position((x - pad[0], y - pad[1]))


def figure2(img_dir, grove, out, img="175.png"):
    im = Image.open(os.path.join(img_dir, img)).convert("RGB")
    W, H = im.size
    recs = grove[img]
    fig = plt.figure(figsize=(6.6, 3.45))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.08], wspace=0.04)
    ax = fig.add_subplot(gs[0, 0])
    ax.imshow(im)
    ax.set_axis_off()
    ax.set_title("(a) Evidence boxes on the input image", loc="left", pad=4)
    fig.canvas.draw()
    r0 = 0.032 * W
    for i, r in enumerate(recs, 1):
        fb = r["src"].startswith("DETR")
        c = ORANGE if fb else GREEN
        if r["box"]:
            b = r["box"]
            draw_box(ax, b, c, dashed=fb, lw=1.7)
            x = b[2] - r0 - 4 if fb else b[0] + r0 + 4
            badge(ax, min(max(x, r0), W - r0), min(max(b[1] + r0 + 4, r0), H - r0), str(i), c)
    ax.legend(handles=[Line2D([0], [0], color=GREEN, lw=1.8, label="GroundingDINO"),
                       Line2D([0], [0], color=ORANGE, lw=1.8, ls=(0, (3, 2)), label="DETR + OpenCLIP fallback")],
              loc="upper center", bbox_to_anchor=(0.5, -0.005), ncol=2, frameon=False, fontsize=6.4,
              handlelength=1.6, columnspacing=1.0, handletextpad=0.5)

    ax2 = fig.add_subplot(gs[0, 1])
    p, q = ax.get_position(), ax2.get_position()
    ax2.set_position([q.x0, p.y0, q.width, p.height])
    ax2.set_axis_off()
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.set_title("(b) Inspection records emitted by GROVE", loc="left", pad=4)
    n = len(recs)
    gap = 0.035
    hgt = (1 - gap * (n - 1)) / n
    for i, r in enumerate(recs, 1):
        fb = r["src"].startswith("DETR")
        c = ORANGE if fb else GREEN
        y0 = 1 - i * hgt - (i - 1) * gap
        ax2.add_patch(patches.FancyBboxPatch((0.0, y0), 1.0, hgt, boxstyle="round,pad=0,rounding_size=0.02",
                                             fc="#f6f7f9", ec="#d3d8de", lw=0.6))
        ax2.add_patch(patches.Rectangle((0.0, y0 + 0.004), 0.013, hgt - 0.008, fc=c, ec="none"))
        top = y0 + hgt - 0.058
        badge(ax2, 0.07, top, str(i), c, size=6.4)
        ax2.text(0.125, top, LABEL.get(r["cat"], r["cat"]), fontsize=7.4, fontweight="bold", color=INK,
                 va="center")
        risk = r["risk"].capitalize()
        ax2.text(0.97, top, f"{risk} risk", fontsize=6.2, fontweight="bold", color="white", ha="right",
                 va="center", bbox=dict(boxstyle="round,pad=0.25", fc=RISK.get(risk, MUTED), ec="none"))
        ax2.text(0.045, top - 0.065, textwrap.fill(r["text"], 48), fontsize=6.7, color=INK, va="top",
                 linespacing=1.25)
        if fb:
            m = re.search(r"Sim=([0-9.]+).*Match='([^']+)'", r["src"])
            src = (f"Box from fallback: DETR '{m.group(2)}', similarity {m.group(1)}" if m
                   else r["src"])
        else:
            src = "Box from GroundingDINO"
        ax2.text(0.045, y0 + 0.03, src, fontsize=6.2, color=MUTED, va="bottom", style="italic")
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out, f"Fig2_reported.{ext}"), bbox_inches="tight", facecolor="white",
                    pad_inches=0.02)
    plt.close(fig)


def figure3(img_dir, gt, grove, llama, out, img="194.png"):
    im = Image.open(os.path.join(img_dir, img)).convert("RGB")
    W, H = im.size
    g = [(b, LABEL[c]) for b, c in gt[img]]
    ref = {lab for _, lab in g}
    panels = [("(a) Reference annotation", g, BLUE, False),
              ("(b) GROVE", [(r["box"], LABEL.get(r["cat"], r["cat"])) for r in grove[img] if r["box"]], GREEN, False),
              ("(c) Single-pass Llama 3.2 Vision 11B",
               [(r["box"], LABEL.get(r["cat"], r["cat"])) for r in llama[img] if r["box"]], RED, True)]
    fig = plt.figure(figsize=(6.6, 2.72))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.17], hspace=0.03, wspace=0.035)
    for k, (title, boxes, col, dashed) in enumerate(panels):
        ax = fig.add_subplot(gs[0, k])
        ax.imshow(im)
        ax.set_axis_off()
        ax.set_title(title, loc="left", pad=3, fontsize=7.4)
        for b, _ in sorted(boxes, key=lambda bl: -((bl[0][2] - bl[0][0]) * (bl[0][3] - bl[0][1]))):
            cb = [min(max(b[0], 3), W - 3), min(max(b[1], 3), H - 3), min(max(b[2], 3), W - 3), min(max(b[3], 3), H - 3)]
            draw_box(ax, cb, col, dashed=dashed, lw=1.5)
        place_tags(fig, ax, boxes, col, W, H)
        axt = fig.add_subplot(gs[1, k])
        axt.set_axis_off()
        cats = sorted({lab for _, lab in boxes}, key=ORDER.index)
        if k == 0:
            line1, line2, c1 = f"{len(ref)} annotated categories", "", MUTED
        else:
            hit = [c for c in cats if c in ref]
            line1 = f"{len(hit)} of {len(ref)} categories found"
            line2 = "Both boxes span the whole image" if k == 2 else "Each hazard has its own box"
            c1 = GREEN if len(hit) == len(ref) else RED
        axt.text(0.0, 0.98, line1, fontsize=6.9, color=c1, fontweight="bold", va="top", transform=axt.transAxes)
        axt.text(0.0, 0.42, line2, fontsize=6.6, color=MUTED, va="top", transform=axt.transAxes)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out, f"Fig3_reported.{ext}"), bbox_inches="tight", facecolor="white",
                    pad_inches=0.02)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Regenerate Figures 2 and 3 from saved predictions.")
    ap.add_argument("--images", required=True, help="Folder with the 203 evaluation images.")
    ap.add_argument("--gt", default=os.path.join(ROOT, "data", "annotations.coco.json"))
    ap.add_argument("--grove", default=os.path.join(ROOT, "predictions", "grove", "grove_qwen35_9b_run1.jsonl"))
    ap.add_argument("--llama", default=os.path.join(ROOT, "predictions", "single_pass",
                                                     "llama32_vision_11b_apr2026_run1.jsonl"))
    ap.add_argument("--out", default=os.path.join(ROOT, "figures"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    gt, grove, llama = load_gt(a.gt), load_pred(a.grove), load_pred(a.llama)
    figure2(a.images, grove, a.out)
    figure3(a.images, gt, grove, llama, a.out)
    print("wrote Fig2_reported and Fig3_reported (.png, .pdf) to", a.out)


if __name__ == "__main__":
    main()
