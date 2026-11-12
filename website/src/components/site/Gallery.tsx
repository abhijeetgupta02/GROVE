import { useMemo, useState } from "react";
import {
  IMAGES,
  G,
  Card,
  Lightbox,
  LayerToggles,
  catsOf,
} from "./GalleryParts";
import type { GalleryImage, Layers } from "./ImageBoxes";

export default function Gallery({ base }: { base: string }) {
  const [cat, setCat] = useState("all");
  const [outcome, setOutcome] = useState("all");
  const [disagree, setDisagree] = useState(false);
  const [layers, setLayers] = useState<Layers>({
    labels: true,
    grove: true,
    gemma: false,
  });
  const [open, setOpen] = useState<number | null>(null);
  const list = useMemo(
    () =>
      IMAGES.filter((img: GalleryImage) => {
        if (cat === "none" && catsOf(img).length) return false;
        if (cat !== "all" && cat !== "none" && !catsOf(img).includes(cat))
          return false;
        if (outcome === "right" && img.role !== "success") return false;
        if (outcome === "fails" && img.role !== "failure") return false;
        if (disagree && !img.outcome.disagree) return false;
        return true;
      }),
    [cat, outcome, disagree],
  );
  const nSucc = IMAGES.filter((x: GalleryImage) => x.role === "success").length;
  const nFail = IMAGES.length - nSucc;
  return (
    <div className="gallery-explorer not-prose font-sans">
      <details className="mb-3 text-sm">
        <summary className="cursor-pointer font-semibold">
          How the examples were chosen (
          {nFail
            ? `${nSucc} correct examples, ${nFail} limitations`
            : `${nSucc} examples`}
          )
        </summary>
        <p className="mt-1">{G.selection_rule}</p>
      </details>
      <div className="gallery-toolbar mb-2 flex flex-wrap items-end gap-3 text-sm">
        <label className="flex flex-col">
          <span>Category</span>
          <select
            value={cat}
            onChange={(e) => {
              setCat(e.target.value);
              setOpen(null);
            }}
            className="rounded-md border-zinc-300 py-1 text-sm dark:border-zinc-600 dark:bg-zinc-800"
          >
            <option value="all">All</option>
            <option value="fall">Fall</option>
            <option value="ppe">Protective equipment</option>
            <option value="none">No violation, no alert</option>
          </select>
        </label>
        <label className="flex flex-col">
          <span>Outcome</span>
          <select
            value={outcome}
            onChange={(e) => {
              setOutcome(e.target.value);
              setOpen(null);
            }}
            className="rounded-md border-zinc-300 py-1 text-sm dark:border-zinc-600 dark:bg-zinc-800"
          >
            <option value="all">All</option>
            <option value="right">Correct examples</option>
            <option value="fails">Limitations</option>
          </select>
        </label>
        <label className="inline-flex items-center gap-1.5 pb-1">
          <input
            type="checkbox"
            checked={disagree}
            onChange={(e) => {
              setDisagree(e.target.checked);
              setOpen(null);
            }}
          />{" "}
          GROVE and <span className="font-mono">gemma4:31b</span> disagree
        </label>
      </div>
      <LayerToggles layers={layers} setLayers={setLayers} />
      <p className="m-0 mt-1 text-xs text-zinc-600 dark:text-zinc-300">
        {G.box_note}
      </p>
      <p className="m-0 mt-2 text-sm" aria-live="polite">
        {list.length} of {IMAGES.length} selected examples shown.
      </p>
      <ul className="gallery-grid m-0 mt-2 grid list-none grid-cols-1 gap-5 p-0 sm:grid-cols-2 lg:grid-cols-3">
        {list.map((img: GalleryImage, k: number) => (
          <Card
            key={img.id}
            img={img}
            base={base}
            layers={layers}
            onOpen={() => setOpen(k)}
          />
        ))}
      </ul>
      {list.length === 0 && (
        <div className="gallery-empty">
          <p>No examples match these filters.</p>
          <button
            type="button"
            onClick={() => {
              setCat("all");
              setOutcome("all");
              setDisagree(false);
            }}
          >
            Show all examples
          </button>
        </div>
      )}
      <Lightbox
        list={list}
        index={open}
        setIndex={setOpen}
        base={base}
        layers={layers}
      />
    </div>
  );
}
