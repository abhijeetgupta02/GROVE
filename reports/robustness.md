# Robustness on the 203 images (experiments 24 to 30)

Generated 2026-11-06T15:27:56. GROVE = d3:27b (Electrical formula of d3:27b). Main-question model = m set of d3:27b. Best single-pass in experiment 9 = qwen3.5:27b.

## Experiment 24. 3, 4 and 7 categories (decision models only)

| Decision model | 3 categories (h formula) | 4 categories (h formula + Housekeeping) | 7 categories (S0, raw) |
|---|---:|---:|---:|
| clef:27b | 0.7448 | 0.7334 | 0.6119 |
| clef-flash:9b | 0.7383 | 0.7010 | 0.6138 |
| pplx-decider:27b | 0.7685 | 0.7239 | 0.6237 |
| d3:9b | 0.7140 | 0.6973 | 0.6236 |
| d3:27b | 0.7862 | 0.7591 | 0.6434 |

Positive pairs: 3 categories 125, 4 categories 173, 7 categories 210.

## Experiment 25. Fall and protective equipment only

| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE | 1.000 | 90.4/31.6/10.6 | 0.7410 | 0.8950 | 0.8108 | 0.8067 | 0.831 / 0.783 | 19.2 | - |  |
| Main-question model | 1.000 | 82.8/28.2/18.2 | 0.7459 | 0.8198 | 0.7811 | 0.7803 | 0.784 / 0.776 | 18.1 | - |  |
| Single-pass qwen3.5:27b | 1.000 | 60.0/12.0/41.0 | 0.8333 | 0.5941 | 0.6936 | 0.6958 | 0.674 / 0.718 | 1.6 | - |  |

## Experiment 26. Excluding the 29 AI-tagged images

| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, Electrical, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE | 1.000 | 73.2/31.0/19.8 | 0.7025 | 0.7871 | 0.7424 | 0.6923 | 0.819 / 0.545 / 0.713 | 16.9 | - |  |
| Main-question model | 1.000 | 69.1/32.0/23.9 | 0.6835 | 0.7430 | 0.7120 | 0.6533 | 0.768 / 0.449 / 0.743 | 18.2 | - |  |
| Single-pass qwen3.5:27b | 1.000 | 55.0/12.0/38.0 | 0.8209 | 0.5914 | 0.6875 | 0.6610 | 0.704 / 0.560 / 0.719 | 2.8 | - |  |

## Experiment 27. Duplicate file 79 removed

| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, Electrical, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE | 1.000 | 105.2/37.4/19.8 | 0.7377 | 0.8416 | 0.7862 | 0.7565 | 0.834 / 0.653 / 0.783 | 17.9 | - |  |
| Main-question model | 1.000 | 97.1/36.1/27.9 | 0.7290 | 0.7768 | 0.7521 | 0.7264 | 0.785 / 0.623 / 0.772 | 18.6 | - |  |
| Single-pass qwen3.5:27b | 1.000 | 73.0/15.0/52.0 | 0.8295 | 0.5840 | 0.6854 | 0.6805 | 0.674 / 0.650 / 0.718 | 3.6 | - |  |

## Experiment 28. Each file block held out (thresholds fit on the other blocks)

| System | Pooled micro-F1 | Block 1-35 | Block 36-80 | Block 81-107 | Block 108-170 | Block 171-203 |
|---|---:|---:|---:|---:|---:|---:|
| GROVE | 0.7480 | 0.8235 | 0.4286 | 0.0000 | 0.7167 | 0.9070 |
| Main-question model | 0.7251 | 0.6250 | 0.4286 | 0.0000 | 0.7438 | 0.8642 |

## Experiment 29a. Negatives = all 111 images without a scored label (98 unlabeled + 13 labeled only with removed categories in the full set)

| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, Electrical, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE | 1.000 | 105.2/37.4/19.8 | 0.7377 | 0.8416 | 0.7862 | 0.7565 | 0.834 / 0.653 / 0.783 | 17.7 | - |  |
| Main-question model | 1.000 | 97.1/36.1/27.9 | 0.7290 | 0.7768 | 0.7521 | 0.7264 | 0.785 / 0.623 / 0.772 | 18.5 | - |  |
| Single-pass qwen3.5:27b | 1.000 | 73.0/15.0/52.0 | 0.8295 | 0.5840 | 0.6854 | 0.6805 | 0.674 / 0.650 / 0.718 | 3.6 | - |  |

## Experiment 29b. Negatives = only the images with no label at all (the 13 labeled only with removed categories are left out)

| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, Electrical, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE | 1.000 | 105.6/37.1/19.4 | 0.7400 | 0.8448 | 0.7889 | 0.7575 | 0.836 / 0.644 / 0.792 | 18.6 | - |  |
| Main-question model | 1.000 | 96.8/34.0/28.2 | 0.7401 | 0.7744 | 0.7568 | 0.7317 | 0.786 / 0.626 / 0.783 | 18.3 | - |  |
| Single-pass qwen3.5:27b | 1.000 | 73.0/13.0/52.0 | 0.8488 | 0.5840 | 0.6919 | 0.6860 | 0.681 / 0.650 / 0.727 | 2.0 | - |  |

## Experiment 30a. Grouped folds (same-scene groups)

| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, Electrical, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE | 1.000 | 105.2/37.4/19.8 | 0.7377 | 0.8416 | 0.7862 | 0.7565 | 0.834 / 0.653 / 0.783 | 17.7 | - |  |
| Main-question model | 1.000 | 97.1/36.1/27.9 | 0.7290 | 0.7768 | 0.7521 | 0.7264 | 0.785 / 0.623 / 0.772 | 18.5 | - |  |
| Single-pass qwen3.5:27b | 1.000 | 73.0/15.0/52.0 | 0.8295 | 0.5840 | 0.6854 | 0.6805 | 0.674 / 0.650 / 0.718 | 3.6 | - |  |

## Experiment 30b. Plain random folds (no groups)

| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, Electrical, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE | 1.000 | 105.1/37.7/19.9 | 0.7360 | 0.8408 | 0.7849 | 0.7586 | 0.830 / 0.668 / 0.778 | 17.7 | - |  |
| Main-question model | 1.000 | 97.1/36.7/27.9 | 0.7257 | 0.7768 | 0.7504 | 0.7286 | 0.780 / 0.641 / 0.766 | 18.6 | - |  |
| Single-pass qwen3.5:27b | 1.000 | 73.0/15.0/52.0 | 0.8295 | 0.5840 | 0.6854 | 0.6805 | 0.674 / 0.650 / 0.718 | 3.6 | - |  |

