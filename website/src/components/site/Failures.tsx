import { useState } from "react";
import errors from "../../data/errors.json";
import { IMAGES, G, Card, Lightbox } from "./GalleryParts";
import type { GalleryImage, Layers } from "./ImageBoxes";
import { COLORS, CAT_NAME, fixed } from "../../lib/format";
import { ChartTable, PostHoc, tableCls } from "./ChartTable";
import { Plot, facetTitles } from "./plot";
import { fmtInt } from "../../lib/numbers";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const E = errors as any;
const FAILS: GalleryImage[] = IMAGES.filter((x: GalleryImage) => x.role === "failure");

/** One plain sentence per failure, built from the image's saved data. */
function sentence(img: GalleryImage): string {
  const th = G.thresholds_refit;
  const e = img.error?.[0];
  const c: string = e?.category ?? "ppe";
  const sc = `${fixed(img.grove.scores[c], 2)} against a threshold of ${fixed(th[c], 2)}`;
  switch (img.failure_type) {
    case "false alarm on a vest in daylight":
      return `In daylight GROVE flagged a missing vest ("${img.grove.phrase.ppe}", score ${sc}), but the labels mark no protective-equipment violation.`;
    case "miss":
      return `The labels mark a protective-equipment violation${img.label_reason.ppe ? ` ("${img.label_reason.ppe}")` : ""}, but GROVE's score stayed below the threshold (${sc}).`;
    case "right category, wrong worker boxed":
      return `GROVE was right that protective equipment is missing, but its evidence box is on a different worker: it does not overlap the labeled box.`;
    case "night-time miss":
      return `At night GROVE missed the labeled ${CAT_NAME[c].toLowerCase()} violation (score ${sc}).`;
    case "miss on height or depth":
      return `The labeled fall hazard depends on height or depth${img.label_reason.fall ? ` ("${img.label_reason.fall}")` : ""}; GROVE did not flag it (score ${sc}).`;
    default:
      return `GROVE's decision differs from the label.`;
  }
}

type Bar = { sys: string; type: string; cls: string; n: number };
const BARS: Bar[] = Object.entries(E.systems as Record<string, { type: string; class: string; all: number }[]>).flatMap(([sys, rows]) =>
  rows.map((r) => ({ sys: sys === "GROVE" ? "GROVE" : "gemma4:31b", type: r.type, cls: r.class.replace("inferred height or depth", "height or depth"), n: r.all })),
);

export default function Failures({ base }: { base: string }) {
  const [open, setOpen] = useState<number | null>(null);
  const layers: Layers = { labels: true, grove: true, gemma: false };
  const make = (w: number) => {
    const ml = Math.min(200, Math.round(w * 0.5));
    return Plot.plot({
      marginBottom: 44,
      width: w,
      height: 320,
      marginLeft: ml,
      marginRight: 20,
      style: { background: "transparent", color: "currentColor", fontSize: "12px", fontFamily: "ui-sans-serif, system-ui, sans-serif" },
      x: { label: "Image-category errors on the final set →", labelOffset: 38, grid: true },
      y: { label: null },
      color: { domain: ["GROVE", "gemma4:31b"], range: [COLORS.grove, COLORS.gemma] },
      marginTop: 24,
      fy: { label: null, domain: ["false alarm", "miss"], axis: null, padding: 0.3 },
      marks: [
        facetTitles(["false alarm", "miss"], ml),
        Plot.barX(BARS, { fy: "type", y: (d: Bar) => `${d.cls} · ${d.sys}`, x: "n", fill: "sys", insetTop: 1, insetBottom: 1 }),
        Plot.tip(BARS, Plot.pointer({ fy: "type", y: (d: Bar) => `${d.cls} · ${d.sys}`, x: "n", title: (d: Bar) => `${d.sys}: ${d.type}, ${d.cls}: ${d.n}` })),
      ],
    });
  };
  return (
    <div className="not-prose font-sans">
      <ul className="m-0 grid list-none grid-cols-1 gap-3 p-0 sm:grid-cols-2 lg:grid-cols-3">
        {FAILS.map((img, k) => (
          <Card key={img.id} img={img} base={base} layers={layers} onOpen={() => setOpen(k)} sentence={`${img.failure_type[0].toUpperCase()}${img.failure_type.slice(1)}. ${sentence(img)}`} />
        ))}
      </ul>
      <Lightbox list={FAILS} index={open} setIndex={setOpen} base={base} layers={layers} />
      <h3 className="mt-6 text-lg font-semibold">Error types on all final images<PostHoc /></h3>
      <ChartTable
        label="Counts of false alarms and misses by error class for GROVE and gemma4:31b on the final set"
        make={make}
        deps={[]}
        caption={<>Classes come from keywords in the system text and the dataset reason; &ldquo;other or no text&rdquo; means no keyword matched. Counted on the {fmtInt("final.n_images")} final images after final scoring. Bars: GROVE (blue) and <span className="font-mono">gemma4:31b</span> (orange).</>}
        table={
          <table className={tableCls}>
            <thead><tr><th className="text-left">System</th><th className="text-left">Type</th><th className="text-left">Class</th><th className="text-right">Errors</th></tr></thead>
            <tbody>{BARS.map((b) => <tr key={b.sys + b.type + b.cls}><td>{b.sys}</td><td>{b.type}</td><td>{b.cls}</td><td className="text-right font-mono">{b.n}</td></tr>)}</tbody>
          </table>
        }
      />
    </div>
  );
}
