# GROVE: Grounded Violation Evaluator for Visual Inspection

Abhijeet Gupta, Shruti Singh, Vijayan Asari and Tam V. Nguyen, University of Dayton. Paper under review.

**Project page: https://abhijeetgupta02.github.io/GROVE/**

GROVE asks a decision model sixteen yes/no questions about visible conditions in a construction-site photograph, combines the answer probabilities into scores for fall hazards, electrical hazards and missing protective equipment, applies thresholds calibrated on labeled images from the target source, and grounds each report with an open-vocabulary detector.

This repository holds the website, the run code and every saved output behind the paper's numbers.

## Main result

Frozen evaluation on 1,000 unseen ConstructionSite10k images, scored once (Fall and protective equipment):

| System | Micro-F1 [95% interval] | False alarms per 100 violation-free images |
|---|---|---|
| GROVE (d3:27b, thresholds refit on 500 calibration images) | 0.702 [0.670, 0.733] | 22.8 |
| Same decision model, main questions only | 0.715 [0.685, 0.746] | 25.0 |
| gemma4:31b, single pass (baseline chosen on the calibration images) | 0.642 [0.613, 0.670] | 71.6 |

GROVE minus the baseline: +0.060 [+0.030, +0.091]. The gain comes from calibrated probability scores, not from the added questions. Intervals: paired bootstrap by near-copy group, 4,000 draws.

## Contents

| Folder | Contents |
|---|---|
| `website/` | Source of the project page (Astro). `website/tools/check_numbers.py` checks every number on the page against the files below |
| `code/` | Run code: model calls, scoring, thresholds, bootstrap, grounding, post hoc analyses (`grove_score.py` holds the metrics) |
| `freeze/` | Frozen settings: selected models and digests, thresholds, prompts, Python packages, SHA-256 of each freeze |
| `lists/` | Identifiers of the 500 calibration and 1,000 final ConstructionSite10k images, drawn before any model ran |
| `packet/` | Question sets and prompts (`prompts/prompts.json`), category mapping, development annotations and inter-annotator records (`data/grove203/`) |
| `runs/`, `runs_posthoc/` | Every saved model response, one JSON line per image and attempt |
| `results/`, `results_posthoc/` | Scores and intervals at full precision; `results_posthoc/` holds the analyses made after final scoring |
| `reports/` | Readable report of each experiment; `PAPER_TABLES_v2.md` gathers the tables |
| `paper_figures/` | Script and file of the paper's Figure 4 |

Where each table of the paper comes from:

| Paper | Source |
|---|---|
| Table 3 (screening, 203 development images) | `results/e15_screening.json` |
| Table 4 (main comparison) | `results/e15_screening.json`, `results/e48.json`, `results/e54_final.json`, `results_posthoc/second_baseline.json`, `results_posthoc/first_freeze_scores.json` |
| Table 5 (per category) | `results/e54_final.json`, `results/e57_59.json` |
| Table 6 (removing one part at a time) | `results/e16_21.json`, `results/e55_removal_final.json` |
| Table 7 (confidence baselines, post hoc) | `results_posthoc/confidence_baseline.json`, `results_posthoc/confidence_signed.json` |
| Table 8 (evidence grounding) | `results/e31_38.json`, `results/e45.json`, `results/e54_final.json` |
| Table 9 (speed and memory) | `results/e56_speed.json`, `results/gpu_peaks.json` |

## Checking the numbers

```bash
cd website
GROVE_PC=.. python3 tools/check_numbers.py
```

This recomputes the headline numbers from the per-image scores and re-reads every number on the project page from its source file in this repository (standard library only).

## Running the code

The code ran on Windows with Python 3.11, Ollama 0.40.14 and one RTX A6000 (48 GB); package versions are in `freeze/pip_freeze.txt` and the model digests in `freeze/freeze_2.json`. It reads its folder from `G` in `code/grove_common.py` (set to `C:\GROVE_PC` in the run) and expects the ConstructionSite10k parquet files under `packet/data/constructionsite10k/`.

## Data

ConstructionSite10k (https://huggingface.co/datasets/LouisChen15/ConstructionSite) is available under CC BY-NC 4.0 after its access conditions are accepted. Its images come from MOCS, whose terms do not allow redistribution, so this repository gives the identifiers of the calibration and final images, not the images. The photographs on the project page are development images we generated with Google Gemini.

## Citation

```bibtex
@article{gupta_grove,
  title  = {GROVE: Grounded Violation Evaluator for Visual Inspection},
  author = {Gupta, Abhijeet and Singh, Shruti and Asari, Vijayan and Nguyen, Tam V.},
  note   = {Under review}
}
```

## License

Code (`code/`, `website/`, `paper_figures/`): MIT. Annotations, saved outputs, scores and reports: CC BY 4.0. The generated images on the project page: CC BY 4.0. See `LICENSE`.
