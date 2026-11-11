import { entry, has } from "../../lib/numbers";
import { COLORS, fixed } from "../../lib/format";
import { ChartTable, PostHoc, tableCls } from "./ChartTable";
import { Plot, facetTitles } from "./plot";

type R = { set: string; label: string; key: string; color: string; reading: string; note?: string };
const ROWS: R[] = [
  { set: "Final", label: "GROVE top box", key: "final.box.grove.0.5.f1", color: COLORS.grove, reading: "pixels" },
  { set: "Final", label: "gemma4:31b", key: "final.box.gemma.0.5.f1", color: COLORS.gemma, reading: "as written (frozen pixel rule)" },
  { set: "Final", label: "gemma4:31b", key: "final.box.gemma_grid.0.5", color: COLORS.gemma, reading: "0–1000 grid", note: "sensitivity; not trusted (most boxes fit both readings)" },
  { set: "Final", label: "qwen3.5:27b", key: "final.box.qwen_as_written.0.5.f1", color: COLORS.qwen, reading: "as written (frozen pixel rule)" },
  { set: "Final", label: "qwen3.5:27b", key: "final.box.qwen_grid.0.5.f1", color: COLORS.qwen, reading: "0–1000 grid" },
  { set: "Calibration", label: "GROVE top box", key: "cal.box.grove.0.5", color: COLORS.grove, reading: "pixels" },
  { set: "Calibration", label: "gemma4:31b", key: "cal.box.gemma.as_written.0.5", color: COLORS.gemma, reading: "as written (frozen pixel rule)" },
  { set: "Calibration", label: "qwen3.5:27b", key: "cal.box.qwen.as_written.0.5", color: COLORS.qwen, reading: "as written (frozen pixel rule)" },
  { set: "Calibration", label: "qwen3.5:27b", key: "cal.box.qwen.grid.0.5", color: COLORS.qwen, reading: "0–1000 grid", note: "sensitivity; not trusted" },
  { set: "Development", label: "GROVE top box", key: "dev.box.grove.0.5", color: COLORS.grove, reading: "pixels" },
  { set: "Development", label: "gemma4:31b", key: "dev.box.gemma.as_written.0.5", color: COLORS.gemma, reading: "as written (frozen pixel rule)" },
  { set: "Development", label: "gemma4:31b", key: "dev.box.gemma.grid.0.5", color: COLORS.gemma, reading: "0–1000 grid", note: "sensitivity" },
  { set: "Development", label: "qwen3.5:27b", key: "dev.box.qwen.as_written.0.5", color: COLORS.qwen, reading: "as written (frozen pixel rule)" },
  { set: "Development", label: "qwen3.5:27b", key: "dev.box.qwen.grid.0.5", color: COLORS.qwen, reading: "0–1000 grid", note: "sensitivity" },
];
const SHORT_READ: Record<string, string> = { pixels: "top box", "as written (frozen pixel rule)": "as written", "0–1000 grid": "0–1000 grid" };
const PTS = ROWS.filter((r) => has(r.key)).map((r) => ({ ...r, v: entry(r.key).value as number, ph: entry(r.key).post_hoc, name: r.label === "GROVE top box" ? "GROVE top box" : `${r.label} · ${SHORT_READ[r.reading]}` }));

export default function Grounding() {
  const d = entry("final.box.grove_minus_qwen_grid.0.5");
  const make = (w: number) => {
    const ml = Math.min(185, Math.round(w * 0.45));
    return Plot.plot({
      marginBottom: 44,
      width: w,
      height: 440,
      marginLeft: ml,
      marginRight: 20,
      style: { background: "transparent", color: "currentColor", fontSize: "12px", fontFamily: "ui-sans-serif, system-ui, sans-serif" },
      x: { domain: [0, Math.max(...PTS.map((p) => p.v)) * 1.1], label: "Top-box F1 at IoU 0.5 →", labelOffset: 38, grid: true },
      y: { label: null },
      marginTop: 24,
      fy: { label: null, domain: ["Final", "Calibration", "Development"], axis: null, padding: 0.3 },
      marks: [
        facetTitles(["Final", "Calibration", "Development"], ml),
        Plot.barX(PTS, { fy: "set", y: "name", x: "v", fill: "color", fillOpacity: (p: (typeof PTS)[number]) => (p.reading.startsWith("0") ? 0.45 : 1) }),
        Plot.tip(PTS, Plot.pointer({ fy: "set", y: "name", x: "v", title: (p: (typeof PTS)[number]) => `${p.set}: ${p.name}\ntop-box F1 ${fixed(p.v, 4)}${p.ph ? " (post hoc)" : ""}${p.note ? "\n" + p.note : ""}` })),
      ],
    });
  };
  return (
    <ChartTable
      label="Top-box F1 at IoU 0.5 for GROVE and the single-pass models, as written and read on a 0-1000 grid, on each set"
      make={make}
      deps={[]}
      caption={
        <>
          The frozen rule reads a single-pass box as pixel coordinates; lighter bars read the same boxes on a 0&ndash;1000 grid (sensitivity analysis). On the final set,
          qwen3.5:27b&rsquo;s boxes read on the grid reach about the same top-box F1 as GROVE (GROVE minus qwen3.5:27b {fixed(d.value as number, 3)} [{fixed(d.interval![0], 3)}, {fixed(d.interval![1], 3)}]<PostHoc />).
          This does not show better localization in general.
        </>
      }
      table={
        <table className={tableCls}>
          <thead><tr><th className="text-left">Set</th><th className="text-left">System</th><th className="text-left">Box reading</th><th className="text-right">Top-box F1 at IoU 0.5</th></tr></thead>
          <tbody>
            {PTS.map((p) => (
              <tr key={p.key}><td>{p.set}</td><td>{p.label}{p.ph && <PostHoc />}</td><td>{p.reading}{p.note ? ` (${p.note})` : ""}</td><td className="text-right font-mono">{fixed(p.v, 4)}</td></tr>
            ))}
          </tbody>
        </table>
      }
    />
  );
}
