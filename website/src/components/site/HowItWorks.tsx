import { useState } from "react";
import gallery from "../../data/gallery.json";
import { ImageBoxes, type GalleryImage } from "./ImageBoxes";
import { CAT_NAME, COLORS, fixed } from "../../lib/format";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const G = gallery as any;
const USED: Record<string, string[]> = {
  fall: ["Fall_Hazard", "f_fall_edge", "f_fall_opening", "ok_fall_protected"],
  ppe: ["PPE_Violation", "f_worker", "f_ppe_nohat", "f_ppe_novest", "f_ppe_noeye_glove"],
};
const STEPS = ["Photo", "Questions", "Formula", "Threshold", "Phrase", "Evidence box"];

function Bar({ value, color, label, title, strong }: { value: number; color: string; label: string; title: string; strong: boolean }) {
  return (
    <div className="grid grid-cols-[minmax(8rem,12rem)_1fr_3rem] items-center gap-2" title={title}>
      <span className={`truncate font-mono text-xs ${strong ? "font-bold" : "opacity-70"}`}>{label}</span>
      <span className="h-3 rounded-sm bg-zinc-200 dark:bg-zinc-700" aria-hidden="true">
        <span className="block h-3 rounded-sm" style={{ width: `${Math.round(value * 100)}%`, background: strong ? color : "#9ca3af" }} />
      </span>
      <span className="text-right font-mono text-xs">{fixed(value, 2)}</span>
    </div>
  );
}

export default function HowItWorks({ base }: { base: string }) {
  const img: GalleryImage = G.images.find((x: GalleryImage) => x.id === G.teaser);
  const [step, setStep] = useState(0);
  const [cat, setCat] = useState<"fall" | "ppe">("fall");
  const p = img.grove.probs as Record<string, number>;
  const w = G.weights;
  const th = G.thresholds_refit[cat];
  const score = img.grove.scores[cat];
  const flagged = img.grove.decisions[cat];
  const nQ = Object.keys(G.questions).length;
  let formula: React.ReactNode;
  if (cat === "fall") {
    const side = Math.max(p.f_fall_edge, p.f_fall_opening);
    const v = w.fall_mix * (p.Fall_Hazard + side) * (1 - w.fall_protection * p.ok_fall_protected);
    formula = (
      <>
        <p className="m-0 font-mono text-xs break-words">{G.formula.fall}</p>
        <p className="m-0 mt-2 font-mono text-sm break-words">
          = {fixed(w.fall_mix, 2)} &times; ({fixed(p.Fall_Hazard, 3)} + max({fixed(p.f_fall_edge, 3)}, {fixed(p.f_fall_opening, 3)})) &times; (1 &minus; {fixed(w.fall_protection, 2)} &times; {fixed(p.ok_fall_protected, 3)}) = <strong>{fixed(v, 3)}</strong>
        </p>
      </>
    );
  } else {
    const side = p.f_worker * Math.max(p.f_ppe_nohat, p.f_ppe_novest, p.f_ppe_noeye_glove);
    const v = w.ppe_mix * (p.PPE_Violation + side);
    formula = (
      <>
        <p className="m-0 font-mono text-xs break-words">{G.formula.ppe}</p>
        <p className="m-0 mt-2 font-mono text-sm break-words">
          = {fixed(w.ppe_mix, 2)} &times; ({fixed(p.PPE_Violation, 3)} + {fixed(p.f_worker, 3)} &times; max({fixed(p.f_ppe_nohat, 3)}, {fixed(p.f_ppe_novest, 3)}, {fixed(p.f_ppe_noeye_glove, 3)})) = <strong>{fixed(v, 3)}</strong>
        </p>
      </>
    );
  }
  return (
    <div className="not-prose font-sans">
      <div className="mb-3 flex flex-wrap items-center gap-2" role="group" aria-label="Category">
        <span className="text-sm">Category:</span>
        {(["fall", "ppe"] as const).map((c) => (
          <button key={c} type="button" aria-pressed={cat === c} onClick={() => setCat(c)}
            className={`rounded-full border px-3 py-1 text-sm ${cat === c ? "border-blue-700 bg-blue-700 text-white" : "border-zinc-300 dark:border-zinc-600"}`}>
            {CAT_NAME[c]}
          </button>
        ))}
      </div>
      <ol className="m-0 mb-3 flex list-none flex-wrap gap-2 p-0" aria-label="Steps">
        {STEPS.map((s, k) => (
          <li key={s} className="m-0 p-0">
            <button type="button" aria-current={step === k ? "step" : undefined} onClick={() => setStep(k)}
              className={`rounded-md border px-3 py-1 text-sm ${step === k ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900" : "border-zinc-300 dark:border-zinc-600"}`}>
              {k + 1}. {s}
            </button>
          </li>
        ))}
      </ol>
      <div className="grid gap-4 md:grid-cols-2">
        <ImageBoxes img={img} base={base} layers={{ grove: step === 5 }} cats={[cat]} />
        <div className="text-sm leading-relaxed" aria-live="polite">
          {step === 0 && (
            <>
              <p className="m-0">The photo and a fixed scene description go to the decision model (<span className="font-mono">d3:27b</span>):</p>
              <blockquote className="m-0 mt-2 border-l-4 border-zinc-300 pl-3 italic dark:border-zinc-600">{G.state}</blockquote>
            </>
          )}
          {step === 1 && (
            <>
              <p className="m-0 mb-2">The model answers {nQ} yes/no questions with a probability each. Bold: the questions used for {CAT_NAME[cat]}.</p>
              <div className="flex flex-col gap-1">
                {Object.keys(G.questions).map((k) => (
                  <Bar key={k} value={p[k]} color={COLORS.grove} label={k} title={G.questions[k]} strong={USED[cat].includes(k)} />
                ))}
              </div>
            </>
          )}
          {step === 2 && (
            <>
              <p className="m-0 mb-2">A fixed formula (weights frozen before any test image was scored) turns the answers into one score:</p>
              {formula}
            </>
          )}
          {step === 3 && (
            <>
              <p className="m-0 mb-2">The score is compared with the category threshold, fit once on the calibration images:</p>
              <div className="relative mt-4 h-4 rounded-sm bg-zinc-200 dark:bg-zinc-700" role="img" aria-label={`Score ${fixed(score, 3)}, threshold ${fixed(th, 2)}`}>
                <span className="absolute top-0 left-0 h-4 rounded-sm" style={{ width: `${score * 100}%`, background: COLORS.grove }} />
                <span className="absolute -top-1 h-6 w-0.5 bg-zinc-900 dark:bg-zinc-100" style={{ left: `${th * 100}%` }} />
              </div>
              <p className="m-0 mt-2">
                Score <strong>{fixed(score, 3)}</strong> {flagged ? "≥" : "<"} threshold <strong>{fixed(th, 2)}</strong>: {flagged ? "GROVE raises an alert." : "no alert."}
              </p>
            </>
          )}
          {step === 4 && (
            <p className="m-0">
              {flagged ? (
                <>For an alert, a fixed phrase for the category is sent to the box finder: <strong>&ldquo;{img.grove.phrase[cat]}&rdquo;</strong>.</>
              ) : (
                <>No alert for {CAT_NAME[cat]} on this image, so no phrase is used.</>
              )}
            </p>
          )}
          {step === 5 && (
            <p className="m-0">
              {flagged ? (
                <>The evidence box (blue) comes from {img.grove.box_source[cat]} for that phrase. Its overlap with the labeled box: IoU {fixed(img.grove.top_iou[cat], 2)}.</>
              ) : (
                <>No alert, so no evidence box.</>
              )}
            </p>
          )}
        </div>
      </div>
      <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">Selected example (image {img.id}, final set), chosen by the fixed rule described in the gallery.</p>
    </div>
  );
}
