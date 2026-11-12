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
        <span
          className="mr-1 inline-block h-3 w-3 rounded-sm align-middle"
          style={{ background: COLORS.gemma }}
          aria-hidden="true"
        />
        <span className="font-mono">gemma4:31b</span>, single pass
      </p>
      <ul className="m-0 list-none p-0">
        {(["fall", "ppe"] as const).map((c) => (
          <li key={c} className="m-0 p-0">
            <strong>{CAT_NAME[c]}:</strong>{" "}
            {img.gemma.decisions[c] ? "alert" : "no alert"}
            {img.gemma.decisions[c] && img.gemma.evidence[c] ? (
              <> &ldquo;{img.gemma.evidence[c]}&rdquo;</>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
function GrovePanel({ img }: { img: GalleryImage }) {
  const th = G.thresholds ?? G.thresholds_refit;
  return (
    <div className="font-sans text-sm leading-snug">
      <p className="m-0 font-semibold">
        <span
          className="mr-1 inline-block h-3 w-3 rounded-sm align-middle"
          style={{ background: COLORS.grove }}
          aria-hidden="true"
        />
        GROVE
      </p>
      <ul className="m-0 list-none p-0">
        {(["fall", "ppe"] as const).map((c) => (
          <li key={c} className="m-0 p-0">
            <strong>{CAT_NAME[c]}:</strong> score{" "}
            {fixed(img.grove.scores[c], 3)} {img.grove.decisions[c] ? "≥" : "<"}{" "}
            {fixed(th[c], 2)},{" "}
            {img.grove.decisions[c] ? (
              <>
                alert; box from the phrase &ldquo;{img.grove.phrase[c]}&rdquo; (
                {img.grove.box_source[c]})
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
  const [selected, setSelected] = useState<string>(G.teaser);
  const img: GalleryImage = G.images.find(
    (x: GalleryImage) => x.id === selected,
  );
  const featured: GalleryImage[] = (G.featured ?? [G.teaser]).map(
    (id: string) => G.images.find((x: GalleryImage) => x.id === id),
  );
  const [labels, setLabels] = useState(false);
  const reduce = useReducedMotion();
  // Start the handle just left of GROVE's first box, so both its box and the left edges of gemma4:31b's boxes show.
  const firstX = Math.min(
    ...(["fall", "ppe"] as const).flatMap((c) =>
      img.grove.decisions[c] ? [img.grove.boxes[c][0][0]] : [],
    ),
    0.5,
  );
  const start = Math.max(20, Math.min(80, Math.round(firstX * 100) - 2));
  return (
    <figure className="comparison-showcase not-prose m-0">
      <div
        className="scene-selector"
        role="group"
        aria-label="Featured comparison scenes"
      >
        <span className="scene-selector-label">CHOOSE A SCENE</span>
        <div className="scene-options">
          {featured.map((scene) => (
            <button
              type="button"
              key={scene.id}
              aria-pressed={selected === scene.id}
              onClick={() => setSelected(scene.id)}
            >
              <img
                src={base + scene.files.thumb_webp}
                alt=""
                width={40}
                height={40}
              />
              <span>{scene.title ?? `Scene ${scene.id}`}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="comparison-layout">
        <div className="comparison-stage">
          <div className="comparison-stage-top">
            <span>
              <i style={{ background: COLORS.gemma }} /> Single pass
            </span>
            <span>
              GROVE <i style={{ background: COLORS.grove }} />
            </span>
          </div>
          <ReactCompareSlider
            key={selected}
            className="comparison-slider w-full"
            transition={reduce ? undefined : "0.15s ease-out"}
            keyboardIncrement="5%"
            position={start}
            itemOne={
              <ImageBoxes
                img={img}
                base={base}
                layers={{ labels, gemma: true }}
                eager
              />
            }
            itemTwo={
              <ImageBoxes
                img={img}
                base={base}
                layers={{ labels, grove: true }}
                eager
              />
            }
          />
          <div className="comparison-instruction">
            <span aria-hidden="true">↔</span> Drag to compare · Arrow keys also
            work
          </div>
        </div>
        <aside
          className="comparison-notes"
          aria-label="Saved model outputs"
          aria-live="polite"
        >
          <p className="eyebrow">DEVELOPMENT SCENE {img.id}</p>
          <h3>{img.title ?? "Inspect the evidence"}</h3>
          <p className="comparison-note">
            Same image. Saved model outputs.
            <br />
            See the decision and its evidence together.
          </p>
          <div className="output-panel output-baseline">
            <GemmaPanel img={img} />
          </div>
          <div className="output-panel output-grove">
            <GrovePanel img={img} />
          </div>
          <label className="labels-toggle">
            <input
              type="checkbox"
              checked={labels}
              onChange={(e) => setLabels(e.target.checked)}
            />{" "}
            Show annotated boxes
          </label>
          <a className="text-link" href="#gallery">
            Inspect all examples <span aria-hidden="true">↗</span>
          </a>
        </aside>
      </div>
      <figcaption className="comparison-caption">
        Google Gemini development image · In-sample illustration using
        development thresholds (Fall 0.12, PPE 0.50). Final-set results are
        reported separately below.
      </figcaption>
    </figure>
  );
}
