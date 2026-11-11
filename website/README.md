# GROVE project website

Source of the GROVE project page, built with Astro from the saved outputs of the GROVE run. Every number on the page is read
from `src/data/numbers.json`, which `tools/export_site_data.py` wrote from the run's saved files; no number is typed by hand.

Published with GitHub Pages from this repository by `.github/workflows/pages.yml` (repository root), which checks every number against the
results in the repository and then builds and deploys the site. The construction-site images come from ConstructionSite10k and
MOCS (credit and terms on the page).

## Run it

Needs Node.js 22 LTS or later (built here with Node 22.23.4 and npm 10.9.9) and, for the number check, Python 3 (standard
library only).

```bash
npm ci            # exact versions from package-lock.json (or: npm install)
npm run dev       # live preview at http://localhost:4321
npm run build     # data check, type check, then the static site in dist/
npm run preview   # serve dist/ locally
python3 tools/check_numbers.py   # recompute the headline numbers; exits 1 on any difference
```

If `NODE_ENV=production` is set in your shell, npm skips the development packages and the build fails; run `unset NODE_ENV`
first.

What the checks do:

- `npm run build` starts with `tools/check_data.mjs`, which recomputes micro-F1 and false alarms from the per-image scores
  and thresholds in `src/data` (GROVE 0.7021 and 22.8, gemma4:31b 0.6423 and 71.6 on the final 1,000 images), compares them
  and the other summary entries with `numbers.json`, and re-applies the frozen formula to every gallery image. Any difference
  stops the build. The page itself throws at build time if it asks for a number that is not in `numbers.json`.
- `tools/check_numbers.py` does the same recomputation in Python. When the GROVE run folder is present (`C:\GROVE_PC`, or the
  folder named by the `GROVE_PC` environment variable) it also re-reads every entry of `numbers.json` from its source file
  and checks the gallery files. Last run on the lab PC: `ALL CHECKS PASSED: 457 comparisons, 0 differences`.
- `npm run screenshots` saves every section at 1440 and 390 px in light and dark to `screenshots/` and checks the threshold
  explorer (0.702 and 22.8 at the refit thresholds; the post hoc first-freeze values at the first-freeze thresholds).
  `npm run test:a11y` runs axe on the built page. Both need `npx playwright install chromium` once.
- The GitHub workflow (`.github/workflows/astro.yml`) runs `tools/check_numbers.py` and `npm run build` before deploying.

## Where the data comes from

All files in `src/data/` and `public/gallery/` were written by `tools/export_site_data.py`, run once with the GROVE Python
environment against the run folder (read only). Paths below are relative to the run folder.

| File | Contents | Source in the run folder |
| --- | --- | --- |
| `src/data/numbers.json` | Every number on the page (352 entries). Each entry has `value`, `interval` (where there is one), `unit`, `source` (file), `key_path` (where in the file) and `post_hoc`. | `results/e48.json`, `results/e54_final.json`, `results/e15_screening.json`, `results/e16_21.json`, `results/e55_removal_final.json`, `reports/PAPER_TABLES_v2.md`, `results_posthoc/*.json`, `freeze/freeze_2.json`, `freeze/freeze_2.sha256`, `freeze/final_thresholds.json`, `lists/final.json`, `runs/e50/d3_27b__h.config.json`, `logs/pc_setup_report.md` (GPU and Ollama version only), `packet/data/constructionsite10k/upstream_README.md` (dataset citation and license) |
| `src/data/final_scores.json` | Per-image labels, scores and decisions on the 1,000 final images: GROVE, main question, gemma4:31b, signed-confidence scores (post hoc), qwen3.5:27b fixed answers (post hoc), dataset attributes. Scores are rounded to 4 decimals without crossing a multiple of 0.01, so every decision at the page's thresholds is unchanged. | `runs/e50/d3_27b__h.jsonl`, `runs/e51/d3_27b__m.jsonl`, `runs/e52/gemma4_31b__sp.jsonl`, `runs_posthoc/p07_final/*__spc.jsonl`, `runs_posthoc/p06_final/qwen3.5_27b__sp.jsonl`, `tools/cs10k_meta.json`, `lists/final.json` |
| `src/data/calibration_scores.json` | The same for the 500 calibration images (the set the thresholds were fit on; not an independent test). | `runs/e40/d3_27b__h.jsonl`, `runs/e41/d3_27b__m.jsonl`, `runs/e43/gemma4_31b__sp.jsonl`, `runs_posthoc/p07_cal/*__spc.jsonl`, `tools/cs10k_meta.json`, `lists/calibration.json` |
| `src/data/thresholds.json` | Refit, first-freeze, Electrical and signed-confidence thresholds, and how each was fit. | `freeze/final_thresholds.json`, `freeze/freeze_1.json`, `freeze/freeze_2.json`, `results_posthoc/confidence_signed.json` |
| `src/data/gallery.json` | The examples on the page: seven development images we generated with Google Gemini, with labels, boxes, GROVE scores, decisions and boxes, and gemma4:31b answers. Written by `tools/build_dev_gallery.py` from the output of `tools/dev_gallery_scores.py`. | `runs/e12/d3_27b__h.jsonl`, `runs/e11/d3_27b__m.jsonl`, `runs/e09/gemma4_31b__sp.jsonl`, `results/gcache_gdino.jsonl`, `packet/data/grove203/annotations.coco.json` |
| `src/data/errors.json` | Error types of GROVE and gemma4:31b on the final set (post hoc). | `reports/errors_final.md` |
| `public/gallery/` | The seven generated development images, at most 1600 px on the long side, WebP quality 82 with a JPEG fallback, 480 px thumbnails, no metadata, no boxes drawn in. No ConstructionSite10k image is shown. | the development images generated with Google Gemini |
| `public/social-preview.png` | Social preview image (title and headline numbers; no dataset image). | drawn by `tools/social_preview.mjs` from `numbers.json` |

To refresh the data after a change in the run folder, run `python tools/export_site_data.py` with the GROVE environment, then
`python tools/check_numbers.py` and `npm run build`.

### The examples

The page shows only images we own: the development images generated with Google Gemini. Among them, the images where
GROVE is right on Fall, protective equipment and Electrical with the thresholds fit on the 203 development images, and
where each reported category has a GroundingDINO box at IoU 0.5 or more with a labeled box, were picked by looking at
them. These are in-sample examples; the measured results are on the 1,000 final images. Run
`tools/build_dev_gallery.py` after `tools/export_site_data.py`, which still writes the earlier final-set gallery.

## Where things are on the page

- `src/paper.mdx`: the page text, in section order.
- `src/components/site/`: the sections and interactive parts (hero, teaser slider, stat tiles, how it works, threshold
  explorer, results, removal tests, grounding, gallery, failures, reproducibility, citation and credit).
- `src/components/Num.astro`, `src/lib/numbers.ts`: every number is shown through these, by key; hovering a number shows its
  source file.
- Charts use Observable Plot, bundled with the site. No CDN, web font service, tracker or cookie is used.

## Publishing

Every push to `main` runs `.github/workflows/pages.yml`: it installs the packages, runs `tools/check_numbers.py` against the
results in the repository (`GROVE_PC` set to the repository root), builds with the Pages `site` and `base`, and deploys.
Still to add: the paper link in `src/components/site/Hero.astro`. The Zenodo archive is 10.5281/zenodo.24145023.

## Credits and license

The page is based on Roman Hauksson's [academic project page template](https://github.com/RomanHauksson/academic-project-astro-template)
(commit 0e90d4f), originally adapted from Eliahu Horwitz's
[Academic Project Page Template](https://github.com/eliahuhorwitz/Academic-project-page-template), which was adapted from
Keunhong Park's [project page for _Nerfies_](https://nerfies.github.io/). The template is licensed under a
[Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/); the
credit is also in the page footer. The template's own documentation is in `documentation.md`.

The construction-site images and labels come from ConstructionSite10k, whose images come from MOCS; they are used under
CC BY-NC 4.0 and the MOCS terms. The dataset citation is on the page and in `src/data/gallery.json`.
