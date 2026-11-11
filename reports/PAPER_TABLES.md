# Paper tables: every number with its source

Written 2026-11-10T12:11:17 by `code\posthoc_parta.py tables` (D24). **Nothing here is computed anew:** each number is copied from the result or report file named beside it (tables copied whole from a report say so above them). Final-set numbers are from final scoring (experiment 54, `logs\final_scored.lock`). Rows marked post hoc or sensitivity come from the analyses of D23 and D24, not from the planned run.

## 1. Datasets

Source: `reports\FINAL_RESULTS.md` (Table 1), `results\e07_lists.json`.

| Set | Images | Positive image-category pairs | Notes |
|---|---:|---:|---|
| 203 development images | 203 | 125 (Fall 61, Electrical 24, PPE 40) | 3 scored categories |
| Calibration | 500 | - | with 250, without 250, top-up {'with': 189, 'without': 0} |
| Final test | 1000 | - | with 500, without 500, top-up {'with': 326, 'without': 0} |

- calibration list (`results\e07_lists.json`): n 500, with violation 250, without 250, top-up from tuning_rest {'with': 189, 'without': 0}, reference violation rate r 0.1220 (tuning_sample), visibility cutoff (largest box share) 0.00300.
- final list (`results\e07_lists.json`): n 1000, with violation 500, without 500, top-up from tuning_rest {'with': 326, 'without': 0}, reference violation rate r 0.1180 (validation), visibility cutoff (largest box share) 0.00300.

## 2. Screening on the 203 images (Table 2)

Copied from `reports\screening.md` (numbers in `results\e15_screening.json`, selection in `freeze\selection.json`).


| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, Electrical, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Single-pass qwen3.5:9b | 1.000 | 73.0/29.0/52.0 | 0.7157 | 0.5840 | 0.6432 | 0.6297 | 0.713 / 0.591 / 0.585 | 12.6 | 2.2 | statuses {'valid': 203} |
| Single-pass qwen3.5:27b | 1.000 | 73.0/15.0/52.0 | 0.8295 | 0.5840 | 0.6854 | 0.6805 | 0.674 / 0.650 / 0.718 | 3.6 | 5.3 | statuses {'valid': 203} |
| Single-pass gemma4:31b | 1.000 | 80.0/30.0/45.0 | 0.7273 | 0.6400 | 0.6809 | 0.6521 | 0.667 / 0.524 / 0.766 | 16.2 | 4.0 | statuses {'valid': 203} |
| Single-pass mistral-small3.2:24b | 1.000 | 42.0/16.0/83.0 | 0.7241 | 0.3360 | 0.4590 | 0.3457 | 0.648 / 0.222 / 0.167 | 9.9 | 3.5 | statuses {'valid': 203} |
| Single-pass ministral-3:14b | 1.000 | 48.0/18.0/77.0 | 0.7273 | 0.3840 | 0.5026 | 0.5016 | 0.526 / 0.550 / 0.429 | 10.8 | 2.4 | statuses {'valid': 203} |
| Single-pass qwen3-vl:32b | 0.995 | 78.0/46.0/47.0 | 0.6290 | 0.6240 | 0.6265 | 0.6042 | 0.680 / 0.513 / 0.619 | 24.3 | 51.9 | statuses {'valid': 202, 'cut_off': 1} |
| Main questions only (m) clef:27b | 1.000 | 104.0/42.3/21.0 | 0.7109 | 0.8320 | 0.7667 | 0.7424 | 0.816 / 0.637 / 0.775 | 23.0 | 1.1 |  |
| GROVE questions and formula (h) clef:27b | 1.000 | 99.1/42.0/25.9 | 0.7023 | 0.7928 | 0.7448 | 0.6949 | 0.831 / 0.527 / 0.727 | 21.4 | 1.9 |  |
| Original 7 questions (S0) clef:27b | 1.000 | 91.0/61.8/34.0 | 0.5955 | 0.7280 | 0.6551 | 0.6374 | 0.700 / 0.586 / 0.626 | 33.9 | 1.3 |  |
| Main questions only (m) clef-flash:9b | 1.000 | 92.4/45.7/32.6 | 0.6691 | 0.7392 | 0.7024 | 0.6792 | 0.803 / 0.648 / 0.586 | 21.4 | 0.5 |  |
| GROVE questions and formula (h) clef-flash:9b | 1.000 | 97.9/42.3/27.1 | 0.6983 | 0.7832 | 0.7383 | 0.7032 | 0.796 / 0.581 / 0.732 | 21.5 | 0.8 |  |
| Original 7 questions (S0) clef-flash:9b | 1.000 | 97.1/61.0/27.9 | 0.6142 | 0.7768 | 0.6860 | 0.6760 | 0.747 / 0.662 / 0.620 | 30.9 | 0.6 |  |
| Main questions only (m) pplx-decider:27b | 0.990 | 88.0/39.5/37.0 | 0.6902 | 0.7040 | 0.6970 | 0.6649 | 0.778 / 0.604 / 0.613 | 19.0 | 1.2 |  |
| GROVE questions and formula (h) pplx-decider:27b | 1.000 | 103.9/41.5/21.1 | 0.7146 | 0.8312 | 0.7685 | 0.7310 | 0.807 / 0.597 / 0.789 | 21.0 | 2.4 |  |
| Original 7 questions (S0) pplx-decider:27b | 1.000 | 98.4/55.9/26.6 | 0.6377 | 0.7872 | 0.7046 | 0.6857 | 0.732 / 0.614 / 0.711 | 28.9 | 1.6 |  |
| Main questions only (m) d3:9b | 1.000 | 82.3/56.5/42.7 | 0.5929 | 0.6584 | 0.6240 | 0.5967 | 0.742 / 0.571 / 0.477 | 29.1 | 1.2 |  |
| GROVE questions and formula (h) d3:9b | 1.000 | 94.0/44.3/31.0 | 0.6797 | 0.7520 | 0.7140 | 0.6877 | 0.738 / 0.588 / 0.737 | 22.2 | 4.9 |  |
| Original 7 questions (S0) d3:9b | 1.000 | 97.8/58.5/27.2 | 0.6257 | 0.7824 | 0.6953 | 0.6782 | 0.777 / 0.706 / 0.552 | 30.1 | 2.2 |  |
| Main questions only (m) d3:27b | 1.000 | 97.1/36.1/27.9 | 0.7290 | 0.7768 | 0.7521 | 0.7264 | 0.785 / 0.623 / 0.772 | 18.5 | 2.5 |  |
| GROVE questions and formula (h) d3:27b | 1.000 | 105.2/37.4/19.8 | 0.7377 | 0.8416 | 0.7862 | 0.7565 | 0.834 / 0.653 / 0.783 | 17.7 | 9.9 |  |
| Original 7 questions (S0) d3:27b | 1.000 | 95.9/39.6/29.1 | 0.7077 | 0.7672 | 0.7363 | 0.7106 | 0.807 / 0.636 / 0.688 | 18.8 | 4.3 |  |
| **GROVE** (d3:27b, Electrical formula of d3:27b) | 1.000 | 105.2/37.4/19.8 | 0.7377 | 0.8416 | 0.7862 | 0.7565 | 0.834 / 0.653 / 0.783 | 17.7 | 9.9 |  |


### Gain from fact questions and the formula, same model (h formula minus m main questions)

| Model | Micro-F1 m | Micro-F1 h | Difference (95% interval, paired bootstrap by scene group) |
|---|---:|---:|---|
| clef:27b | 0.7667 | 0.7448 | -0.0218 [-0.0587, +0.0138] |
| clef-flash:9b | 0.7024 | 0.7383 | +0.0359 [-0.0050, +0.0778] |
| pplx-decider:27b | 0.6970 | 0.7685 | +0.0715 [+0.0275, +0.1165] |
| d3:9b | 0.6240 | 0.7140 | +0.0901 [+0.0543, +0.1287] |
| d3:27b | 0.7521 | 0.7862 | +0.0341 [-0.0020, +0.0708] |


### GROVE against single-pass models

- GROVE minus qwen3.5:27b: +0.1008 [+0.0283, +0.1751]
- GROVE minus gemma4:31b: +0.1054 [+0.0513, +0.1625]
- GROVE minus qwen3.5:9b: +0.1431 [+0.0801, +0.2050]
- GROVE minus qwen3-vl:32b: +0.1597 [+0.0999, +0.2269]
- GROVE minus ministral-3:14b: +0.2836 [+0.1900, +0.3774]
- GROVE minus mistral-small3.2:24b: +0.3272 [+0.2414, +0.4155]
- Valid-only sensitivity (203 images where both are valid), GROVE minus qwen3.5:27b: +0.1008 [+0.0283, +0.1751]


### Selection (experiment 14)

- Main model d3:27b, Electrical from formula of d3:27b, held-out micro-F1 0.7862, runner-up main model pplx-decider:27b (`freeze\selection.json`). Best single-pass for the new images: gemma4:31b (experiment 46, `freeze\best_baseline.json`).

## 3. GROVE, main questions and best single-pass (Table 3)

| Set | Thresholds | System | Micro-F1 [95% interval where saved] | Precision | Recall | F1 per category | False alarms per 100 negatives | Completion | Source |
|---|---|---|---|---:|---:|---|---:|---:|---|
| 203 (Fall, Electrical, PPE) | held-out folds (10 x 5 grouped, fit on training folds); single-pass fixed | GROVE | 0.7862 | 0.7377 | 0.8416 | 0.8336 / 0.6531 / 0.7827 | 17.7 | 1.000 | `results\e15_screening.json` |
| 203 (Fall, Electrical, PPE) | held-out folds (10 x 5 grouped, fit on training folds); single-pass fixed | main questions (d3:27b) | 0.7521 | 0.7290 | 0.7768 | 0.7846 / 0.6225 / 0.7722 | 18.5 | 1.000 | `results\e15_screening.json` |
| 203 (Fall, Electrical, PPE) | held-out folds (10 x 5 grouped, fit on training folds); single-pass fixed | single-pass gemma4:31b (frozen best single-pass) | 0.6809 | 0.7273 | 0.6400 | 0.6667 / 0.5238 / 0.7660 | 16.2 | 1.000 | `results\e15_screening.json` |
| 203 (Fall, Electrical, PPE) | held-out folds (10 x 5 grouped, fit on training folds); single-pass fixed | single-pass qwen3.5:27b (best on the 203) | 0.6854 | 0.8295 | 0.5840 | 0.6737 / 0.6500 / 0.7179 | 3.6 | 1.000 | `results\e15_screening.json` |
| 203 (Fall, PPE only; experiment 25) | held-out folds; single-pass fixed | GROVE | 0.8108 | 0.7410 | 0.8950 | 0.8307 / 0.7827 | 19.2 | - | `results\e24_30.json` |
| 203 (Fall, PPE only; experiment 25) | held-out folds; single-pass fixed | main questions (d3:27b) | 0.7811 | 0.7459 | 0.8198 | 0.7842 / 0.7763 | 18.1 | - | `results\e24_30.json` |
| 203 (Fall, PPE only; experiment 25) | held-out folds; single-pass fixed | single-pass qwen3.5:27b (best on the 203) | 0.6936 | 0.8333 | 0.5941 | 0.6737 / 0.7179 | 1.6 | - | `results\e24_30.json` |
| 203 | first-freeze (fit on all 203) | all systems | not saved by the run (only the thresholds, `results\e_thresholds_all203.json`; these are in-sample) | | | | | | - |
| Calibration 500 (Fall, PPE; not independent) | first-freeze (from the 203) | GROVE | 0.4798 | 0.3198 | 0.9606 | 0.2208 / 0.7033 | 133.6 | 1.000 | `results\e48.json` |
| Calibration 500 (Fall, PPE; not independent) | first-freeze (from the 203) | main questions (d3:27b) | 0.5401 | 0.3908 | 0.8740 | 0.2695 / 0.7627 | 82.8 | 1.000 | `results\e48.json` |
| Calibration 500 (Fall, PPE; not independent) | first-freeze (from the 203) | single-pass gemma4:31b (frozen best single-pass) | 0.6162 | 0.4649 | 0.9134 | 0.4036 / 0.7057 | 71.6 | 1.000 | `results\e48.json` |
| Calibration 500 (Fall, PPE; not independent) | first-freeze (from the 203) | single-pass qwen3.5:27b | 0.6038 | 0.4463 | 0.9331 | 0.3468 / 0.7225 | 72.0 | 1.000 | `results\e48.json` |
| Calibration 500 (Fall, PPE; not independent) | first-freeze (from the 203) | GROVE questions, runner-up model pplx-decider:27b | 0.4820 | 0.3231 | 0.9488 | 0.2068 / 0.7606 | 123.6 | 1.000 | `results\e48.json` |
| Calibration 500 (Fall, PPE; not independent) | refit on these 500 (in-sample) | GROVE | 0.7065 | 0.6726 | 0.7441 | 0.4878 / 0.7718 | 20.0 | 1.000 | `results\e48.json` |
| Calibration 500 (Fall, PPE; not independent) | refit on these 500 (in-sample) | main questions (d3:27b) | 0.7063 | 0.6512 | 0.7717 | 0.4697 / 0.7801 | 23.2 | 1.000 | `results\e48.json` |
| Calibration 500 (Fall, PPE; not independent) | refit on these 500 (in-sample) | single-pass gemma4:31b (frozen best single-pass) | 0.6162 | 0.4649 | 0.9134 | 0.4036 / 0.7057 | 71.6 | 1.000 | `results\e48.json` |
| Calibration 500 (Fall, PPE; not independent) | refit on these 500 (in-sample) | single-pass qwen3.5:27b | 0.6038 | 0.4463 | 0.9331 | 0.3468 / 0.7225 | 72.0 | 1.000 | `results\e48.json` |
| Calibration 500 (Fall, PPE; not independent) | refit on these 500 (in-sample) | GROVE questions, runner-up model pplx-decider:27b | 0.7149 | 0.7295 | 0.7008 | 0.2571 / 0.7897 | 19.2 | 1.000 | `results\e48.json` |
| **Final 1,000** (Fall, PPE) | refit on calibration (primary); single-pass fixed | GROVE | 0.7021 [0.6699, 0.7329] | 0.6777 | 0.7283 | 0.4398 / 0.7601 | 22.8 | 1.000 | `results\e54_final.json` |
| **Final 1,000** (Fall, PPE) | refit on calibration (primary); single-pass fixed | main questions (d3:27b) | 0.7152 [0.6851, 0.7457] | 0.6724 | 0.7638 | 0.4216 / 0.7832 | 25.0 | 1.000 | `results\e54_final.json` |
| **Final 1,000** (Fall, PPE) | refit on calibration (primary); single-pass fixed | single-pass gemma4:31b (best single-pass) | 0.6423 [0.6131, 0.6698] | 0.4897 | 0.9331 | 0.4083 / 0.7254 | 71.6 | 1.000 | `results\e54_final.json` |
| Final 1,000 | first-freeze | per-system scores | not saved by the run; only GROVE minus best single-pass below | | | | | | - |

Criteria on the final 1,000 (`results\e54_final.json`, `criteria`):

- Primary, GROVE minus best single-pass micro-F1: +0.0598 [+0.0305, +0.0906], met True.
- False alarms per 100 negatives, GROVE minus best single-pass: -48.8000 [-54.8389, -42.9974], met True.
- GROVE minus main questions: -0.0131 [-0.0312, +0.0049], met False.
- Top-box F1 at 0.5: GROVE 0.3333, best single-pass 0.0036, met True.
- Valid-only sensitivity (1000 images): +0.0598 [+0.0305, +0.0906]. First-freeze thresholds, GROVE minus best single-pass: -0.1597 [-0.1775, -0.1426].
- Per category, GROVE minus best single-pass: Fall +0.0315 [-0.0511, +0.1118]; PPE +0.0347 [+0.0064, +0.0644].
- Calibration (`results\e48.json`), refit thresholds (in-sample): GROVE minus best single-pass micro-F1 +0.0903 [+0.0521, +0.1285], false alarms per 100 negatives -51.6000 [-59.9156, -43.4199]; GROVE minus main questions +0.0002 [-0.0252, +0.0262]. First-freeze thresholds: GROVE minus best single-pass micro-F1 -0.1364 [-0.1592, -0.1132], false alarms +62.0000 [+54.3207, +69.7482]; GROVE minus main questions -0.0603 [-0.0811, -0.0393].

## 4. Per category (Table 4)

203 images: F1 per category in section 2 and section 3 (held-out). Calibration and final: copied from `reports\per_category_subgroups.md` (numbers in `results\e57_59.json`).

### Calibration (500 images, not independent)

| System | Category | F1 (95% interval) | Precision | Recall |
|---|---|---|---:|---:|
| GROVE | Fall | 0.4878 [0.3731, 0.5865] | 0.4225 | 0.5769 |
| GROVE | PPE | 0.7718 [0.7260, 0.8145] | 0.7571 | 0.7871 |
| main_question | Fall | 0.4697 [0.3564, 0.5714] | 0.3875 | 0.5962 |
| main_question | PPE | 0.7801 [0.7342, 0.8227] | 0.7466 | 0.8168 |
| single-pass gemma4:31b | Fall | 0.4036 [0.3220, 0.4828] | 0.2632 | 0.8654 |
| single-pass gemma4:31b | PPE | 0.7057 [0.6610, 0.7486] | 0.5701 | 0.9257 |

| System | False alarms per 100 negative images | Prevalence-standardized precision (95% interval) | Prevalence-standardized F1 (95% interval) | Completion |
|---|---:|---|---|---:|
| GROVE | 20.0 | 0.3199 [0.2700, 0.3857] | 0.4474 [0.3924, 0.5105] | 1.000 |
| main_question | 23.2 | 0.2968 [0.2524, 0.3535] | 0.4287 [0.3783, 0.4872] | 1.000 |
| single-pass gemma4:31b | 71.6 | 0.1443 [0.1302, 0.1609] | 0.2492 [0.2275, 0.2742] | 1.000 |
- r = 0.1220 (natural violation rate of the main pool), p = 0.5000 in this sample. Top-up images count in their group, so this is performance standardized to that rate under the assumption that the pools are comparable within the violation and no-violation groups.


### Final test (1000 images)

| System | Category | F1 (95% interval) | Precision | Recall |
|---|---|---|---:|---:|
| GROVE | Fall | 0.4398 [0.3509, 0.5269] | 0.4375 | 0.4421 |
| GROVE | PPE | 0.7601 [0.7273, 0.7914] | 0.7289 | 0.7942 |
| main_question | Fall | 0.4216 [0.3333, 0.5025] | 0.3945 | 0.4526 |
| main_question | PPE | 0.7832 [0.7521, 0.8131] | 0.7372 | 0.8354 |
| single-pass gemma4:31b | Fall | 0.4083 [0.3440, 0.4700] | 0.2705 | 0.8316 |
| single-pass gemma4:31b | PPE | 0.7254 [0.6950, 0.7553] | 0.5843 | 0.9564 |

| System | False alarms per 100 negative images | Prevalence-standardized precision (95% interval) | Prevalence-standardized F1 (95% interval) | Completion |
|---|---:|---|---|---:|
| GROVE | 22.8 | 0.2881 [0.2555, 0.3276] | 0.4129 [0.3760, 0.4549] | 1.000 |
| main_question | 25.0 | 0.2799 [0.2493, 0.3157] | 0.4096 [0.3740, 0.4500] | 1.000 |
| single-pass gemma4:31b | 71.6 | 0.1443 [0.1334, 0.1563] | 0.2499 [0.2333, 0.2680] | 1.000 |
- r = 0.1180 (natural violation rate of the main pool), p = 0.5000 in this sample. Top-up images count in their group, so this is performance standardized to that rate under the assumption that the pools are comparable within the violation and no-violation groups.


## 5. Subgroups

Copied from `reports\per_category_subgroups.md` (experiment 58) and `reports\calibration.md`.

#### Subgroups, Calibration (500 images, not independent), GROVE

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 483 | 0.7073 | 0.7595 | 20.0 |
| Hazard size below 1% of image (violation images) | 86 | 0.8302 | 0.7500 | 0.0 |
| Hazard size 1% to 10% (violation images) | 120 | 0.7563 | 0.7438 | 0.0 |
| Hazard size 10% or more (violation images) | 44 | 0.7500 | 0.7333 | 0.0 |
| camera_distance = long distance | 18 | 0.4000 | 0.2500 | 0.0 |
| camera_distance = mid distance | 369 | 0.7103 | 0.7344 | 16.6 |
| camera_distance = short distance | 113 | 0.7068 | 0.8103 | 36.4 |
| illumination = night | 37 | 0.5490 | 0.4000 | 0.0 |
| illumination = normal lighting | 388 | 0.7143 | 0.8011 | 22.5 |
| illumination = overexposed | 18 | 0.7368 | 0.8750 | 9.1 |
| illumination = underexposed | 57 | 0.7797 | 0.7667 | 7.1 |
| Rule-4-only negatives (false alarms) | 0 | - | - | - |


#### Subgroups, Calibration (500 images, not independent), main_question

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 483 | 0.6947 | 0.7679 | 23.2 |
| Hazard size below 1% of image (violation images) | 86 | 0.8941 | 0.8636 | 0.0 |
| Hazard size 1% to 10% (violation images) | 120 | 0.7521 | 0.7521 | 0.0 |
| Hazard size 10% or more (violation images) | 44 | 0.6824 | 0.6444 | 0.0 |
| camera_distance = long distance | 18 | 0.5714 | 0.5000 | 7.1 |
| camera_distance = mid distance | 369 | 0.7022 | 0.7552 | 21.0 |
| camera_distance = short distance | 113 | 0.7259 | 0.8448 | 34.5 |
| illumination = night | 37 | 0.5185 | 0.4000 | 0.0 |
| illumination = normal lighting | 388 | 0.7299 | 0.8508 | 24.9 |
| illumination = overexposed | 18 | 0.5556 | 0.6250 | 18.2 |
| illumination = underexposed | 57 | 0.7541 | 0.7667 | 14.3 |
| Rule-4-only negatives (false alarms) | 0 | - | - | - |


#### Subgroups, Calibration (500 images, not independent), single-pass gemma4:31b

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 483 | 0.5981 | 0.9072 | 71.6 |
| Hazard size below 1% of image (violation images) | 86 | 0.8615 | 0.9545 | 0.0 |
| Hazard size 1% to 10% (violation images) | 120 | 0.7914 | 0.9091 | 0.0 |
| Hazard size 10% or more (violation images) | 44 | 0.7525 | 0.8444 | 0.0 |
| camera_distance = long distance | 18 | 0.3750 | 0.7500 | 57.1 |
| camera_distance = mid distance | 369 | 0.6135 | 0.9010 | 70.7 |
| camera_distance = short distance | 113 | 0.6474 | 0.9655 | 78.2 |
| illumination = night | 37 | 0.6667 | 0.6571 | 0.0 |
| illumination = normal lighting | 388 | 0.6014 | 0.9503 | 73.7 |
| illumination = overexposed | 18 | 0.5333 | 1.0000 | 100.0 |
| illumination = underexposed | 57 | 0.7073 | 0.9667 | 50.0 |
| Rule-4-only negatives (false alarms) | 0 | - | - | - |


#### Subgroups, Final test (1000 images), GROVE

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 942 | 0.6953 | 0.7378 | 22.8 |
| Hazard size below 1% of image (violation images) | 201 | 0.8571 | 0.7761 | 0.0 |
| Hazard size 1% to 10% (violation images) | 200 | 0.7725 | 0.7192 | 0.0 |
| Hazard size 10% or more (violation images) | 99 | 0.6869 | 0.6538 | 0.0 |
| camera_distance = long distance | 46 | 0.7647 | 0.7222 | 7.1 |
| camera_distance = mid distance | 727 | 0.6933 | 0.7046 | 20.9 |
| camera_distance = short distance | 227 | 0.7185 | 0.8017 | 33.3 |
| illumination = night | 58 | 0.5385 | 0.3889 | 0.0 |
| illumination = normal lighting | 794 | 0.7191 | 0.7775 | 23.2 |
| illumination = overexposed | 42 | 0.6047 | 0.6842 | 26.1 |
| illumination = underexposed | 106 | 0.7290 | 0.7358 | 20.4 |
| Rule-4-only negatives (false alarms) | 2 | 0.0000 | 0.0000 | 0.0 |


#### Subgroups, Final test (1000 images), main_question

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 942 | 0.6960 | 0.7556 | 25.0 |
| Hazard size below 1% of image (violation images) | 201 | 0.9171 | 0.8806 | 0.0 |
| Hazard size 1% to 10% (violation images) | 200 | 0.7853 | 0.7389 | 0.0 |
| Hazard size 10% or more (violation images) | 99 | 0.6354 | 0.5865 | 0.0 |
| camera_distance = long distance | 46 | 0.7778 | 0.7778 | 10.7 |
| camera_distance = mid distance | 727 | 0.7103 | 0.7507 | 24.5 |
| camera_distance = short distance | 227 | 0.7212 | 0.8017 | 30.6 |
| illumination = night | 58 | 0.5122 | 0.3889 | 0.0 |
| illumination = normal lighting | 794 | 0.7318 | 0.8141 | 26.0 |
| illumination = overexposed | 42 | 0.5714 | 0.6316 | 30.4 |
| illumination = underexposed | 106 | 0.7928 | 0.8302 | 16.7 |
| Rule-4-only negatives (false alarms) | 2 | 0.0000 | 0.0000 | 0.0 |


#### Subgroups, Final test (1000 images), single-pass gemma4:31b

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 942 | 0.6164 | 0.9267 | 71.6 |
| Hazard size below 1% of image (violation images) | 201 | 0.9061 | 0.9602 | 0.0 |
| Hazard size 1% to 10% (violation images) | 200 | 0.8168 | 0.9113 | 0.0 |
| Hazard size 10% or more (violation images) | 99 | 0.8033 | 0.9231 | 0.0 |
| camera_distance = long distance | 46 | 0.6071 | 0.9444 | 60.7 |
| camera_distance = mid distance | 727 | 0.6369 | 0.9268 | 72.3 |
| camera_distance = short distance | 227 | 0.6647 | 0.9504 | 72.2 |
| illumination = night | 58 | 0.7193 | 0.7593 | 0.0 |
| illumination = normal lighting | 794 | 0.6309 | 0.9555 | 74.9 |
| illumination = overexposed | 42 | 0.5538 | 0.9474 | 87.0 |
| illumination = underexposed | 106 | 0.7143 | 0.9434 | 44.4 |
| Rule-4-only negatives (false alarms) | 2 | 0.0000 | 0.0000 | 100.0 |

## 6. False alarms and prevalence-standardized precision

- Calibration and final: the false-alarm and prevalence-standardized tables in section 4 (copied from `reports\per_category_subgroups.md`, experiment 59).
- Final, GROVE minus best single-pass, false alarms per 100 negatives: -48.8000 [-54.8389, -42.9974] (`results\e54_final.json`).
- 203 images: copied from `reports\intervals_addendum.md` (D23, offline, after final scoring):

GROVE and main questions: held-out predictions (10 repeats of 5 grouped folds, seed 20260422, thresholds fit on training folds only), averaged over repeats, exactly as in `reports\screening.md`. Single-pass: fixed answers. Negative images: no scored violation (111 of 203).

| Comparison | GROVE | Other system | GROVE minus other (95% interval) |
|---|---:|---:|---|
| GROVE minus main questions only (m), d3:27b | 17.7 | 18.5 | -0.7 [-6.6, +4.7] |
| GROVE minus best single-pass, gemma4:31b (experiment 46 choice, frozen) | 17.7 | 16.2 | +1.5 [-4.9, +7.3] |
| GROVE minus single-pass qwen3.5:27b (highest micro-F1 on the 203) | 17.7 | 3.6 | +14.1 [+6.2, +22.2] |

Check: GROVE 17.7, main questions 18.5 per 100 negatives, the same values as `reports\screening.md`.


## 7. Removing one part at a time (Table 5)

### 203 images (copied from `reports\removal_tests.md`, numbers in `results\e16_21.json`)

Offline, from saved outputs of d3:27b. Held-out: 10 repeats of 5 grouped folds, seed 20260422, thresholds fit on training folds only (except experiment 21).

| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, Electrical, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE (as selected) | 1.000 | 105.2/37.4/19.8 | 0.7377 | 0.8416 | 0.7862 | 0.7565 | 0.834 / 0.653 / 0.783 | 17.7 | - |  |
| 16 Main questions only (m set of d3:27b) | 1.000 | 97.1/36.1/27.9 | 0.7290 | 0.7768 | 0.7521 | 0.7264 | 0.785 / 0.623 / 0.772 | 18.5 | - |  |
| 17 No protection term | 1.000 | 103.5/38.8/21.5 | 0.7273 | 0.8280 | 0.7744 | 0.7484 | 0.809 / 0.653 / 0.783 | 19.1 | - |  |
| 18 No worker-visible term | 1.000 | 103.6/38.4/21.4 | 0.7296 | 0.8288 | 0.7760 | 0.7465 | 0.834 / 0.653 / 0.753 | 17.5 | - |  |
| 19 Electrical from the main model (h formula) | 1.000 | 105.2/37.4/19.8 | 0.7377 | 0.8416 | 0.7862 | 0.7565 | 0.834 / 0.653 / 0.783 | 17.7 | - |  |
| 20 One threshold for all categories | 1.000 | 89.8/33.6/35.2 | 0.7277 | 0.7184 | 0.7230 | 0.7030 | 0.742 / 0.624 / 0.743 | 15.0 | - |  |
| 21 Fixed 0.5, nothing tuned | 1.000 | 86.0/23.0/39.0 | 0.7890 | 0.6880 | 0.7350 | 0.7123 | 0.713 / 0.615 / 0.809 | 10.8 | - |  |

| Change | Micro-F1 change against GROVE (95% interval, paired bootstrap by scene group) |
|---|---|
| 16 Main questions only (m set of d3:27b) | -0.0341 [-0.0708, +0.0020] |
| 17 No protection term | -0.0118 [-0.0234, -0.0031] |
| 18 No worker-visible term | -0.0102 [-0.0200, -0.0023] |
| 19 Electrical from the main model (h formula) | +0.0000 [+0.0000, +0.0000] |
| 20 One threshold for all categories | -0.0632 [-0.1082, -0.0219] |
| 21 Fixed 0.5 | -0.0512 [-0.0976, -0.0046] |

Experiment 22 (learned safe-image filter) is not run, as the design states.

### Final 1,000 (`results\e55_removal_final.json`; thresholds from `freeze_2.json`, unchanged)

| Variant | Micro-F1 | Micro-F1 change against GROVE (95% interval) |
|---|---:|---|
| variant_no_fact_questions | 0.7152 | +0.0131 [-0.0049, +0.0312] |
| variant_no_protection | 0.7011 | -0.0010 [-0.0102, +0.0091] |
| variant_no_worker | 0.7074 | +0.0053 [-0.0005, +0.0121] |

### Calibration 500 (`results\e44.json`, refit thresholds, in-sample)

| System | Micro-F1 refit | Micro-F1 first-freeze |
|---|---:|---:|
| GROVE | 0.7065 | 0.4798 |
| main_question | 0.7063 | 0.5401 |
| variant_no_fact_questions | 0.7063 | 0.5401 |
| variant_no_protection | 0.7009 | 0.4742 |
| variant_no_worker | 0.7050 | 0.4879 |
| second_GROVE_questions | 0.7149 | 0.4820 |

## 8. Grounding, top box against top box (Table 6)

### 203 images (copied from `reports\grounding.md`, numbers in `results\e31_38.json`)

Thresholds fit on all 203 images for the selected GROVE models ({'Fall_Hazard': 0.12, 'Electrocution_Hazard': 0.32, 'PPE_Violation': 0.5}). Flagged image-category pairs: 144. True boxes: all boxes in the scored categories (132), including categories the system did not flag. One-to-one matching per image and category (primary cutoff 0.5, also 0.3). Comparisons use the top box per category.

| System | Predicted boxes | True boxes | Matched at 0.5 | Box precision | Box recall | Box F1 at 0.5 | Box F1 at 0.3 | Unmatched predicted/true | Coverage IoG 0.5 | Coverage IoG 0.7 | Rates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 31 fixed phrases, top box | 141 | 132 | 60 | 0.4255 | 0.4545 | 0.4396 | 0.5128 | 81/72 | 0.500 | 0.348 |  no box 0.021, no visible evidence 0.000, GroundingDINO 0.819, fallback 0.160 |
| 32 written phrases, top box | 94 | 132 | 47 | 0.5000 | 0.3561 | 0.4159 | 0.4513 | 47/85 | 0.386 | 0.288 |  no box 0.347, no visible evidence 0.340, GroundingDINO 0.611, fallback 0.042 |

**Experiment 33.** Top-box F1 at 0.5: fixed 0.4396, written 0.4159 -> phrase method **fixed**.

| System | Predicted boxes | True boxes | Matched at 0.5 | Box precision | Box recall | Box F1 at 0.5 | Box F1 at 0.3 | Unmatched predicted/true | Coverage IoG 0.5 | Coverage IoG 0.7 | Rates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 34 GroundingDINO only, top box | 118 | 132 | 57 | 0.4831 | 0.4318 | 0.4560 | 0.5360 | 61/75 | 0.477 | 0.333 |  no box 0.181, no visible evidence 0.000, GroundingDINO 0.819, fallback 0.000 |
| 35 DETR + OpenCLIP only, top box | 138 | 132 | 40 | 0.2899 | 0.3030 | 0.2963 | 0.3704 | 98/92 | 0.318 | 0.227 |  no box 0.042, no visible evidence 0.000, GroundingDINO 0.000, fallback 0.958 |
| 36 both, as designed, top box | 141 | 132 | 60 | 0.4255 | 0.4545 | 0.4396 | 0.5128 | 81/72 | 0.500 | 0.348 |  no box 0.021, no visible evidence 0.000, GroundingDINO 0.819, fallback 0.160 |
| 36 both, up to 5 boxes per category (reported separately, never compared with single-pass) | 175 | 132 | 65 | 0.3714 | 0.4924 | 0.4235 | 0.4886 | 110/67 | 0.545 | 0.394 |  |

**Experiment 37.** Single-pass boxes, same scoring (one box per category when present is true and the box is 4 integers inside the image).

| System | Predicted boxes | True boxes | Matched at 0.5 | Box precision | Box recall | Box F1 at 0.5 | Box F1 at 0.3 | Unmatched predicted/true | Coverage IoG 0.5 | Coverage IoG 0.7 | Rates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Single-pass qwen3.5:9b | 27 | 132 | 6 | 0.2222 | 0.0455 | 0.0755 | 0.1006 | 21/126 | 0.061 | 0.053 |  |
| Single-pass qwen3.5:27b | 30 | 132 | 4 | 0.1333 | 0.0303 | 0.0494 | 0.0988 | 26/128 | 0.038 | 0.038 |  |
| Single-pass gemma4:31b | 39 | 132 | 1 | 0.0256 | 0.0076 | 0.0117 | 0.0351 | 38/131 | 0.030 | 0.008 |  |
| Single-pass mistral-small3.2:24b | 55 | 132 | 2 | 0.0364 | 0.0152 | 0.0214 | 0.1176 | 53/130 | 0.030 | 0.015 |  |
| Single-pass ministral-3:14b | 63 | 132 | 5 | 0.0794 | 0.0379 | 0.0513 | 0.1641 | 58/127 | 0.053 | 0.038 |  |
| Single-pass qwen3-vl:32b | 46 | 132 | 6 | 0.1304 | 0.0455 | 0.0674 | 0.1348 | 40/126 | 0.053 | 0.023 |  |

**Experiment 38.** OpenCLIP image-crop to phrase similarity for fallback boxes (reported only): n 23, mean 0.226, min 0.182, max 0.287.

### Calibration 500 (copied from `reports\calibration.md`, numbers in `results\e45.json`)


| System | Predicted boxes | True boxes | Matched at 0.5 | Box precision | Box recall | Box F1 at 0.5 | Box F1 at 0.3 | Unmatched predicted/true | Coverage IoG 0.5 | Coverage IoG 0.7 | Rates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE top box | 281 | 470 | 112 | 0.3986 | 0.2383 | 0.2983 | 0.3169 | 169/358 | 0.260 | 0.247 |  no box 0.000, no visible evidence 0.000, GroundingDINO 0.932, fallback 0.068 |
| GROVE up to 5 boxes | 463 | 470 | 164 | 0.3542 | 0.3489 | 0.3516 | 0.3666 | 299/306 | 0.370 | 0.353 |  |
| single-pass qwen3.5:27b | 398 | 470 | 6 | 0.0151 | 0.0128 | 0.0138 | 0.0438 | 392/464 | 0.057 | 0.026 |  |
| single-pass gemma4:31b | 422 | 470 | 2 | 0.0047 | 0.0043 | 0.0045 | 0.0157 | 420/468 | 0.032 | 0.021 |  |


### Final 1,000 (`results\e54_final.json`, `criteria.secondary_top_box`)

| System | Box F1 at 0.5 | Box precision at 0.5 | Box recall at 0.5 | Box F1 at 0.3 |
|---|---:|---:|---:|---:|
| GROVE top box | 0.3333 | 0.4396 | 0.2685 | 0.3514 |
| best single-pass top box | 0.0036 | 0.0038 | 0.0034 | 0.0178 |
| GROVE up to 5 boxes (reported separately, never compared) | 0.3887 | 0.4024 | 0.3758 | 0.4060 |

### Sensitivity analysis (D18, D23): single-pass boxes read as 0-1000 grid coordinates (copied from `reports\box_rescale.md`; intervals from `reports\intervals_addendum.md`)

#### 203 development images (Fall, Electrical, PPE)

Images 203; true boxes 132.

| System | Boxes | Fit pixel rule as written | Fit only as 0-1000 grid | Fit neither | Rescaled row | Top-box F1 at 0.5, as written | at 0.5, rescaled | at 0.3, as written | at 0.3, rescaled |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| **GROVE top box** (stored) | - | - | - | - | - | 0.4396 | - | 0.5128 | - |
| single-pass qwen3.5:9b | 102 | 27 | 75 | 0 | trusted (74% grid only) | 0.0755 | 0.3761 | 0.1006 | 0.4530 |
| single-pass qwen3.5:27b | 88 | 30 | 58 | 0 | trusted (66% grid only) | 0.0494 | 0.2909 | 0.0988 | 0.3818 |
| single-pass gemma4:31b | 110 | 39 | 71 | 0 | trusted (65% grid only) | 0.0117 | 0.0909 | 0.0351 | 0.2314 |
| single-pass mistral-small3.2:24b | 58 | 55 | 3 | 0 | not trusted (5% grid only) | 0.0214 | 0.0000 | 0.1176 | 0.0432 |
| single-pass ministral-3:14b | 66 | 63 | 3 | 0 | not trusted (5% grid only) | 0.0513 | 0.0104 | 0.1641 | 0.0622 |
| single-pass qwen3-vl:32b | 124 | 46 | 78 | 0 | trusted (63% grid only) | 0.0674 | 0.2188 | 0.1348 | 0.2969 |


#### Calibration 500 (Fall, PPE)

Images 500; true boxes 470.

| System | Boxes | Fit pixel rule as written | Fit only as 0-1000 grid | Fit neither | Rescaled row | Top-box F1 at 0.5, as written | at 0.5, rescaled | at 0.3, as written | at 0.3, rescaled |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| **GROVE top box** (stored) | - | - | - | - | - | 0.2983 | - | 0.3169 | - |
| single-pass qwen3.5:27b | 531 | 398 | 133 | 0 | not trusted (25% grid only) | 0.0138 | 0.2977 | 0.0438 | 0.3317 |
| single-pass gemma4:31b | 499 | 422 | 72 | 5 | not trusted (14% grid only) | 0.0045 | 0.0187 | 0.0157 | 0.0436 |

On these images most boxes fit both readings (qwen3.5:27b: 398 of 531, gemma4:31b: 422 of 499), so the counts cannot show which reading a model used; by the rule above those rows are not trusted.


#### Final 1,000 (Fall, PPE)

Images 1000; true boxes 894.

| System | Boxes | Fit pixel rule as written | Fit only as 0-1000 grid | Fit neither | Rescaled row | Top-box F1 at 0.5, as written | at 0.5, rescaled | at 0.3, as written | at 0.3, rescaled |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| **GROVE top box** (stored) | - | - | - | - | - | 0.3333 | - | 0.3514 | - |
| single-pass qwen3.5:27b | not run in experiment 52 (no model call allowed) | | | | | | | | |
| single-pass gemma4:31b | 968 | 788 | 175 | 5 | not trusted (18% grid only) | 0.0036 | 0.0108 | 0.0178 | 0.0302 |

On these images most boxes fit both readings (gemma4:31b: 786 of 968), so the counts cannot show which reading a model used; by the rule above those rows are not trusted.


### A. Top-box F1 at intersection over union 0.5, GROVE minus single-pass

Box F1 = 2 x matched / (predicted boxes + true boxes), recomputed in every draw from per-image counts. "Rescaled" uses the 0-1000 grid reading of `reports\box_rescale.md` and is shown only for trusted rows. As written is the frozen rule and the primary comparison.

| Set | Single-pass model | Reading | GROVE top-box F1 | Single-pass top-box F1 | GROVE minus single-pass (95% interval) |
|---|---|---|---:|---:|---|
| 203 development images | qwen3.5:9b | as written | 0.4396 | 0.0755 | +0.3641 [+0.2628, +0.4616] |
| 203 development images | qwen3.5:9b | rescaled | 0.4396 | 0.3761 | +0.0635 [-0.0253, +0.1514] |
| 203 development images | qwen3.5:27b | as written | 0.4396 | 0.0494 | +0.3902 [+0.3012, +0.4767] |
| 203 development images | qwen3.5:27b | rescaled | 0.4396 | 0.2909 | +0.1487 [+0.0652, +0.2373] |
| 203 development images | gemma4:31b | as written | 0.4396 | 0.0117 | +0.4279 [+0.3471, +0.5079] |
| 203 development images | gemma4:31b | rescaled | 0.4396 | 0.0909 | +0.3487 [+0.2703, +0.4292] |
| 203 development images | mistral-small3.2:24b | as written | 0.4396 | 0.0214 | +0.4182 [+0.3368, +0.5014] |
| 203 development images | mistral-small3.2:24b | rescaled | - | - | not trusted, no interval |
| 203 development images | ministral-3:14b | as written | 0.4396 | 0.0513 | +0.3883 [+0.2961, +0.4781] |
| 203 development images | ministral-3:14b | rescaled | - | - | not trusted, no interval |
| 203 development images | qwen3-vl:32b | as written | 0.4396 | 0.0674 | +0.3721 [+0.2672, +0.4742] |
| 203 development images | qwen3-vl:32b | rescaled | 0.4396 | 0.2188 | +0.2208 [+0.1292, +0.3189] |
| Calibration 500 | qwen3.5:27b | as written | 0.2983 | 0.0138 | +0.2844 [+0.2426, +0.3281] |
| Calibration 500 | qwen3.5:27b | rescaled | - | - | not trusted, no interval |
| Calibration 500 | gemma4:31b | as written | 0.2983 | 0.0045 | +0.2938 [+0.2530, +0.3367] |
| Calibration 500 | gemma4:31b | rescaled | - | - | not trusted, no interval |
| Final 1,000 | gemma4:31b | as written | 0.3333 | 0.0036 | +0.3298 [+0.2984, +0.3625] |
| Final 1,000 | gemma4:31b | rescaled | - | - | not trusted, no interval |

Groups: 203 203 images in 174 same-scene groups; cal 500 images in 496 near-copy groups; final 1000 images in 988 near-copy groups.


Post hoc upper bound for the single-pass boxes: `reports\box_upper_bound.md` (D24).

## 9. Speed and memory (Table 7)

Copied from `reports\speed.md` (numbers in `results\e56_speed.json`).

## Batch runs (seconds per image, valid responses)

| Experiment | File | Images | Valid | Mean seconds per image | Total hours |
|---|---|---:|---:|---:|---:|
| e09 | gemma4_31b__sp.jsonl | 203 | 203 | 4.02 | 0.23 |
| e09 | ministral-3_14b__sp.jsonl | 203 | 203 | 2.44 | 0.14 |
| e09 | mistral-small3.2_24b__sp.jsonl | 203 | 203 | 3.53 | 0.20 |
| e09 | qwen3-vl_32b__sp.jsonl | 203 | 202 | 51.95 | 2.98 |
| e09 | qwen3.5_27b__sp.jsonl | 203 | 203 | 5.30 | 0.30 |
| e09 | qwen3.5_9b__sp.jsonl | 203 | 203 | 2.23 | 0.13 |
| e10 | gemma4_31b__sp.jsonl | 20 | 20 | 4.09 | 0.02 |
| e10 | qwen3.5_27b__sp.jsonl | 20 | 20 | 5.11 | 0.03 |
| e10 | qwen3.5_9b__sp.jsonl | 20 | 20 | 2.09 | 0.01 |
| e11 | clef-flash_9b__m.jsonl | 203 | 203 | 0.54 | 0.03 |
| e11 | clef_27b__m.jsonl | 203 | 203 | 1.10 | 0.06 |
| e11 | d3_27b__m.jsonl | 203 | 203 | 2.51 | 0.14 |
| e11 | d3_9b__m.jsonl | 203 | 203 | 1.25 | 0.07 |
| e11 | pplx-decider_27b__m.jsonl | 203 | 201 | 1.23 | 0.07 |
| e12 | clef-flash_9b__h.jsonl | 203 | 203 | 0.80 | 0.05 |
| e12 | clef_27b__h.jsonl | 203 | 203 | 1.94 | 0.11 |
| e12 | d3_27b__h.jsonl | 203 | 203 | 9.91 | 0.56 |
| e12 | d3_9b__h.jsonl | 203 | 203 | 4.90 | 0.28 |
| e12 | pplx-decider_27b__h.jsonl | 203 | 203 | 2.35 | 0.13 |
| e13 | clef-flash_9b__S0.jsonl | 203 | 203 | 0.60 | 0.03 |
| e13 | clef_27b__S0.jsonl | 203 | 203 | 1.31 | 0.07 |
| e13 | d3_27b__S0.jsonl | 203 | 203 | 4.35 | 0.25 |
| e13 | d3_9b__S0.jsonl | 203 | 203 | 2.16 | 0.12 |
| e13 | pplx-decider_27b__S0.jsonl | 203 | 203 | 1.56 | 0.09 |
| e23_rep1 | d3_27b__h.jsonl | 203 | 203 | 9.87 | 0.56 |
| e23_rep2 | d3_27b__h.jsonl | 203 | 203 | 9.87 | 0.56 |
| e31_32_phrases | qwen3.5_9b__phrase.jsonl | 144 | 144 | 0.63 | 0.03 |
| e40 | d3_27b__h.jsonl | 500 | 500 | 17.44 | 2.42 |
| e41 | d3_27b__m.jsonl | 500 | 500 | 4.42 | 0.61 |
| e42 | pplx-decider_27b__h.jsonl | 500 | 500 | 3.00 | 0.42 |
| e43 | gemma4_31b__sp.jsonl | 500 | 500 | 4.77 | 0.66 |
| e43 | qwen3.5_27b__sp.jsonl | 500 | 500 | 6.21 | 0.86 |
| e50 | d3_27b__h.jsonl | 1000 | 1000 | 17.61 | 4.89 |
| e51 | d3_27b__m.jsonl | 1000 | 1000 | 4.47 | 1.24 |
| e52 | gemma4_31b__sp.jsonl | 1000 | 1000 | 4.76 | 1.32 |

## Peak graphics memory (MiB, sampled every minute by nvidia-smi)

- e09|gemma4:31b: 25071
- e09|ministral-3:14b: 14915
- e09|mistral-small3.2:24b: 20933
- e09|qwen3-vl:32b: 32663
- e09|qwen3.5:27b: 19877
- e09|qwen3.5:9b: 8587
- e10|gemma4:31b: 24789
- e10|qwen3.5:27b: 19495
- e10|qwen3.5:9b: 8253
- e11|clef-flash:9b: 14452
- e11|clef:27b: 25292
- e11|d3:27b: 31840
- e11|d3:9b: 11864
- e11|pplx-decider:27b: 21096
- e12|clef-flash:9b: 14468
- e12|clef:27b: 25316
- e12|d3:27b: 31866
- e12|d3:9b: 11878
- e12|pplx-decider:27b: 21098
- e13|clef-flash:9b: 14456
- e13|clef:27b: 25298
- e13|d3:27b: 31840
- e13|d3:9b: 11864
- e13|pplx-decider:27b: 21098
- e23_rep1|d3:27b: 31866
- e23_rep2|d3:27b: 31866
- e31_32_phrases|qwen3.5:9b: 16908
- e40|d3:27b: 32150
- e41|d3:27b: 32150
- e42|pplx-decider:27b: 21406
- e43|gemma4:31b: 25346
- e43|qwen3.5:27b: 20156
- e50|d3:27b: 32161
- e51|d3:27b: 32150
- e52|gemma4:31b: 25352
- |: 31840

## Single-image speed of the whole GROVE pipeline (20 calibration images, one at a time)

- Seconds per image with models loaded: mean 19.12, max 29.95.
- main model h: {'model': 'd3:27b', 'first_call_seconds': 24.38, 'warm_median_seconds': 18.499, 'load_seconds_estimate': 5.881}
- grounding models: {'load_seconds': 2.1340794563293457}

Batch speed is not single-image speed: batch runs keep one model loaded for the whole set.

## 10. Completion

Copied from `reports\FINAL_RESULTS.md`.

- e09/gemma4_31b__sp.jsonl: 203 terminal, {'valid': 203}
- e09/ministral-3_14b__sp.jsonl: 203 terminal, {'valid': 203}
- e09/mistral-small3.2_24b__sp.jsonl: 203 terminal, {'valid': 203}
- e09/qwen3-vl_32b__sp.jsonl: 203 terminal, {'valid': 202, 'cut_off': 1}
- e09/qwen3.5_27b__sp.jsonl: 203 terminal, {'valid': 203}
- e09/qwen3.5_9b__sp.jsonl: 203 terminal, {'valid': 203}
- e10/gemma4_31b__sp.jsonl: 20 terminal, {'valid': 20}
- e10/qwen3.5_27b__sp.jsonl: 20 terminal, {'valid': 20}
- e10/qwen3.5_9b__sp.jsonl: 20 terminal, {'valid': 20}
- e11/clef-flash_9b__m.jsonl: 203 terminal, {'valid': 203}
- e11/clef_27b__m.jsonl: 203 terminal, {'valid': 203}
- e11/d3_27b__m.jsonl: 203 terminal, {'valid': 203}
- e11/d3_9b__m.jsonl: 203 terminal, {'valid': 203}
- e11/pplx-decider_27b__m.jsonl: 203 terminal, {'valid': 201, 'call_failure': 2}
- e12/clef-flash_9b__h.jsonl: 203 terminal, {'valid': 203}
- e12/clef_27b__h.jsonl: 203 terminal, {'valid': 203}
- e12/d3_27b__h.jsonl: 203 terminal, {'valid': 203}
- e12/d3_9b__h.jsonl: 203 terminal, {'valid': 203}
- e12/pplx-decider_27b__h.jsonl: 203 terminal, {'valid': 203}
- e13/clef-flash_9b__S0.jsonl: 203 terminal, {'valid': 203}
- e13/clef_27b__S0.jsonl: 203 terminal, {'valid': 203}
- e13/d3_27b__S0.jsonl: 203 terminal, {'valid': 203}
- e13/d3_9b__S0.jsonl: 203 terminal, {'valid': 203}
- e13/pplx-decider_27b__S0.jsonl: 203 terminal, {'valid': 203}
- e23_rep1/d3_27b__h.jsonl: 203 terminal, {'valid': 203}
- e23_rep2/d3_27b__h.jsonl: 203 terminal, {'valid': 203}
- e31_32_phrases/qwen3.5_9b__phrase.jsonl: 144 terminal, {'valid': 144}
- e40/d3_27b__h.jsonl: 500 terminal, {'valid': 500}
- e41/d3_27b__m.jsonl: 500 terminal, {'valid': 500}
- e42/pplx-decider_27b__h.jsonl: 500 terminal, {'valid': 500}
- e43/gemma4_31b__sp.jsonl: 500 terminal, {'valid': 500}
- e43/qwen3.5_27b__sp.jsonl: 500 terminal, {'valid': 500}
- e50/d3_27b__h.jsonl: 1000 terminal, {'valid': 1000}
- e51/d3_27b__m.jsonl: 1000 terminal, {'valid': 1000}
- e52/gemma4_31b__sp.jsonl: 1000 terminal, {'valid': 1000}
- e56_d3_27b_h/d3_27b__h.jsonl: 20 terminal, {'valid': 20}


