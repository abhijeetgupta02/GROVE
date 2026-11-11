# Screening on the 203 images (experiments 9, 11, 12, 13, 14, 15)

Generated 2026-11-06T14:15:44. Held-out scores: 10 repeats of 5 grouped folds (seed 20260422), thresholds fit on training folds only. Single-pass models give fixed answers (no thresholds). A failed response counts as no prediction.

## Table 2. Model screening, Fall, Electrical, PPE

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

## Gain from fact questions and the formula, same model (h formula minus m main questions)

| Model | Micro-F1 m | Micro-F1 h | Difference (95% interval, paired bootstrap by scene group) |
|---|---:|---:|---|
| clef:27b | 0.7667 | 0.7448 | -0.0218 [-0.0587, +0.0138] |
| clef-flash:9b | 0.7024 | 0.7383 | +0.0359 [-0.0050, +0.0778] |
| pplx-decider:27b | 0.6970 | 0.7685 | +0.0715 [+0.0275, +0.1165] |
| d3:9b | 0.6240 | 0.7140 | +0.0901 [+0.0543, +0.1287] |
| d3:27b | 0.7521 | 0.7862 | +0.0341 [-0.0020, +0.0708] |

## GROVE against single-pass models

- GROVE minus qwen3.5:27b: +0.1008 [+0.0283, +0.1751]
- GROVE minus gemma4:31b: +0.1054 [+0.0513, +0.1625]
- GROVE minus qwen3.5:9b: +0.1431 [+0.0801, +0.2050]
- GROVE minus qwen3-vl:32b: +0.1597 [+0.0999, +0.2269]
- GROVE minus ministral-3:14b: +0.2836 [+0.1900, +0.3774]
- GROVE minus mistral-small3.2:24b: +0.3272 [+0.2414, +0.4155]
- Valid-only sensitivity (203 images where both are valid), GROVE minus qwen3.5:27b: +0.1008 [+0.0283, +0.1751]

## Selection (experiment 14)

- Selected: **d3:27b** for Fall and PPE, Electrical from **formula of d3:27b** (held-out micro-F1 0.7862, 1 model(s), 9.9 s per image).
- Runner-up main model (second-best decision model): pplx-decider:27b.
- Excluded (failed): none

| Main model | Electrical source | Held-out micro-F1 | Models | Seconds per image |
|---|---|---:|---:|---:|
| d3:27b | S0(d3:9b) | 0.7888 | 2 | 12.1 |
| d3:27b | formula(d3:27b) | 0.7862 | 1 | 9.9 |
| d3:27b | m(d3:9b) | 0.7855 | 2 | 11.2 |
| d3:27b | S0(clef-flash:9b) | 0.7808 | 2 | 10.5 |
| d3:27b | S0(d3:27b) | 0.7807 | 1 | 14.3 |
| d3:27b | m(d3:27b) | 0.7805 | 1 | 12.4 |
| d3:27b | S0(pplx-decider:27b) | 0.7800 | 2 | 11.5 |
| d3:27b | m(pplx-decider:27b) | 0.7793 | 2 | 11.1 |
| pplx-decider:27b | S0(d3:9b) | 0.7788 | 2 | 4.5 |
| d3:27b | formula(pplx-decider:27b) | 0.7784 | 2 | 12.3 |
| d3:27b | formula(d3:9b) | 0.7782 | 2 | 14.8 |
| d3:27b | m(clef:27b) | 0.7766 | 2 | 11.0 |
| pplx-decider:27b | formula(d3:27b) | 0.7759 | 2 | 12.3 |
| pplx-decider:27b | m(d3:9b) | 0.7750 | 2 | 3.6 |
| d3:27b | formula(clef-flash:9b) | 0.7740 | 2 | 10.7 |
| pplx-decider:27b | S0(clef-flash:9b) | 0.7720 | 2 | 3.0 |
| d3:27b | m(clef-flash:9b) | 0.7718 | 2 | 10.5 |
| pplx-decider:27b | S0(d3:27b) | 0.7703 | 2 | 6.7 |
| d3:27b | S0(clef:27b) | 0.7703 | 2 | 11.2 |
| pplx-decider:27b | m(d3:27b) | 0.7703 | 2 | 4.9 |

Fold selection counts (pair chosen by the rule inside each of the 50 training folds): {"d3:27b + Electrical formula(d3:27b)": 16, "d3:27b + Electrical S0(d3:27b)": 11, "d3:27b + Electrical m(d3:27b)": 10, "pplx-decider:27b + Electrical m(pplx-decider:27b)": 2, "pplx-decider:27b + Electrical m(d3:9b)": 2, "pplx-decider:27b + Electrical S0(pplx-decider:27b)": 2, "pplx-decider:27b + Electrical m(clef:27b)": 1, "d3:27b + Electrical S0(pplx-decider:27b)": 1, "pplx-decider:27b + Electrical S0(d3:9b)": 1, "d3:27b + Electrical m(d3:9b)": 1, "clef:27b + Electrical S0(clef-flash:9b)": 1, "clef:27b + Electrical m(clef:27b)": 1, "clef:27b + Electrical m(d3:9b)": 1}
