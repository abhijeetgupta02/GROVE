import { useState } from "react";
import { entry, has, fmtInt, str } from "../../lib/numbers";
import { COLORS, CAT_NAME, fixed, interval } from "../../lib/format";
import { ChartTable, PostHoc, tableCls } from "./ChartTable";
import { Plot, facetTitles } from "./plot";

type SetKey = "dev" | "cal" | "final";
const SETS: { key: SetKey; label: string; note: string }[] = [
  { key: "dev", label: `Development (${fmtInt("dev.n_images")})`, note: `${fmtInt("dev.n_images")} development images; Fall, Electrical and protective equipment. GROVE and the main questions use held-out thresholds (${str("method.cv_repeats")} repeats of ${str("method.cv_folds")} grouped folds); single-pass models use their fixed answers.` },
  { key: "cal", label: `Calibration (${fmtInt("cal.n_images")})`, note: `${fmtInt("cal.n_images")} calibration images; Fall and protective equipment. The thresholds were fit on these images, so this is not an independent test.` },
  { key: "final", label: `Final (${fmtInt("final.n_images")})`, note: `${fmtInt("final.n_images")} final images, scored once with thresholds fixed beforehand. qwen3.5:27b was run on the final images after final scoring (post hoc).` },
];
const SYS = [
  { key: "grove", label: "GROVE", color: COLORS.grove },
  { key: "main", label: "Main questions (d3:27b)", color: COLORS.main },
  { key: "gemma", label: "gemma4:31b single pass", color: COLORS.gemma },
  { key: "qwen", label: "qwen3.5:27b single pass", color: COLORS.qwen },
];
function cats(s: SetKey) {
  return s === "dev" ? ["fall", "electrical", "ppe"] : ["fall", "ppe"];
}
/** Key of the per-category F1 entry: Table 4 entries (with intervals) where they exist, otherwise the summary entry. */
function catKey(s: SetKey, sys: string, c: string, q: "f1" | "precision" | "recall") {
  const t = `${s}.table4.${sys}.${c}.${q}`;
  return has(t) ? t : `${s}.${sys}.${c}.${q}`;
}
function postHoc(s: SetKey, sys: string) {
  return entry(`${s}.${sys}.micro_f1`).post_hoc;
}
type Pt = { sys: string; label: string; color: string; metric: string; v: number; lo?: number; hi?: number; key: string; ph: boolean };
function points(s: SetKey): Pt[] {
  const out: Pt[] = [];
  for (const y of SYS) {
    const ph = postHoc(s, y.key);
    const mk = `${s}.${y.key}.micro_f1`, me = entry(mk);
    out.push({ sys: y.key, label: y.label, color: y.color, metric: "Micro-F1", v: me.value as number, lo: me.interval?.[0], hi: me.interval?.[1], key: mk, ph });
    for (const c of cats(s)) {
      const k = catKey(s, y.key, c, "f1"), e = entry(k);
      out.push({ sys: y.key, label: y.label, color: y.color, metric: `${CAT_NAME[c]} F1`, v: e.value as number, lo: e.interval?.[0], hi: e.interval?.[1], key: k, ph: ph || e.post_hoc });
    }
  }
  return out;
}

export default function Results() {
  const [s, setS] = useState<SetKey>("final");
  const pts = points(s);
  const metricsOrder = ["Micro-F1", ...cats(s).map((c) => `${CAT_NAME[c]} F1`)];
  const make = (w: number) => {
    const ml = Math.min(170, Math.round(w * 0.42));
    return Plot.plot({
      marginBottom: 44,
      width: w,
      height: 70 + metricsOrder.length * 130,
      marginLeft: ml,
      marginRight: 16,
      marginTop: 24,
      style: { background: "transparent", color: "currentColor", fontSize: "12px", fontFamily: "ui-sans-serif, system-ui, sans-serif" },
      x: { domain: [0, 1], label: "F1 \u2192", labelOffset: 38, grid: true },
      y: { label: null, domain: SYS.map((x) => x.label) },
      fy: { label: null, domain: metricsOrder, axis: null, padding: 0.3 },
      marks: [
        facetTitles(metricsOrder, ml),
        Plot.ruleY(pts.filter((p) => p.lo !== undefined), { fy: "metric", y: "label", x1: "lo", x2: "hi", stroke: "color", strokeWidth: 2 }),
        Plot.dot(pts, { fy: "metric", y: "label", x: "v", fill: (d: Pt) => (d.ph ? "none" : d.color), stroke: "color", r: 5, strokeWidth: 2 }),
        Plot.tip(pts, Plot.pointer({ fy: "metric", y: "label", x: "v", title: (d: Pt) => `${d.label}, ${d.metric}: ${fixed(d.v, 3)}${d.lo !== undefined ? " " + interval([d.lo, d.hi!], 3) : ""}${d.ph ? " (post hoc)" : ""}\nsource: ${entry(d.key).source}` })),
      ],
    });
  };
  const setNote = SETS.find((x) => x.key === s)!.note;
  return (
    <div className="not-prose font-sans">
      <div className="mb-3 flex flex-wrap gap-2" role="group" aria-label="Image set">
        {SETS.map((x) => (
          <button key={x.key} type="button" aria-pressed={s === x.key} onClick={() => setS(x.key)}
            className={`rounded-full border px-3 py-1 text-sm ${s === x.key ? "border-blue-700 bg-blue-700 text-white" : "border-zinc-300 dark:border-zinc-600"}`}>
            {x.label}
          </button>
        ))}
      </div>
      <p className="m-0 mb-3 text-sm text-zinc-700 dark:text-zinc-300">{setNote}</p>
      <h3 className="mt-0 text-lg font-semibold">Table 4. F1, precision and recall per category</h3>
      <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Table 4, scrollable">
        <table className={tableCls}>
          <thead>
            <tr><th className="text-left">System</th><th className="text-left">Category</th><th className="text-right">F1 [95% interval]</th><th className="text-right">Precision</th><th className="text-right">Recall</th></tr>
          </thead>
          <tbody>
            {SYS.flatMap((y) =>
              cats(s).map((c) => {
                const f = entry(catKey(s, y.key, c, "f1"));
                return (
                  <tr key={y.key + c}>
                    <td><span className="mr-1 inline-block h-3 w-3 rounded-sm align-middle" style={{ background: y.color }} aria-hidden="true" />{y.label}{postHoc(s, y.key) && <PostHoc />}</td>
                    <td>{CAT_NAME[c]}</td>
                    <td className="text-right font-mono" title={`source: ${f.source}`}>{fixed(f.value as number, 3)} {f.interval ? interval(f.interval, 3) : ""}</td>
                    <td className="text-right font-mono">{fixed(entry(catKey(s, y.key, c, "precision")).value as number, 3)}</td>
                    <td className="text-right font-mono">{fixed(entry(catKey(s, y.key, c, "recall")).value as number, 3)}</td>
                  </tr>
                );
              }),
            )}
          </tbody>
        </table>
      </div>
      <p className="m-0 mt-1 text-xs text-zinc-600 dark:text-zinc-300">Intervals: paired bootstrap by near-copy group ({Number(str("method.bootstrap_draws")).toLocaleString("en-US")} draws), where the run saved them. Hover a value to see its source file.</p>
      <h3 className="mt-6 text-lg font-semibold">Figure 4. Micro-F1 and F1 per category, by system</h3>
      <ChartTable
        label={`Dot plot of micro-F1 and F1 per category for each system on the ${s} set, with 95% intervals where saved`}
        make={make}
        deps={[s]}
        caption={<>Filled dots: planned analyses. Hollow dots: post hoc. Lines: 95% intervals where saved.</>}
        table={
          <table className={tableCls}>
            <thead><tr><th className="text-left">System</th>{metricsOrder.map((m) => <th key={m} className="text-right">{m}</th>)}<th className="text-right">False alarms per 100 violation-free images</th></tr></thead>
            <tbody>
              {SYS.map((y) => (
                <tr key={y.key}>
                  <td>{y.label}{postHoc(s, y.key) && <PostHoc />}</td>
                  {metricsOrder.map((m) => {
                    const p = pts.find((q) => q.sys === y.key && q.metric === m)!;
                    return <td key={m} className="text-right font-mono">{fixed(p.v, 3)}{p.lo !== undefined ? " " + interval([p.lo, p.hi!], 3) : ""}</td>;
                  })}
                  <td className="text-right font-mono">{fixed(entry(`${s}.${y.key}.false_alarms`).value as number, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      />
    </div>
  );
}
