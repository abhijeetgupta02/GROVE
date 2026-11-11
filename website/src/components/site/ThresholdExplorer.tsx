import { useMemo, useState } from "react";
import finalScores from "../../data/final_scores.json";
import calScores from "../../data/calibration_scores.json";
import thresholds from "../../data/thresholds.json";
import { COLORS, CAT_NAME, fixed } from "../../lib/format";
import { CATS, type Cat2, type Row, ge, metrics, prCurve, prPoint, PlotFigure, Plot } from "./plot";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const TH = thresholds as any;
const DATA = {
  final: (finalScores as unknown as { rows: Row[] }).rows,
  cal: (calScores as unknown as { rows: Row[] }).rows,
};
const REFIT = TH.refit.GROVE, FIRST = TH.first_freeze.GROVE, MAIN = TH.refit.main_question, SIGN = TH.signed_confidence;
const toK = (x: number) => Math.round(x * 100);
const fromK = (k: number) => Number((k / 100).toFixed(2));

type Sys = { key: string; label: string; color: string; postHoc: boolean; pred: (r: Row) => [boolean, boolean]; finalOnly?: boolean; note?: string };
const SYSTEMS: Sys[] = [
  { key: "refit", label: "GROVE, refit thresholds (used on the final set)", color: COLORS.grove, postHoc: false, pred: (r) => [ge(r.grove_fall, REFIT.fall), ge(r.grove_ppe, REFIT.ppe)] },
  { key: "first", label: "GROVE, first-freeze thresholds", color: COLORS.grove, postHoc: true, pred: (r) => [ge(r.grove_fall, FIRST.fall), ge(r.grove_ppe, FIRST.ppe)], note: "post hoc reporting on the final set" },
  { key: "main", label: "Main questions only (d3:27b), refit thresholds", color: COLORS.main, postHoc: false, pred: (r) => [ge(r.main_fall, MAIN.fall), ge(r.main_ppe, MAIN.ppe)] },
  { key: "gemma", label: "gemma4:31b, single pass (fixed answers)", color: COLORS.gemma, postHoc: false, pred: (r) => [r.gemma_fall === 1, r.gemma_ppe === 1] },
  { key: "qwen", label: "qwen3.5:27b, single pass (fixed answers)", color: COLORS.qwen, postHoc: true, finalOnly: true, pred: (r) => [r.qwen_fall === 1, r.qwen_ppe === 1] },
  { key: "gsign", label: "gemma4:31b, signed confidence", color: COLORS.gemma, postHoc: true, pred: (r) => [ge(r.gemma_signed_fall, SIGN.gemma.fall), ge(r.gemma_signed_ppe, SIGN.gemma.ppe)], note: "score redefined after the first scoring" },
  { key: "qsign", label: "qwen3.5:27b, signed confidence", color: COLORS.qwen, postHoc: true, pred: (r) => [ge(r.qwen_signed_fall, SIGN.qwen.fall), ge(r.qwen_signed_ppe, SIGN.qwen.ppe)], note: "score redefined after the first scoring" },
];

function Badge() {
  return <span className="ml-1 rounded bg-amber-200 px-1 text-[11px] font-semibold text-amber-950">post hoc</span>;
}

export default function ThresholdExplorer() {
  const [setKey, setSetKey] = useState<"final" | "cal">("final");
  const [kFall, setKFall] = useState(toK(REFIT.fall));
  const [kPpe, setKPpe] = useState(toK(REFIT.ppe));
  const tFall = fromK(kFall), tPpe = fromK(kPpe);
  const rows = DATA[setKey];
  const m = useMemo(() => metrics(rows, (r) => [ge(r.grove_fall, tFall), ge(r.grove_ppe, tPpe)]), [rows, tFall, tPpe]);
  const ref = useMemo(() => SYSTEMS.filter((s) => setKey === "final" || !s.finalOnly).map((s) => ({ ...s, m: metrics(rows, s.pred) })), [rows, setKey]);
  const curves = useMemo(() => {
    const out: Record<string, Record<string, { r: number; p: number; t: number }[]>> = {};
    for (const c of CATS) {
      out[c] = {
        grove: prCurve(rows, `grove_${c}`, `y_${c}`),
        main: prCurve(rows, `main_${c}`, `y_${c}`),
        gsign: prCurve(rows, `gemma_signed_${c}`, `y_${c}`),
        qsign: prCurve(rows, `qwen_signed_${c}`, `y_${c}`),
      };
    }
    return out;
  }, [rows]);
  const isRefit = kFall === toK(REFIT.fall) && kPpe === toK(REFIT.ppe);
  const isFirst = kFall === toK(FIRST.fall) && kPpe === toK(FIRST.ppe);

  function chart(c: Cat2, width: number) {
    const y = `y_${c}`;
    const t = c === "fall" ? tFall : tPpe;
    const pts = [
      { ...prPoint(rows, y, (r) => ge(r[`grove_${c}`], REFIT[c])), label: `GROVE, refit threshold ${fixed(REFIT[c], 2)}`, fill: COLORS.grove, stroke: COLORS.grove, symbol: "circle" },
      { ...prPoint(rows, y, (r) => ge(r[`grove_${c}`], FIRST[c])), label: `GROVE, first-freeze threshold ${fixed(FIRST[c], 2)}${setKey === "final" ? " (post hoc reporting)" : ""}`, fill: "none", stroke: COLORS.grove, symbol: "circle" },
      { ...prPoint(rows, y, (r) => ge(r[`main_${c}`], MAIN[c])), label: `Main questions, refit threshold ${fixed(MAIN[c], 2)}`, fill: COLORS.main, stroke: COLORS.main, symbol: "square" },
      { ...prPoint(rows, y, (r) => r[`gemma_${c}`] === 1), label: "gemma4:31b, fixed answers", fill: COLORS.gemma, stroke: COLORS.gemma, symbol: "diamond" },
      ...(setKey === "final" ? [{ ...prPoint(rows, y, (r) => r[`qwen_${c}`] === 1), label: "qwen3.5:27b, fixed answers (post hoc)", fill: COLORS.qwen, stroke: COLORS.qwen, symbol: "triangle" }] : []),
      { ...prPoint(rows, y, (r) => ge(r[`gemma_signed_${c}`], SIGN.gemma[c])), label: `gemma4:31b signed confidence, threshold ${fixed(SIGN.gemma[c], 2)} (post hoc)`, fill: "none", stroke: COLORS.gemma, symbol: "diamond" },
      { ...prPoint(rows, y, (r) => ge(r[`qwen_signed_${c}`], SIGN.qwen[c])), label: `qwen3.5:27b signed confidence, threshold ${fixed(SIGN.qwen[c], 2)} (post hoc)`, fill: "none", stroke: COLORS.qwen, symbol: "triangle" },
    ];
    const cur = { ...prPoint(rows, y, (r) => ge(r[`grove_${c}`], t)), label: `Sliders: threshold ${fixed(t, 2)}` };
    const line = (data: { r: number; p: number }[], stroke: string, dash?: string) =>
      Plot.line(data, { x: "r", y: "p", stroke, strokeWidth: 1.8, strokeDasharray: dash, curve: "step-before" });
    const cv = curves[c];
    return Plot.plot({
      width,
      height: Math.round(Math.min(width, 420) * 0.78),
      marginLeft: 44,
      style: { background: "transparent", color: "currentColor", fontSize: "12px", fontFamily: "ui-sans-serif, system-ui, sans-serif" },
      x: { domain: [0, 1], label: "Recall →", grid: true },
      y: { domain: [0, 1], label: "↑ Precision", grid: true },
      marks: [
        line(cv.qsign, COLORS.qwen, "5,4"),
        line(cv.gsign, COLORS.gemma, "5,4"),
        line(cv.main, COLORS.main),
        line(cv.grove, COLORS.grove),
        Plot.dot(pts, { x: "r", y: "p", fill: "fill", stroke: "stroke", symbol: "symbol", r: 6, strokeWidth: 2 }),
        Plot.dot([cur], { x: "r", y: "p", r: 10, stroke: "currentColor", strokeWidth: 2.5, fill: "none" }),
        Plot.tip([...pts, cur], Plot.pointer({ x: "r", y: "p", title: (d: { label: string; p: number; r: number }) => `${d.label}\nprecision ${fixed(d.p, 3)}, recall ${fixed(d.r, 3)}` })),
      ],
    });
  }

  return (
    <div className="not-prose font-sans">
      <div className="mb-3 flex flex-wrap items-center gap-2" role="group" aria-label="Image set">
        {(["final", "cal"] as const).map((s) => (
          <button key={s} type="button" aria-pressed={setKey === s} onClick={() => setSetKey(s)}
            className={`rounded-full border px-3 py-1 text-sm ${setKey === s ? "border-blue-700 bg-blue-700 text-white" : "border-zinc-300 dark:border-zinc-600"}`}>
            {s === "final" ? `Final set (${rows === DATA.final ? rows.length.toLocaleString("en-US") : DATA.final.length.toLocaleString("en-US")} images)` : `Calibration set (${DATA.cal.length.toLocaleString("en-US")} images, where the thresholds were fit)`}
          </button>
        ))}
      </div>
      <p className="m-0 mb-3 text-sm text-zinc-700 dark:text-zinc-300">
        {setKey === "final"
          ? "The thresholds were fixed on the calibration images before the final set was scored. Moving the sliders here uses final-set labels and is for illustration only."
          : "These are the images the thresholds were fit on, so every number in this view is in-sample, not an independent test."}
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        {CATS.map((c) => {
          const k = c === "fall" ? kFall : kPpe;
          const setK = c === "fall" ? setKFall : setKPpe;
          return (
            <div key={c}>
              <label className="block text-sm font-semibold" htmlFor={`th-${c}`}>
                {CAT_NAME[c]} threshold: <span className="font-mono">{fixed(fromK(k), 2)}</span>
              </label>
              <input id={`th-${c}`} type="range" min={0} max={100} step={1} value={k} onChange={(e) => setK(Number(e.target.value))}
                aria-valuetext={`${fixed(fromK(k), 2)}`} className="w-full accent-blue-700" />
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex flex-wrap gap-2 text-sm">
        <button type="button" className="rounded-md border border-zinc-300 px-3 py-1 dark:border-zinc-600" onClick={() => { setKFall(toK(REFIT.fall)); setKPpe(toK(REFIT.ppe)); }}>
          Set to the refit thresholds ({fixed(REFIT.fall, 2)}, {fixed(REFIT.ppe, 2)})
        </button>
        <button type="button" className="rounded-md border border-zinc-300 px-3 py-1 dark:border-zinc-600" onClick={() => { setKFall(toK(FIRST.fall)); setKPpe(toK(FIRST.ppe)); }}>
          Set to the first-freeze thresholds ({fixed(FIRST.fall, 2)}, {fixed(FIRST.ppe, 2)})
        </button>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4" aria-live="polite" data-testid="explorer-stats">
        {[
          ["Micro-F1", fixed(m.f1, 3), "explorer-f1"],
          ["Precision", fixed(m.precision, 3), "explorer-precision"],
          ["Recall", fixed(m.recall, 3), "explorer-recall"],
          ["False alarms per 100 violation-free images", fixed(m.fa, 1), "explorer-fa"],
        ].map(([l, v, id]) => (
          <div key={id} className="rounded-lg border border-zinc-200 p-3 dark:border-zinc-700">
            <div className="text-xs text-zinc-600 dark:text-zinc-300">{l}</div>
            <div className="font-mono text-2xl" data-testid={id}>{v}</div>
          </div>
        ))}
      </div>
      <p className="m-0 mt-2 text-sm text-zinc-700 dark:text-zinc-300">
        GROVE at these thresholds on the {setKey === "final" ? "final" : "calibration"} images. F1 per category: Fall {fixed(m.fall.f1, 3)}, protective equipment {fixed(m.ppe.f1, 3)}.
        {isRefit && (setKey === "final" ? " These are the thresholds used on the final set." : " These are the refit thresholds (fit on these images).")}
        {isFirst && (setKey === "final" ? <> First-freeze thresholds on the final set<Badge />.</> : " First-freeze thresholds (fit on the development images).")}
      </p>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {CATS.map((c) => (
          <figure key={c} className="m-0">
            <PlotFigure label={`Precision-recall curves for ${CAT_NAME[c]} on the ${setKey === "final" ? "final" : "calibration"} set, with the slider position and reference points`} deps={[c, rows, kFall, kPpe, setKey]} make={(w) => chart(c, w)} />
            <figcaption className="text-center text-sm">{CAT_NAME[c]}</figcaption>
          </figure>
        ))}
      </div>
      <ul className="m-0 mt-2 flex list-none flex-wrap gap-x-4 gap-y-1 p-0 text-xs">
        <li><span className="inline-block h-0.5 w-5 align-middle" style={{ background: COLORS.grove }} /> GROVE score</li>
        <li><span className="inline-block h-0.5 w-5 align-middle" style={{ background: COLORS.main }} /> Main questions score</li>
        <li><span className="inline-block w-5 border-t-2 border-dashed align-middle" style={{ borderColor: COLORS.gemma }} /> gemma4:31b signed confidence<Badge /></li>
        <li><span className="inline-block w-5 border-t-2 border-dashed align-middle" style={{ borderColor: COLORS.qwen }} /> qwen3.5:27b signed confidence<Badge /></li>
        <li>Filled markers: fixed answers or refit thresholds. Hollow markers: first-freeze and signed-confidence thresholds. Large ring: the sliders.</li>
      </ul>
      <details className="mt-4">
        <summary className="cursor-pointer text-sm font-semibold">Show table: every system on this set</summary>
        <div className="overflow-x-auto">
          <table className="mt-2 w-full text-sm">
            <thead>
              <tr><th className="text-left">System</th><th className="text-right">Micro-F1</th><th className="text-right">Precision</th><th className="text-right">Recall</th><th className="text-right">False alarms per 100 violation-free images</th></tr>
            </thead>
            <tbody>
              {ref.map((s) => (
                <tr key={s.key}>
                  <td>
                    <span className="mr-1 inline-block h-3 w-3 rounded-sm align-middle" style={{ background: s.color }} aria-hidden="true" />
                    {s.label}{s.postHoc && (setKey === "final" || s.key !== "first") ? <Badge /> : null}
                    {s.note && (setKey === "final" || s.key !== "first") ? <span className="text-xs text-zinc-600 dark:text-zinc-300"> ({s.note})</span> : null}
                  </td>
                  <td className="text-right font-mono">{fixed(s.m.f1, 3)}</td>
                  <td className="text-right font-mono">{fixed(s.m.precision, 3)}</td>
                  <td className="text-right font-mono">{fixed(s.m.recall, 3)}</td>
                  <td className="text-right font-mono">{fixed(s.m.fa, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
