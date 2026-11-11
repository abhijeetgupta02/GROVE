import { entry, val } from "../../lib/numbers";
import { COLORS, fixed, signed, interval } from "../../lib/format";
import { ChartTable, tableCls } from "./ChartTable";
import { Plot } from "./plot";

const ROWS = [
  { set: "Development", key: "dev.removal.16", label: "Main questions only" },
  { set: "Development", key: "dev.removal.17", label: "No protection term" },
  { set: "Development", key: "dev.removal.18", label: "No worker-visible term" },
  { set: "Development", key: "dev.removal.20", label: "One threshold for all" },
  { set: "Development", key: "dev.removal.21", label: "Fixed threshold" },
  { set: "Final", key: "final.removal.variant_no_fact_questions", label: "Main questions only" },
  { set: "Final", key: "final.removal.variant_no_protection", label: "No protection term" },
  { set: "Final", key: "final.removal.variant_no_worker", label: "No worker-visible term" },
];
type P = { set: string; label: string; d: number; lo: number; hi: number; f1: number };
const PTS: P[] = ROWS.map((r) => {
  const e = entry(r.key + ".diff");
  return { set: r.set, label: r.label, d: e.value as number, lo: e.interval![0], hi: e.interval![1], f1: val(r.key + ".micro_f1") };
});
const X = [Math.min(...PTS.map((p) => p.lo)) * 1.05, Math.max(0, ...PTS.map((p) => p.hi)) * 1.15];

function one(set: string, w: number) {
  const pts = PTS.filter((p) => p.set === set);
  return Plot.plot({
    width: w,
    height: 54 + pts.length * 30,
    marginBottom: 44,
    marginLeft: Math.min(160, Math.round(w * 0.42)),
    marginRight: 16,
    style: { background: "transparent", color: "currentColor", fontSize: "12px", fontFamily: "ui-sans-serif, system-ui, sans-serif" },
    x: { domain: X, label: `${set}: micro-F1 change against GROVE →`, labelOffset: 38, grid: true },
    y: { label: null, domain: pts.map((p) => p.label) },
    marks: [
      Plot.ruleX([0], { stroke: "currentColor", strokeOpacity: 0.6 }),
      Plot.ruleY(pts, { y: "label", x1: "lo", x2: "hi", stroke: COLORS.grove, strokeWidth: 2 }),
      Plot.dot(pts, { y: "label", x: "d", fill: COLORS.grove, r: 5 }),
      Plot.tip(pts, Plot.pointer({ y: "label", x: "d", title: (p: P) => `${p.set}: ${p.label}\nchange ${signed(p.d, 4)} ${interval([p.lo, p.hi], 4, true)}; micro-F1 ${fixed(p.f1, 4)}` })),
    ],
  });
}

export default function Removal() {
  const make = (w: number) => {
    const box = document.createElement("div");
    box.append(one("Development", w), one("Final", w));
    return box;
  };
  return (
    <ChartTable
      label="Micro-F1 change when one part of GROVE is removed, with 95% intervals, on the development and final sets"
      make={make}
      deps={[]}
      caption={
        <>
          Development: GROVE micro-F1 {fixed(val("dev.removal.grove.micro_f1"), 3)} with held-out thresholds. Final: GROVE {fixed(val("final.grove.micro_f1"), 3)}; each variant uses the thresholds frozen for it before the final images were scored. Lines: 95% intervals (paired bootstrap).
        </>
      }
      table={
        <table className={tableCls}>
          <thead><tr><th className="text-left">Set</th><th className="text-left">Change</th><th className="text-right">Micro-F1</th><th className="text-right">Change against GROVE [95% interval]</th></tr></thead>
          <tbody>
            {PTS.map((p) => (
              <tr key={p.set + p.label}><td>{p.set}</td><td>{p.label}</td><td className="text-right font-mono">{fixed(p.f1, 4)}</td><td className="text-right font-mono">{signed(p.d, 4)} {interval([p.lo, p.hi], 4, true)}</td></tr>
            ))}
          </tbody>
        </table>
      }
    />
  );
}
