import { useEffect, useState } from "react";
import { ReactCompareSlider } from "react-compare-slider";
import gallery from "../../data/gallery.json";
import { ImageBoxes, type GalleryImage } from "./ImageBoxes";
import { CAT_NAME, COLORS, fixed } from "../../lib/format";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const G = gallery as any;

export function useReducedMotion(): boolean {
  const [reduce, setReduce] = useState(false);
  useEffect(() => {
    const m = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (!m) return;
    setReduce(m.matches);
    const f = () => setReduce(m.matches);
    m.addEventListener("change", f);
    return () => m.removeEventListener("change", f);
  }, []);
  return reduce;
}

function GemmaPanel({ img }: { img: GalleryImage }) {
  return (
    <div className="font-sans text-sm leading-snug">
      <p className="m-0 font-semibold">
        <span className="mr-1 inline-block h-3 w-3 rounded-sm align-middle" style={{ background: COLORS.gemma }} aria-hidden="true" />
        <span className="font-mono">gemma4:31b</span>, single pass
      </p>
      <ul className="m-0 list-none p-0">
        {(["fall", "ppe"] as const).map((c) => (
          <li key={c} className="m-0 p-0">
            <strong>{CAT_NAME[c]}:</strong> {img.gemma.decisions[c] ? "alert" : "no alert"}
            {img.gemma.decisions[c] && img.gemma.evidence[c] ? <> &ldquo;{img.gemma.evidence[c]}&rdquo;</> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
function GrovePanel({ img }: { img: GalleryImage }) {
  const th = G.thresholds_refit;
  return (
    <div className="font-sans text-sm leading-snug">
      <p className="m-0 font-semibold">
        <span className="mr-1 inline-block h-3 w-3 rounded-sm align-middle" style={{ background: COLORS.grove }} aria-hidden="true" />
        GROVE
      </p>
      <ul className="m-0 list-none p-0">
        {(["fall", "ppe"] as const).map((c) => (
          <li key={c} className="m-0 p-0">
            <strong>{CAT_NAME[c]}:</strong> score {fixed(img.grove.scores[c], 3)} {img.grove.decisions[c] ? "≥" : "<"} {fixed(th[c], 2)},{" "}
            {img.grove.decisions[c] ? (
              <>
                alert; box from the phrase &ldquo;{img.grove.phrase[c]}&rdquo; ({img.grove.box_source[c]})
              </>
            ) : (
              "no alert"
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Teaser({ base }: { base: string }) {
  const img: GalleryImage = G.images.find((x: GalleryImage) => x.id === G.teaser);
  const [labels, setLabels] = useState(false);
  const reduce = useReducedMotion();
  // Start the handle just left of GROVE's first box, so both its box and the left edges of gemma4:31b's boxes show.
  const firstX = Math.min(...(["fall", "ppe"] as const).flatMap((c) => (img.grove.decisions[c] ? [img.grove.boxes[c][0][0]] : [])), 0.5);
  const start = Math.max(20, Math.min(80, Math.round(firstX * 100) - 2));
  return (
    <figure className="not-prose m-0">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 font-sans text-sm">
        <span className="text-zinc-600 dark:text-zinc-300">Drag the handle or use the arrow keys. Left: <span className="font-mono">gemma4:31b</span>. Right: GROVE.</span>
        <label className="inline-flex items-center gap-2">
          <input type="checkbox" checked={labels} onChange={(e) => setLabels(e.target.checked)} /> Show labeled boxes
        </label>
      </div>
      <ReactCompareSlider
        className="w-full rounded-lg"
        transition={reduce ? undefined : "0.15s ease-out"}
        keyboardIncrement="5%"
        position={start}
        itemOne={<ImageBoxes img={img} base={base} layers={{ labels, gemma: true }} eager />}
        itemTwo={<ImageBoxes img={img} base={base} layers={{ labels, grove: true }} eager />}
      />
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-zinc-200 p-3 dark:border-zinc-700">
          <GemmaPanel img={img} />
        </div>
        <div className="rounded-lg border border-zinc-200 p-3 dark:border-zinc-700">
          <GrovePanel img={img} />
        </div>
      </div>
      <figcaption className="mt-2 font-sans text-sm text-zinc-600 dark:text-zinc-300">
        Selected example (image {img.id}, final set), chosen by the fixed rule described in the gallery. The labels mark{" "}
        {(["fall", "ppe"] as const).filter((c) => img.labels[c]).map((c) => CAT_NAME[c]).join(" and ") || "no violation"}.
      </figcaption>
    </figure>
  );
}
