// Small helpers shared by the charts: metrics from per-image rows, precision-recall curves, and a React wrapper
// that renders an Observable Plot chart (bundled locally; no CDN).
import { useEffect, useRef } from "react";
import * as Plot from "@observablehq/plot";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Row = Record<string, any>;
export const CATS = ["fall", "ppe"] as const;
export type Cat2 = (typeof CATS)[number];

export function ge(x: number | null | undefined, t: number): boolean {
  return x !== null && x !== undefined && x >= t;
}
/** Same definitions as grove_score.summary: micro counts over Fall and protective equipment; false alarms are
 *  false-positive image-category pairs on violation-free images per 100 violation-free images. */
export function metrics(rows: Row[], pred: (r: Row) => [boolean, boolean]) {
  let tp = 0, fp = 0, fn = 0, fa = 0, neg = 0;
  const cat = { fall: { tp: 0, fp: 0, fn: 0 }, ppe: { tp: 0, fp: 0, fn: 0 } };
  for (const r of rows) {
    const y: [boolean, boolean] = [r.y_fall === 1, r.y_ppe === 1];
    const p = pred(r);
    const isNeg = !y[0] && !y[1];
    if (isNeg) neg++;
    CATS.forEach((c, j) => {
      const a = p[j], b = y[j];
      if (a && b) { tp++; cat[c].tp++; }
      if (a && !b) { fp++; cat[c].fp++; if (isNeg) fa++; }
      if (!a && b) { fn++; cat[c].fn++; }
    });
  }
  const f1 = (t: { tp: number; fp: number; fn: number }) => (2 * t.tp) / Math.max(2 * t.tp + t.fp + t.fn, 1e-9);
  return {
    precision: tp / Math.max(tp + fp, 1e-9),
    recall: tp / Math.max(tp + fn, 1e-9),
    f1: f1({ tp, fp, fn }),
    fa: (100 * fa) / Math.max(neg, 1),
    fall: { ...cat.fall, f1: f1(cat.fall), p: cat.fall.tp / Math.max(cat.fall.tp + cat.fall.fp, 1e-9), r: cat.fall.tp / Math.max(cat.fall.tp + cat.fall.fn, 1e-9) },
    ppe: { ...cat.ppe, f1: f1(cat.ppe), p: cat.ppe.tp / Math.max(cat.ppe.tp + cat.ppe.fp, 1e-9), r: cat.ppe.tp / Math.max(cat.ppe.tp + cat.ppe.fn, 1e-9) },
  };
}
/** Per-category precision-recall points at every distinct score (flag if score >= value). */
export function prCurve(rows: Row[], scoreKey: string, labelKey: string) {
  const pts = rows.map((r) => ({ s: r[scoreKey] ?? -1, y: r[labelKey] === 1 })).sort((a, b) => b.s - a.s);
  const pos = pts.filter((x) => x.y).length;
  const out: { r: number; p: number; t: number }[] = [];
  let tp = 0, fp = 0;
  for (let i = 0; i < pts.length; i++) {
    if (pts[i].y) tp++; else fp++;
    if (i === pts.length - 1 || pts[i + 1].s !== pts[i].s) out.push({ r: tp / Math.max(pos, 1), p: tp / Math.max(tp + fp, 1e-9), t: pts[i].s });
  }
  return out;
}
export function prPoint(rows: Row[], labelKey: string, pred: (r: Row) => boolean) {
  let tp = 0, fp = 0, pos = 0;
  for (const r of rows) {
    const y = r[labelKey] === 1, a = pred(r);
    if (y) pos++;
    if (a && y) tp++;
    if (a && !y) fp++;
  }
  return { r: tp / Math.max(pos, 1), p: tp / Math.max(tp + fp, 1e-9) };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function PlotFigure({ make, deps, label }: { make: (width: number) => any; deps: unknown[]; label: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let chart: Element | null = null;
    let lastW = -1;
    const draw = () => {
      const w = Math.max(260, Math.min(Math.floor(el.clientWidth), 760));
      if (w === lastW && chart) return;
      lastW = w;
      const c = make(w) as Element;
      // The container carries the description (role="img" + aria-label) and every chart has a table view, so the
      // chart's own SVG labels are hidden from assistive technology.
      c.setAttribute("aria-hidden", "true");
      c.querySelectorAll("[aria-label],[aria-description]").forEach((e) => { e.removeAttribute("aria-label"); e.removeAttribute("aria-description"); });
      chart?.remove();
      chart = c;
      el.append(c);
    };
    draw();
    const ro = new ResizeObserver(() => draw());
    ro.observe(el);
    return () => {
      ro.disconnect();
      chart?.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return <div ref={ref} role="img" aria-label={label} className="plot-host w-full" />;
}
/** Facet titles drawn above each facet (instead of the default labels at the right, which narrow screens clip). */
export function facetTitles(domain: string[], marginLeft = 0, channel = "fy") {
  return Plot.text(
    domain.map((d) => ({ [channel]: d, t: d })),
    { [channel]: channel, text: "t", frameAnchor: "top-left", dx: -marginLeft, dy: -14, textAnchor: "start", fontWeight: 600, fontSize: 12 },
  );
}
export { Plot };
