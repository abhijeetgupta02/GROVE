#!/usr/bin/env python3
"""Regenerate the qualitative figures (Figures 2 and 3) from the saved predictions.

No inference is run. The script reads the reference annotations, the saved GROVE
predictions and the saved single-pass Llama 3.2 Vision 11B predictions, and draws
the boxes exactly as stored. Figures are drawn at the journal's text width
(13.9 cm) so that fonts print at their nominal size.

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
import matplotlib.font_manager as fm  # noqa: E402
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

# Palette taken from Figure 1 of the paper (muted blue / green with an orange accent).
REF, GROVE, FALLBACK, BASE = "#2f62a8", "#2b7a5b", "#c0661c", "#a8392d"
INK, MUTED, RULE, CARD = "#1e1e1e", "#5f5f5f", "#bdbdbd", "#f4f5f6"
TEXT_WIDTH_IN = 13.9 / 2.54  # MDPI Applied Sciences text width

_serif = [f for f in ("Palatino", "TeX Gyre Pagella", "Palatino Linotype", "Book Antiqua")
          if any(x.name == f for x in fm.fontManager.ttflist)]
plt.rcParams.update({"font.family": "serif", "font.serif": _serif + ["DejaVu Serif"], "font.size": 7.0,
                     "axes.titlesize": 7.4, "axes.titleweight": "normal", "savefig.dpi": 450,
                     "pdf.fonttype": 42})


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


def image_axis(ax, im):
    ax.imshow(im)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_linewidth(0.4)
        s.set_color(RULE)


def fit_to_axis(fig, ax, t, min_size=5.0):
    """Shrink a text artist until it fits inside the axis width."""
    r = fig.canvas.get_renderer()
    width = ax.get_window_extent(r).width
    while t.get_window_extent(r).width > width and t.get_fontsize() > min_size:
        t.set_fontsize(t.get_fontsize() - 0.2)


def panel_title(ax, letter, text):
    t = ax.set_title(f"({letter}) {text}", loc="left", pad=2.5, color=INK)
    ax.figure.canvas.draw()
    fit_to_axis(ax.figure, ax, t)


def draw_box(ax, b, color, dashed=False, lw=1.1):
    ax.add_patch(patches.Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec=color, lw=lw,
                                   ls=(0, (3.5, 2)) if dashed else "solid", joinstyle="miter"))


def badge(ax, x, y, text, color, size=6.0):
    return ax.text(x, y, text, color="white", fontsize=size, ha="center", va="center", zorder=6,
                   bbox=dict(boxstyle="circle,pad=0.22", fc=color, ec="white", lw=0.5))


def tag(ax, text, color):
    return ax.text(0, 0, text, color="white", fontsize=5.6, ha="left", va="top", zorder=6,
                   bbox=dict(boxstyle="square,pad=0.18", fc=color, ec="none", alpha=0.92))


def _extent(fig, ax, t):
    r = fig.canvas.get_renderer()
    bb = t.get_bbox_patch().get_window_extent(r)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def place_tags(fig, ax, boxes, color, W, H):
    """One tag per distinct label at a corner of its box; tags never overlap each other or hide small boxes."""
    placed, done = [], set()
    m = 0.008 * W
    obstacles = [(b[0] - m, b[1] - m, b[2] - b[0] + 2 * m, b[3] - b[1] + 2 * m) for b, _ in boxes
                 if (b[2] - b[0]) * (b[3] - b[1]) < 0.05 * W * H]
    for b, lab in sorted(boxes, key=lambda bl: (bl[0][1], bl[0][0])):
        if lab in done:
            continue
        done.add(lab)
        t = tag(ax, lab, color)
        fig.canvas.draw()
        x0, y0, x1, y1 = _extent(fig, ax, t)
        w, h = x1 - x0, y1 - y0
        inside = [(b[0] + m, b[1] + m), (b[2] - w - m, b[1] + m), (b[0] + m, b[3] - h - m),
                  (b[2] - w - m, b[3] - h - m)] + [(b[0] + m, b[1] + m + k * (h + m)) for k in range(1, 6)]
        outside = [(b[0], b[1] - h - m), (b[0], b[3] + m), (b[2] - w, b[1] - h - m), (b[2] - w, b[3] + m)]
        small = (b[2] - b[0]) < 1.1 * w or (b[3] - b[1]) < 2.5 * h
        for x, y in (outside + inside if small else inside + outside):
            x = min(max(x, m), W - w - m)
            y = min(max(y, m), H - h - m)
            others = placed + [o for o in obstacles if not (o[0] <= b[0] and o[1] <= b[1] and
                                                             o[0] + o[2] >= b[2] and o[1] + o[3] >= b[3])]
            if not any(x < px + pw and px < x + w and y < py + ph and py < y + h for px, py, pw, ph in others):
                break
        placed.append((x, y, w, h))
        t.set_position((x - x0, y - y0))


def save(fig, out, name):
    for ext in ("png", "pdf"):
        try:
            fig.savefig(os.path.join(out, f"{name}.{ext}"), bbox_inches="tight", facecolor="white", pad_inches=0.015)
        except Exception as exc:  # some system fonts cannot be embedded in PDF
            print(f"skipped {name}.{ext}: {exc}")
    plt.close(fig)


def figure2(img_dir, grove, out, img="175.png"):
    im = Image.open(os.path.join(img_dir, img)).convert("RGB")
    W, H = im.size
    recs = grove[img]
    fig = plt.figure(figsize=(TEXT_WIDTH_IN, 2.85))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.12], wspace=0.045)
    ax = fig.add_subplot(gs[0, 0])
    image_axis(ax, im)
    panel_title(ax, "a", "Evidence boxes")
    r0 = 0.03 * W
    for i, r in enumerate(recs, 1):
        fb = r["src"].startswith("DETR")
        c = FALLBACK if fb else GROVE
        if r["box"]:
            b = r["box"]
            draw_box(ax, b, c, dashed=fb, lw=1.2)
            x = b[2] - r0 - 4 if fb else b[0] + r0 + 4
            badge(ax, min(max(x, r0), W - r0), min(max(b[1] + r0 + 4, r0), H - r0), str(i), c)
    ax.legend(handles=[Line2D([0], [0], color=GROVE, lw=1.2, label="GroundingDINO"),
                       Line2D([0], [0], color=FALLBACK, lw=1.2, ls=(0, (3.5, 2)), label="DETR + OpenCLIP fallback")],
              loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, fontsize=6.1,
              handlelength=1.8, columnspacing=1.2, handletextpad=0.5, borderaxespad=0.25)

    ax2 = fig.add_subplot(gs[0, 1])
    fig.canvas.draw()
    p, q = ax.get_position(), ax2.get_position()
    ax2.set_position([q.x0, p.y0, q.width, p.height])
    ax2.set_axis_off()
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    panel_title(ax2, "b", "Inspection records")
    n, gap = len(recs), 0.03
    hgt = (1 - gap * (n - 1)) / n
    for i, r in enumerate(recs, 1):
        fb = r["src"].startswith("DETR")
        c = FALLBACK if fb else GROVE
        y0 = 1 - i * hgt - (i - 1) * gap
        ax2.add_patch(patches.Rectangle((0.0, y0), 1.0, hgt, fc=CARD, ec=RULE, lw=0.4))
        ax2.add_patch(patches.Rectangle((0.0, y0), 0.011, hgt, fc=c, ec="none"))
        top = y0 + hgt - 0.048
        badge(ax2, 0.062, top, str(i), c, size=5.8)
        ax2.text(0.105, top, LABEL.get(r["cat"], r["cat"]), fontsize=7.2, color=INK, va="center",
                 fontweight="bold")
        risk = r["risk"].capitalize()
        ax2.text(0.975, top, f"{risk} risk", fontsize=6.3, color=MUTED, ha="right", va="center", style="italic")
        ax2.text(0.045, top - 0.052, textwrap.fill(r["text"], 48), fontsize=6.5, color=INK, va="top",
                 linespacing=1.15)
        if fb:
            mt = re.search(r"Sim=([0-9.]+).*Match='([^']+)'", r["src"])
            src = f"Box: fallback (DETR ‘{mt.group(2)}’, similarity {mt.group(1)})" if mt else r["src"]
        else:
            src = "Box: GroundingDINO"
        ax2.text(0.045, y0 + 0.026, src, fontsize=5.9, color=MUTED, va="bottom", style="italic")
    save(fig, out, "Fig2_reported")


def figure3(img_dir, gt, grove, llama, out, img="194.png"):
    im = Image.open(os.path.join(img_dir, img)).convert("RGB")
    W, H = im.size
    g = [(b, LABEL[c]) for b, c in gt[img]]
    ref = {lab for _, lab in g}
    gv = [(r["box"], LABEL.get(r["cat"], r["cat"])) for r in grove[img] if r["box"]]
    lv = [(r["box"], LABEL.get(r["cat"], r["cat"])) for r in llama[img] if r["box"]]
    panels = [("a", "Reference annotation", g, REF, False, f"{len(ref)} annotated categories"),
              ("b", "GROVE", gv, GROVE, False,
               f"{len({lab for _, lab in gv} & ref)} of {len(ref)} categories found"),
              ("c", "Llama 3.2 Vision 11B", lv, BASE, True,
               f"{len({lab for _, lab in lv} & ref)} of {len(ref)} found; full-image boxes")]
    fig = plt.figure(figsize=(TEXT_WIDTH_IN, 2.18))
    gs = fig.add_gridspec(1, 3, wspace=0.04)
    for k, (letter, title, boxes, col, dashed, note) in enumerate(panels):
        ax = fig.add_subplot(gs[0, k])
        image_axis(ax, im)
        panel_title(ax, letter, title)
        for b, _ in sorted(boxes, key=lambda bl: -((bl[0][2] - bl[0][0]) * (bl[0][3] - bl[0][1]))):
            cb = [min(max(b[0], 4), W - 4), min(max(b[1], 4), H - 4), min(max(b[2], 4), W - 4), min(max(b[3], 4), H - 4)]
            draw_box(ax, cb, col, dashed=dashed, lw=1.1)
        place_tags(fig, ax, boxes, col, W, H)
        nt = ax.text(0.0, -0.035, note, transform=ax.transAxes, fontsize=6.4, color=MUTED, va="top",
                     style="italic")
        fig.canvas.draw()
        fit_to_axis(fig, ax, nt)
    save(fig, out, "Fig3_reported")


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
    print("wrote Fig2_reported and Fig3_reported to", a.out)


if __name__ == "__main__":
    main()
