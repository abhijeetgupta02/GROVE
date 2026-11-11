# POST HOC: single-pass baselines with a confidence score and a fitted threshold

**Post hoc analysis** (D24). Written 2026-11-10T19:40:49 by `code\posthoc_partb.py confidence`, after final scoring. The frozen single-pass prompt and schema with one change, an integer "confidence" from 0 to 100 for each category ("confidence: how sure you are that this violation is present, 0 to 100"; prompt and schema in `freeze\posthoc_confidence_prompt.txt`), were run on the calibration 500 and the final 1,000 for gemma4:31b and qwen3.5:27b (`runs_posthoc\p07_cal`, `runs_posthoc\p07_final`) with the run's code path, options, image encoding, retries and context. Score = confidence / 100 (an invalid response is no prediction). One threshold per category was fit on the calibration 500 with the grid and method of experiment 44 and applied unchanged to the final 1,000. GROVE and the main questions keep their frozen refit thresholds; nothing of GROVE changed.

Thresholds fit on the calibration 500 (`results_posthoc\confidence_thresholds.json`): gemma4:31b Fall 0.96, PPE 0.02; qwen3.5:27b Fall 0.96, PPE 0.02.

## Final 1,000 (thresholds from calibration, applied unchanged)

| System | Micro-F1 [95% interval] | Precision | Recall | F1 Fall / PPE | False alarms per 100 negatives | Completion |
|---|---|---:|---:|---|---:|---:|
| GROVE (d3:27b, refit thresholds) | 0.7021 [0.6699, 0.7329] | 0.6777 | 0.7283 | 0.4398 / 0.7601 | 22.8 | 1.000 |
| main questions (d3:27b, refit thresholds) | 0.7152 [0.6851, 0.7457] | 0.6724 | 0.7638 | 0.4216 / 0.7832 | 25.0 | 1.000 |
| single-pass gemma4:31b, frozen prompt (fixed answers) | 0.6423 [0.6131, 0.6698] | 0.4897 | 0.9331 | 0.4083 / 0.7254 | 71.6 | 1.000 |
| gemma4:31b confidence, fitted thresholds (post hoc) | 0.4154 [0.3912, 0.4397] | 0.2761 | 0.8386 | 0.0408 / 0.5846 | 154.0 | 1.000 |
| gemma4:31b confidence prompt, its own present answers (post hoc, for reference) | 0.6442 [0.6151, 0.6716] | 0.4952 | 0.9213 | 0.4151 / 0.7227 | 68.8 | 1.000 |
| qwen3.5:27b confidence, fitted thresholds (post hoc) | 0.5067 [0.4751, 0.5386] | 0.3660 | 0.8228 | 0.0422 / 0.5846 | 126.8 | 1.000 |
| qwen3.5:27b confidence prompt, its own present answers (post hoc, for reference) | 0.6095 [0.5829, 0.6362] | 0.4549 | 0.9232 | 0.3553 / 0.7165 | 69.2 | 1.000 |

**Paired intervals** (bootstrap, 4000 draws, seed 20260422, near-copy groups):

- GROVE minus gemma4:31b confidence baseline: micro-F1 +0.2867 [+0.2548, +0.3187]; Fall +0.3990 [+0.3094, +0.4895]; PPE +0.1756 [+0.1426, +0.2101]; false alarms per 100 negatives -131.2 [-137.7, -124.6]; valid-only (1000 images) +0.2867 [+0.2548, +0.3187]. Statuses: {'valid': 1000}.
- GROVE minus qwen3.5:27b confidence baseline: micro-F1 +0.1954 [+0.1614, +0.2305]; Fall +0.3976 [+0.2963, +0.4956]; PPE +0.1756 [+0.1426, +0.2101]; false alarms per 100 negatives -104.0 [-110.4, -97.6]; valid-only (1000 images) +0.1954 [+0.1614, +0.2305]. Statuses: {'valid': 1000}.

Average precision (threshold-free, post hoc; GROVE and main questions as in `reports\posthoc_threshold_free.md`):

| Category | GROVE | main questions | gemma4:31b confidence | qwen3.5:27b confidence | GROVE minus gemma4:31b confidence | GROVE minus qwen3.5:27b confidence |
|---|---|---|---|---|---|---|
| Fall | 0.3956 [0.3147, 0.5039] | 0.4239 [0.3321, 0.5282] | 0.0764 [0.0620, 0.0928] | 0.0871 [0.0701, 0.1073] | +0.3193 [+0.2447, +0.4205] | +0.3086 [+0.2362, +0.4083] |
| PPE | 0.8645 [0.8352, 0.8912] | 0.8850 [0.8585, 0.9089] | 0.4235 [0.3875, 0.4600] | 0.4295 [0.3928, 0.4675] | +0.4410 [+0.4063, +0.4752] | +0.4349 [+0.3989, +0.4704] |

Figure: `reports\posthoc_pr_final_with_confidence.png`.

## Calibration 500 (thresholds fit on these images: in-sample, not independent)

| System | Micro-F1 [95% interval] | Precision | Recall | F1 Fall / PPE | False alarms per 100 negatives | Completion |
|---|---|---:|---:|---|---:|---:|
| GROVE (d3:27b, refit thresholds) | 0.7065 [0.6642, 0.7467] | 0.6726 | 0.7441 | 0.4878 / 0.7718 | 20.0 | 1.000 |
| main questions (d3:27b, refit thresholds) | 0.7063 [0.6632, 0.7458] | 0.6512 | 0.7717 | 0.4697 / 0.7801 | 23.2 | 1.000 |
| single-pass gemma4:31b, frozen prompt (fixed answers) | 0.6162 [0.5769, 0.6531] | 0.4649 | 0.9134 | 0.4036 / 0.7057 | 71.6 | 1.000 |
| gemma4:31b confidence, fitted thresholds (post hoc) | 0.4194 [0.3826, 0.4545] | 0.2818 | 0.8189 | 0.0414 / 0.5755 | 152.0 | 1.000 |
| gemma4:31b confidence prompt, its own present answers (post hoc, for reference) | 0.6287 [0.5897, 0.6658] | 0.4793 | 0.9134 | 0.4112 / 0.7176 | 66.8 | 1.000 |
| qwen3.5:27b confidence, fitted thresholds (post hoc) | 0.5012 [0.4545, 0.5455] | 0.3635 | 0.8071 | 0.0517 / 0.5755 | 123.2 | 1.000 |
| qwen3.5:27b confidence prompt, its own present answers (post hoc, for reference) | 0.6072 [0.5699, 0.6421] | 0.4519 | 0.9252 | 0.3401 / 0.7324 | 69.2 | 1.000 |

**Paired intervals** (bootstrap, 4000 draws, seed 20260422, near-copy groups):

- GROVE minus gemma4:31b confidence baseline: micro-F1 +0.2872 [+0.2385, +0.3337]; Fall +0.4464 [+0.3266, +0.5576]; PPE +0.1963 [+0.1460, +0.2464]; false alarms per 100 negatives -132.0 [-141.1, -123.0]; valid-only (500 images) +0.2872 [+0.2385, +0.3337]. Statuses: {'valid': 500}.
- GROVE minus qwen3.5:27b confidence baseline: micro-F1 +0.2053 [+0.1541, +0.2550]; Fall +0.4361 [+0.3002, +0.5574]; PPE +0.1963 [+0.1460, +0.2464]; false alarms per 100 negatives -103.2 [-111.9, -94.8]; valid-only (500 images) +0.2053 [+0.1541, +0.2550]. Statuses: {'valid': 500}.

Average precision (threshold-free, post hoc; GROVE and main questions as in `reports\posthoc_threshold_free.md`):

| Category | GROVE | main questions | gemma4:31b confidence | qwen3.5:27b confidence | GROVE minus gemma4:31b confidence | GROVE minus qwen3.5:27b confidence |
|---|---|---|---|---|---|---|
| Fall | 0.3778 [0.2823, 0.5186] | 0.3602 [0.2655, 0.4959] | 0.0841 [0.0631, 0.1091] | 0.0981 [0.0733, 0.1287] | +0.2937 [+0.2082, +0.4261] | +0.2797 [+0.1948, +0.4098] |
| PPE | 0.8531 [0.8053, 0.8937] | 0.8623 [0.8162, 0.9010] | 0.4026 [0.3535, 0.4551] | 0.4026 [0.3528, 0.4584] | +0.4505 [+0.4011, +0.4993] | +0.4505 [+0.3983, +0.4988] |

Figure: `reports\posthoc_pr_calibration_with_confidence.png`.

Numbers in `results_posthoc\confidence_baseline.json`. The figures add the confidence curves to the threshold-free figures of `reports\posthoc_threshold_free.md` (those figures are unchanged).

