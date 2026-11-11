# POST HOC: confidence baselines checked and rescored with a signed score

**Post hoc analysis, twice over** (D29). Written 2026-11-11T08:12:54 by `code\posthoc_signed.py`. No model was called. The confidence baselines of `reports\posthoc_confidence_baseline.md` (D24, Part B) used score = confidence / 100. After that first scoring, the saved answers showed that the models' confidence describes how sure they are of their own answer, not how likely the violation is (part 1). This report redefines the score **after seeing the first scoring and the diagnostic**: s = confidence / 100 when present = true and s = 1 - confidence / 100 when present = false (an invalid response is no prediction). Every new row is labelled "signed confidence (post hoc; score redefined after the first scoring)". The original confidence / 100 rows are recomputed from the saved files and thresholds and are identical to `results_posthoc\confidence_baseline.json` (checked); they are kept unchanged. GROVE, its thresholds, the baseline choice and every frozen result are unchanged; nothing in runs, runs_posthoc, freeze, lists, results or the existing reports changed.

Inputs: `runs_posthoc\p07_cal` and `runs_posthoc\p07_final` (gemma4:31b and qwen3.5:27b, confidence prompt in `freeze\posthoc_confidence_prompt.txt`); labels, near-copy groups, GROVE and main-question scores and the single-pass gemma4:31b answers exactly as `code\posthoc_partb.py` builds them (its functions are imported).

## 1. Diagnostic: confidence by answer and by label

Valid responses only (all gemma4:31b calibration 500, gemma4:31b final 1000, qwen3.5:27b calibration 500, qwen3.5:27b final 1000). Confidence is the saved integer 0-100. Quartiles: numpy linear interpolation.

### By the model's answer

| Model | Set | Category | Answer present: n | mean | median | quartiles | Answer absent: n | mean | median | quartiles | Answer absent with confidence >= 50 |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---|---:|
| gemma4:31b | calibration | Fall | 162 | 92.3 | 90.0 | 90.0-95.0 | 338 | 98.4 | 100.0 | 95.0-100.0 | 338 |
| gemma4:31b | calibration | PPE | 322 | 94.4 | 95.0 | 90.0-100.0 | 178 | 97.7 | 100.0 | 95.0-100.0 | 178 |
| gemma4:31b | final | Fall | 276 | 92.0 | 90.0 | 90.0-95.0 | 724 | 98.6 | 100.0 | 95.0-100.0 | 724 |
| gemma4:31b | final | PPE | 669 | 94.7 | 95.0 | 90.0-100.0 | 331 | 98.1 | 100.0 | 95.0-100.0 | 331 |
| qwen3.5:27b | calibration | Fall | 195 | 92.3 | 95.0 | 90.0-95.0 | 305 | 94.6 | 95.0 | 95.0-95.0 | 304 |
| qwen3.5:27b | calibration | PPE | 325 | 90.0 | 90.0 | 85.0-95.0 | 175 | 93.5 | 95.0 | 90.0-100.0 | 175 |
| qwen3.5:27b | final | Fall | 361 | 92.0 | 95.0 | 90.0-95.0 | 639 | 94.8 | 95.0 | 95.0-95.0 | 638 |
| qwen3.5:27b | final | PPE | 670 | 90.1 | 90.0 | 85.0-95.0 | 330 | 94.5 | 95.0 | 90.0-100.0 | 330 |

### By the reference label

| Model | Set | Category | Violation present: n | mean | median | quartiles | Violation absent: n | mean | median | quartiles |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---|
| gemma4:31b | calibration | Fall | 52 | 93.8 | 95.0 | 90.0-95.0 | 448 | 96.7 | 100.0 | 95.0-100.0 |
| gemma4:31b | calibration | PPE | 202 | 95.6 | 95.0 | 95.0-100.0 | 298 | 95.5 | 95.0 | 90.0-100.0 |
| gemma4:31b | final | Fall | 95 | 94.1 | 95.0 | 90.0-95.0 | 905 | 97.1 | 100.0 | 95.0-100.0 |
| gemma4:31b | final | PPE | 413 | 96.1 | 95.0 | 95.0-100.0 | 587 | 95.6 | 95.0 | 90.0-100.0 |
| qwen3.5:27b | calibration | Fall | 52 | 93.5 | 95.0 | 90.0-95.0 | 448 | 93.7 | 95.0 | 90.0-95.0 |
| qwen3.5:27b | calibration | PPE | 202 | 91.3 | 90.0 | 90.0-98.0 | 298 | 91.2 | 90.0 | 85.0-95.0 |
| qwen3.5:27b | final | Fall | 95 | 92.9 | 95.0 | 90.0-95.0 | 905 | 93.9 | 95.0 | 90.0-95.0 |
| qwen3.5:27b | final | PPE | 413 | 92.6 | 95.0 | 90.0-98.0 | 587 | 90.8 | 90.0 | 85.0-100.0 |

The counts of all four label-by-answer cells, with the same statistics, are in `results_posthoc\confidence_signed.json` (diagnostic, crossed_label_by_answer).

## 2. Signed score: thresholds and results

One threshold per category fit on the calibration 500 with `grove_score.fit` (grid 0.02-0.98 step 0.02, best single threshold then 2 rounds per category, micro-F1; the method of experiment 44), applied unchanged to the final 1,000.

| Model | Original confidence/100: Fall | PPE | signed confidence (post hoc; score redefined after the first scoring): Fall | PPE |
|---|---:|---:|---:|---:|
| gemma4:31b | 0.96 | 0.02 | 0.96 | 0.86 |
| qwen3.5:27b | 0.96 | 0.02 | 0.96 | 0.16 |

### Final 1,000 (thresholds from calibration, applied unchanged)

| System | Micro-F1 [95% interval] | Precision | Recall | F1 Fall / PPE | False alarms per 100 negatives | Completion |
|---|---|---:|---:|---|---:|---:|
| GROVE (d3:27b, refit thresholds) | 0.7021 [0.6699, 0.7329] | 0.6777 | 0.7283 | 0.4398 / 0.7601 | 22.8 | 1.000 |
| main questions (d3:27b, refit thresholds) | 0.7152 [0.6851, 0.7457] | 0.6724 | 0.7638 | 0.4216 / 0.7832 | 25.0 | 1.000 |
| single-pass gemma4:31b, frozen prompt (fixed answers) | 0.6423 [0.6131, 0.6698] | 0.4897 | 0.9331 | 0.4083 / 0.7254 | 71.6 | 1.000 |
| gemma4:31b confidence, fitted thresholds (post hoc) | 0.4154 [0.3912, 0.4397] | 0.2761 | 0.8386 | 0.0408 / 0.5846 | 154.0 | 1.000 |
| gemma4:31b confidence prompt, its own present answers (post hoc, for reference) | 0.6442 [0.6151, 0.6716] | 0.4952 | 0.9213 | 0.4151 / 0.7227 | 68.8 | 1.000 |
| **gemma4:31b signed confidence (post hoc; score redefined after the first scoring), fitted thresholds** | 0.6753 [0.6411, 0.7080] | 0.6003 | 0.7717 | 0.0808 / 0.7307 | 40.4 | 1.000 |
| qwen3.5:27b confidence, fitted thresholds (post hoc) | 0.5067 [0.4751, 0.5386] | 0.3660 | 0.8228 | 0.0422 / 0.5846 | 126.8 | 1.000 |
| qwen3.5:27b confidence prompt, its own present answers (post hoc, for reference) | 0.6095 [0.5829, 0.6362] | 0.4549 | 0.9232 | 0.3553 / 0.7165 | 69.2 | 1.000 |
| **qwen3.5:27b signed confidence (post hoc; score redefined after the first scoring), fitted thresholds** | 0.6582 [0.6240, 0.6917] | 0.5772 | 0.7657 | 0.0000 / 0.7157 | 43.2 | 1.000 |

**Paired intervals, GROVE minus each signed baseline** (bootstrap, 4000 draws, seed 20260422, near-copy groups). The intervals for the original confidence/100 baselines are in `reports\posthoc_confidence_baseline.md`.

- GROVE minus gemma4:31b signed confidence (post hoc; score redefined after the first scoring): micro-F1 +0.0268 [-0.0029, +0.0575]; Fall +0.3590 [+0.2536, +0.4643]; PPE +0.0294 [+0.0015, +0.0576]; false alarms per 100 negatives -17.6 [-21.9, -13.4]; valid-only (1000 images) +0.0268 [-0.0029, +0.0575]. Statuses: {'valid': 1000}.
- GROVE minus qwen3.5:27b signed confidence (post hoc; score redefined after the first scoring): micro-F1 +0.0439 [+0.0134, +0.0765]; Fall +0.4398 [+0.3509, +0.5269]; PPE +0.0444 [+0.0156, +0.0750]; false alarms per 100 negatives -20.4 [-24.9, -15.8]; valid-only (1000 images) +0.0439 [+0.0134, +0.0765]. Statuses: {'valid': 1000}.

Average precision (threshold-free; intervals from the same 4000 paired draws):

| Category | GROVE | main questions | gemma4:31b confidence/100 | qwen3.5:27b confidence/100 | gemma4:31b signed | qwen3.5:27b signed | GROVE minus gemma4:31b signed | GROVE minus qwen3.5:27b signed |
|---|---|---|---|---|---|---|---|---|
| Fall | 0.3956 [0.3147, 0.5039] | 0.4239 [0.3321, 0.5282] | 0.0764 [0.0620, 0.0928] | 0.0871 [0.0701, 0.1073] | 0.3444 [0.2688, 0.4245] | 0.2408 [0.1897, 0.2974] | +0.0513 [-0.0090, +0.1349] | +0.1548 [+0.0955, +0.2413] |
| PPE | 0.8645 [0.8352, 0.8912] | 0.8850 [0.8585, 0.9089] | 0.4235 [0.3875, 0.4600] | 0.4295 [0.3928, 0.4675] | 0.7349 [0.6934, 0.7736] | 0.7811 [0.7443, 0.8155] | +0.1296 [+0.1001, +0.1617] | +0.0834 [+0.0566, +0.1133] |

### Calibration 500 (thresholds fit on these images: in-sample, not independent)

| System | Micro-F1 [95% interval] | Precision | Recall | F1 Fall / PPE | False alarms per 100 negatives | Completion |
|---|---|---:|---:|---|---:|---:|
| GROVE (d3:27b, refit thresholds) | 0.7065 [0.6642, 0.7467] | 0.6726 | 0.7441 | 0.4878 / 0.7718 | 20.0 | 1.000 |
| main questions (d3:27b, refit thresholds) | 0.7063 [0.6632, 0.7458] | 0.6512 | 0.7717 | 0.4697 / 0.7801 | 23.2 | 1.000 |
| single-pass gemma4:31b, frozen prompt (fixed answers) | 0.6162 [0.5769, 0.6531] | 0.4649 | 0.9134 | 0.4036 / 0.7057 | 71.6 | 1.000 |
| gemma4:31b confidence, fitted thresholds (post hoc) | 0.4194 [0.3826, 0.4545] | 0.2818 | 0.8189 | 0.0414 / 0.5755 | 152.0 | 1.000 |
| gemma4:31b confidence prompt, its own present answers (post hoc, for reference) | 0.6287 [0.5897, 0.6658] | 0.4793 | 0.9134 | 0.4112 / 0.7176 | 66.8 | 1.000 |
| **gemma4:31b signed confidence (post hoc; score redefined after the first scoring), fitted thresholds** | 0.6643 [0.6154, 0.7113] | 0.6078 | 0.7323 | 0.0370 / 0.7312 | 37.2 | 1.000 |
| qwen3.5:27b confidence, fitted thresholds (post hoc) | 0.5012 [0.4545, 0.5455] | 0.3635 | 0.8071 | 0.0517 / 0.5755 | 123.2 | 1.000 |
| qwen3.5:27b confidence prompt, its own present answers (post hoc, for reference) | 0.6072 [0.5699, 0.6421] | 0.4519 | 0.9252 | 0.3401 / 0.7324 | 69.2 | 1.000 |
| **qwen3.5:27b signed confidence (post hoc; score redefined after the first scoring), fitted thresholds** | 0.6655 [0.6182, 0.7114] | 0.5873 | 0.7677 | 0.0000 / 0.7331 | 42.4 | 1.000 |

**Paired intervals, GROVE minus each signed baseline** (bootstrap, 4000 draws, seed 20260422, near-copy groups). The intervals for the original confidence/100 baselines are in `reports\posthoc_confidence_baseline.md`.

- GROVE minus gemma4:31b signed confidence (post hoc; score redefined after the first scoring): micro-F1 +0.0423 [-0.0030, +0.0854]; Fall +0.4508 [+0.3190, +0.5652]; PPE +0.0406 [-0.0003, +0.0795]; false alarms per 100 negatives -17.2 [-23.4, -11.0]; valid-only (500 images) +0.0423 [-0.0030, +0.0854]. Statuses: {'valid': 500}.
- GROVE minus qwen3.5:27b signed confidence (post hoc; score redefined after the first scoring): micro-F1 +0.0410 [-0.0076, +0.0890]; Fall +0.4878 [+0.3731, +0.5865]; PPE +0.0388 [-0.0065, +0.0834]; false alarms per 100 negatives -22.4 [-28.8, -15.6]; valid-only (500 images) +0.0410 [-0.0076, +0.0890]. Statuses: {'valid': 500}.

Average precision (threshold-free; intervals from the same 4000 paired draws):

| Category | GROVE | main questions | gemma4:31b confidence/100 | qwen3.5:27b confidence/100 | gemma4:31b signed | qwen3.5:27b signed | GROVE minus gemma4:31b signed | GROVE minus qwen3.5:27b signed |
|---|---|---|---|---|---|---|---|---|
| Fall | 0.3778 [0.2823, 0.5186] | 0.3602 [0.2655, 0.4959] | 0.0841 [0.0631, 0.1091] | 0.0981 [0.0733, 0.1287] | 0.2884 [0.2113, 0.3864] | 0.2230 [0.1603, 0.2977] | +0.0894 [+0.0172, +0.1988] | +0.1548 [+0.0826, +0.2712] |
| PPE | 0.8531 [0.8053, 0.8937] | 0.8623 [0.8162, 0.9010] | 0.4026 [0.3535, 0.4551] | 0.4026 [0.3528, 0.4584] | 0.7227 [0.6617, 0.7816] | 0.7314 [0.6716, 0.7863] | +0.1304 [+0.0842, +0.1767] | +0.1217 [+0.0799, +0.1641] |

Figure: `reports\posthoc_pr_final_signed.png` (final 1,000; dotted lines confidence/100, dashed lines signed). Numbers in `results_posthoc\confidence_signed.json`.

