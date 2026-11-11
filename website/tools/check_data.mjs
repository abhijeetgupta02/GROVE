// Runs before every build (npm run build). Recomputes the headline numbers from the per-image data and stops the
// build if anything differs from src/data/numbers.json or from the values fixed for the page.
// tools/check_numbers.py does the same and also compares every entry with its source in the run folder.
import { readFileSync } from "node:fs";
const load = (n) => JSON.parse(readFileSync(new URL(`../src/data/${n}`, import.meta.url), "utf8"));
const NUM = load("numbers.json").numbers, TH = load("thresholds.json"), G = load("gallery.json");
const bad = [];
let ok = 0;
const check = (name, got, want, tol = 1e-9) => {
  if (typeof got === "number" && typeof want === "number" ? Math.abs(got - want) <= tol : JSON.stringify(got) === JSON.stringify(want)) ok++;
  else bad.push(`${name}: got ${JSON.stringify(got)}, expected ${JSON.stringify(want)}`);
};
const ge = (x, t) => x !== null && x !== undefined && x >= t;
function metrics(rows, pred) {
  let tp = 0, fp = 0, fn = 0, fa = 0, neg = 0;
  for (const r of rows) {
    const y = [r.y_fall === 1, r.y_ppe === 1], p = pred(r), isNeg = !y[0] && !y[1];
    if (isNeg) neg++;
    for (let j = 0; j < 2; j++) {
      if (p[j] && y[j]) tp++;
      if (p[j] && !y[j]) { fp++; if (isNeg) fa++; }
      if (!p[j] && y[j]) fn++;
    }
  }
  return { micro_f1: (2 * tp) / Math.max(2 * tp + fp + fn, 1e-9), false_alarms: (100 * fa) / Math.max(neg, 1) };
}
const RF = TH.refit.GROVE, FF = TH.first_freeze.GROVE, MQ = TH.refit.main_question, SG = TH.signed_confidence;
for (const [setk, file] of [["final", "final_scores.json"], ["cal", "calibration_scores.json"]]) {
  const rows = load(file).rows;
  check(`${setk} rows`, rows.length, NUM[`${setk}.n_images`].value);
  const sys = {
    grove: (r) => [ge(r.grove_fall, RF.fall), ge(r.grove_ppe, RF.ppe)],
    main: (r) => [ge(r.main_fall, MQ.fall), ge(r.main_ppe, MQ.ppe)],
    gemma: (r) => [r.gemma_fall === 1, r.gemma_ppe === 1],
    "signed.gemma": (r) => [ge(r.gemma_signed_fall, SG.gemma.fall), ge(r.gemma_signed_ppe, SG.gemma.ppe)],
    "signed.qwen": (r) => [ge(r.qwen_signed_fall, SG.qwen.fall), ge(r.qwen_signed_ppe, SG.qwen.ppe)],
  };
  if (setk === "final") {
    sys.qwen = (r) => [r.qwen_fall === 1, r.qwen_ppe === 1];
    sys.first_freeze_grove = (r) => [ge(r.grove_fall, FF.fall), ge(r.grove_ppe, FF.ppe)];
  }
  for (const [k, f] of Object.entries(sys)) {
    const m = metrics(rows, f);
    for (const q of ["micro_f1", "false_alarms"]) if (NUM[`${setk}.${k}.${q}`]) check(`${setk}.${k}.${q}`, m[q], NUM[`${setk}.${k}.${q}`].value);
  }
  if (setk === "final") {
    const g = metrics(rows, sys.grove), b = metrics(rows, sys.gemma);
    check("GROVE final micro-F1 (4 decimals)", g.micro_f1.toFixed(4), "0.7021");
    check("GROVE final false alarms (1 decimal)", g.false_alarms.toFixed(1), "22.8");
    check("gemma4:31b final micro-F1 (4 decimals)", b.micro_f1.toFixed(4), "0.6423");
    check("gemma4:31b final false alarms (1 decimal)", b.false_alarms.toFixed(1), "71.6");
  }
}
// the formula shown in "How it works" reproduces each gallery image's stored score
const w = G.weights;
for (const im of G.images) {
  const p = im.grove.probs;
  const fall = w.fall_mix * (p.Fall_Hazard + Math.max(p.f_fall_edge, p.f_fall_opening)) * (1 - w.fall_protection * p.ok_fall_protected);
  const ppe = w.ppe_mix * (p.PPE_Violation + p.f_worker * Math.max(p.f_ppe_nohat, p.f_ppe_novest, p.f_ppe_noeye_glove));
  check(`formula fall ${im.id}`, fall, im.grove.scores.fall, 5e-4);
  check(`formula ppe ${im.id}`, ppe, im.grove.scores.ppe, 5e-4);
}
if (bad.length) {
  console.error(`check_data: FAILED, ${bad.length} differences`);
  for (const b of bad) console.error("  " + b);
  process.exit(1);
}
console.log(`check_data: ${ok} checks passed`);
