# Removing one part at a time, 203 images (experiments 16 to 21)

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
