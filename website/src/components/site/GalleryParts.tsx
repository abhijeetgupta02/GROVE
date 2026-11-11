import { useEffect, useRef } from "react";
import gallery from "../../data/gallery.json";
import { ImageBoxes, type GalleryImage, type Layers } from "./ImageBoxes";
import { CAT_NAME, COLORS, fixed } from "../../lib/format";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const G = gallery as any;
export const IMAGES: GalleryImage[] = G.images;
const CATS = ["fall", "ppe"] as const;

/** Categories that are labeled or flagged by GROVE on this image. */
export function catsOf(img: GalleryImage): string[] {
  return CATS.filter((c) => img.labels[c] || img.grove.decisions[c]);
}
export function outcomeText(img: GalleryImage): string {
  return img.role === "success" ? "GROVE right" : `GROVE fails: ${img.failure_type}`;
}
function Chip({ children, tone }: { children: React.ReactNode; tone: "ok" | "bad" | "info" }) {
  const cls = tone === "ok" ? "bg-emerald-100 text-emerald-950" : tone === "bad" ? "bg-rose-100 text-rose-950" : "bg-zinc-200 text-zinc-900";
  return <span className={`rounded px-1.5 py-0.5 text-[11px] font-semibold ${cls}`}>{children}</span>;
}

export function Card({ img, base, layers, onOpen, sentence }: { img: GalleryImage; base: string; layers: Layers; onOpen: () => void; sentence?: string }) {
  return (
    <li className="m-0 list-none p-0">
      <button type="button" onClick={onOpen} className="group block w-full overflow-hidden rounded-lg border border-zinc-200 text-left hover:border-zinc-400 focus-visible:outline-2 focus-visible:outline-blue-700 dark:border-zinc-700"
        aria-haspopup="dialog">
        <ImageBoxes img={img} base={base} layers={layers} thumb />
        <span className="flex flex-wrap items-center gap-1 p-2">
          <span className="font-mono text-xs">{img.id}</span>
          <Chip tone={img.role === "success" ? "ok" : "bad"}>{img.role === "success" ? "GROVE right" : "GROVE fails"}</Chip>
          {img.outcome.gemma_wrong && <Chip tone="info">gemma4:31b wrong</Chip>}
          <span className="w-full text-[11px]">Labels: {CATS.filter((c) => img.labels[c]).map((c) => CAT_NAME[c]).join(", ") || "no violation"}</span>
          <span className="w-full text-[11px] text-zinc-600 dark:text-zinc-300">{img.illumination}, {img.camera_distance}</span>
          {sentence && <span className="w-full text-sm leading-snug">{sentence}</span>}
        </span>
      </button>
    </li>
  );
}

function ScoreBar({ label, score, th, flagged }: { label: string; score: number; th: number; flagged: boolean }) {
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs"><span>{label}</span><span className="font-mono">{fixed(score, 3)} {flagged ? "≥" : "<"} {fixed(th, 2)} {flagged ? "alert" : "no alert"}</span></div>
      <div className="relative h-3 rounded-sm bg-zinc-200 dark:bg-zinc-700" aria-hidden="true">
        <span className="absolute top-0 left-0 h-3 rounded-sm" style={{ width: `${score * 100}%`, background: COLORS.grove }} />
        <span className="absolute -top-0.5 h-4 w-0.5 bg-zinc-900 dark:bg-zinc-100" style={{ left: `${th * 100}%` }} />
      </div>
    </div>
  );
}

export function Detail({ img }: { img: GalleryImage }) {
  const th = G.thresholds_refit;
  return (
    <div className="text-sm leading-snug">
      <p className="m-0 mb-2 text-xs text-zinc-600 dark:text-zinc-300">Image {img.id}, final set. {img.illumination}, {img.camera_distance}. Why selected: {img.draw_reason}.</p>
      <h4 className="m-0 mb-1 font-semibold">Labels</h4>
      <ul className="m-0 mb-2 list-disc pl-5">
        {CATS.map((c) => (
          <li key={c}>{CAT_NAME[c]}: {img.labels[c] ? "violation" : "no violation"}{img.labels[c] && img.label_reason[c] ? <> (dataset reason: &ldquo;{img.label_reason[c]}&rdquo;)</> : null}</li>
        ))}
      </ul>
      <h4 className="m-0 mb-1 font-semibold">GROVE scores against the thresholds</h4>
      {CATS.map((c) => <ScoreBar key={c} label={CAT_NAME[c]} score={img.grove.scores[c]} th={th[c]} flagged={img.grove.decisions[c]} />)}
      {CATS.filter((c) => img.grove.decisions[c]).map((c) => (
        <p key={c} className="m-0 mb-1">{CAT_NAME[c]}: phrase &ldquo;{img.grove.phrase[c]}&rdquo;, box from {img.grove.box_source[c]}, IoU with the labeled box {fixed(img.grove.top_iou[c] ?? 0, 2)}.</p>
      ))}
      <h4 className="m-0 mt-2 mb-1 font-semibold"><span className="font-mono">gemma4:31b</span> (single pass)</h4>
      <ul className="m-0 mb-2 list-disc pl-5">
        {CATS.map((c) => (
          <li key={c}>{CAT_NAME[c]}: {img.gemma.decisions[c] ? "alert" : "no alert"}{img.gemma.evidence[c] ? <> &ldquo;{img.gemma.evidence[c]}&rdquo;</> : null}
            {img.gemma.decisions[c] && img.gemma.box_as_written[c] ? <span className="text-xs"> Box as written: <span className="font-mono">[{(img.gemma.box_as_written[c] as number[]).join(", ")}]</span>{img.gemma.fits_pixel_rule[c] ? "" : " (does not fit the pixel rule)"}{img.gemma.fits_grid_reading[c] ? "; also fits a 0–1000 grid reading" : ""}.</span> : null}
          </li>
        ))}
      </ul>
      <details>
        <summary className="cursor-pointer font-semibold">GROVE question probabilities</summary>
        <div className="mt-1 flex flex-col gap-0.5">
          {Object.keys(G.questions).map((k) => (
            <div key={k} className="grid grid-cols-[minmax(7rem,11rem)_1fr_2.5rem] items-center gap-2" title={G.questions[k]}>
              <span className="truncate font-mono text-[11px]">{k}</span>
              <span className="h-2 rounded-sm bg-zinc-200 dark:bg-zinc-700" aria-hidden="true"><span className="block h-2 rounded-sm" style={{ width: `${img.grove.probs[k] * 100}%`, background: COLORS.grove }} /></span>
              <span className="text-right font-mono text-[11px]">{fixed(img.grove.probs[k], 2)}</span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}

export function Lightbox({ list, index, setIndex, base, layers }: { list: GalleryImage[]; index: number | null; setIndex: (i: number | null) => void; base: string; layers: Layers }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (index !== null && !d.open) d.showModal();
    if (index === null && d.open) d.close();
  }, [index]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (index === null) return;
      if (e.key === "ArrowRight") setIndex((index + 1) % list.length);
      if (e.key === "ArrowLeft") setIndex((index - 1 + list.length) % list.length);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [index, list.length, setIndex]);
  const img = index !== null ? list[index] : null;
  return (
    <dialog ref={ref} onClose={() => setIndex(null)} aria-label={img ? `Image ${img.id}` : "Image"}
      className="m-auto max-h-[95svh] w-[min(1200px,96vw)] max-w-none overflow-y-auto rounded-xl bg-white p-0 text-zinc-900 backdrop:bg-black/70 dark:bg-zinc-900 dark:text-zinc-100">
      {img && (
        <div className="p-3 md:p-4">
          <div className="mb-2 flex items-center justify-between gap-2">
            <p className="m-0 text-sm font-semibold">{outcomeText(img)} <span className="font-normal text-zinc-600 dark:text-zinc-300">(selected example {index! + 1} of {list.length})</span></p>
            <div className="flex gap-1">
              <button type="button" className="rounded-md border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-600" onClick={() => setIndex((index! - 1 + list.length) % list.length)} aria-label="Previous image">&larr;</button>
              <button type="button" className="rounded-md border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-600" onClick={() => setIndex((index! + 1) % list.length)} aria-label="Next image">&rarr;</button>
              <button type="button" className="rounded-md border border-zinc-300 px-2 py-1 text-sm dark:border-zinc-600" onClick={() => setIndex(null)} aria-label="Close">Close</button>
            </div>
          </div>
          <div className="grid gap-4 lg:grid-cols-[3fr_2fr]">
            <ImageBoxes img={img} base={base} layers={layers} />
            <Detail img={img} />
          </div>
        </div>
      )}
    </dialog>
  );
}

export function LayerToggles({ layers, setLayers }: { layers: Layers; setLayers: (l: Layers) => void }) {
  const items: [keyof Layers, string, string][] = [
    ["labels", "Labeled boxes", COLORS.label],
    ["grove", "GROVE evidence box", COLORS.grove],
    ["groveAll", "GROVE up to 5 boxes", COLORS.grove],
    ["gemma", "gemma4:31b box as written", COLORS.gemma],
  ];
  return (
    <fieldset className="m-0 flex flex-wrap gap-x-4 gap-y-1 border-0 p-0 text-sm">
      <legend className="sr-only">Overlays</legend>
      {items.map(([k, l, c]) => (
        <label key={k} className="inline-flex items-center gap-1.5">
          <input type="checkbox" checked={!!layers[k]} onChange={(e) => setLayers({ ...layers, [k]: e.target.checked })} />
          <span className="inline-block h-3 w-3 rounded-sm border border-zinc-500" style={{ background: c }} aria-hidden="true" /> {l}
        </label>
      ))}
    </fieldset>
  );
}
