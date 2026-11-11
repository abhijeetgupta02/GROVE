# POST HOC: first-freeze thresholds on the calibration 500 and final 1,000

**Post hoc reporting** (D24 addendum), written 2026-11-10T14:05:56 by `code\posthoc_addendum.py firstfreeze`, after final scoring. GROVE and the main questions are scored with the first-freeze thresholds from `freeze\freeze_1.json` (fit on all 203 images, unchanged; GROVE Fall 0.12, PPE 0.50; main questions Fall 0.16, PPE 0.58). The design reports first-freeze thresholds as a sensitivity check (Section 7.6); the run saved only GROVE minus best single-pass for them on the final set. The refit thresholds remain primary. Single-pass models give fixed answers. qwen3.5:27b on the final set is the post hoc run `runs_posthoc\p06_final`. Paired bootstrap, 4000 draws, seed 20260422, near-copy groups. No model call, nothing refit.

Check: the calibration first-freeze micro-F1 equals the run's saved value in `results\e48.json` (GROVE yes, main questions yes).

## Final 1,000

| System | Thresholds | Micro-F1 [95% interval] | Precision | Recall | F1 Fall | F1 PPE | False alarms per 100 negatives | Completion |
|---|---|---|---:|---:|---:|---:|---:|---:|
| GROVE (d3:27b, h formula) | first-freeze | 0.4826 [0.4605, 0.5039] | 0.3215 | 0.9665 | 0.2054 | 0.7135 | 128.0 | 1.000 |
| main questions (d3:27b, m) | first-freeze | 0.5667 [0.5411, 0.5914] | 0.4120 | 0.9075 | 0.2793 | 0.7694 | 80.0 | 1.000 |
| single-pass gemma4:31b (fixed answers) | none (fixed) | 0.6423 [0.6131, 0.6698] | 0.4897 | 0.9331 | 0.4083 | 0.7254 | 71.6 | 1.000 |
| single-pass qwen3.5:27b (fixed answers) | none (fixed) | 0.6076 [0.5814, 0.6333] | 0.4509 | 0.9311 | 0.3696 | 0.7074 | 71.8 | 1.000 |

| Comparison (first-freeze thresholds) | Micro-F1 difference | Fall F1 difference | PPE F1 difference | False alarms per 100 negatives difference |
|---|---|---|---|---|
| GROVE minus single-pass gemma4:31b | -0.1597 [-0.1775, -0.1426] | -0.2029 [-0.2453, -0.1612] | -0.0119 [-0.0258, +0.0016] | +56.4 [+50.9, +61.7] |
| GROVE minus single-pass qwen3.5:27b | -0.1250 [-0.1416, -0.1093] | -0.1642 [-0.1957, -0.1319] | +0.0061 [-0.0094, +0.0215] | +56.2 [+50.3, +62.1] |
| main questions minus single-pass gemma4:31b | -0.0756 [-0.0941, -0.0563] | -0.1289 [-0.1661, -0.0917] | +0.0440 [+0.0230, +0.0657] | +8.4 [+3.1, +13.9] |
| main questions minus single-pass qwen3.5:27b | -0.0409 [-0.0573, -0.0233] | -0.0902 [-0.1169, -0.0632] | +0.0620 [+0.0395, +0.0853] | +8.2 [+2.4, +14.2] |

## Calibration 500 (not independent)

| System | Thresholds | Micro-F1 [95% interval] | Precision | Recall | F1 Fall | F1 PPE | False alarms per 100 negatives | Completion |
|---|---|---|---:|---:|---:|---:|---:|---:|
| GROVE (d3:27b, h formula) | first-freeze | 0.4798 [0.4473, 0.5116] | 0.3198 | 0.9606 | 0.2208 | 0.7033 | 133.6 | 1.000 |
| main questions (d3:27b, m) | first-freeze | 0.5401 [0.5032, 0.5749] | 0.3908 | 0.8740 | 0.2695 | 0.7627 | 82.8 | 1.000 |
| single-pass gemma4:31b (fixed answers) | none (fixed) | 0.6162 [0.5769, 0.6531] | 0.4649 | 0.9134 | 0.4036 | 0.7057 | 71.6 | 1.000 |
| single-pass qwen3.5:27b (fixed answers) | none (fixed) | 0.6038 [0.5663, 0.6389] | 0.4463 | 0.9331 | 0.3468 | 0.7225 | 72.0 | 1.000 |

| Comparison (first-freeze thresholds) | Micro-F1 difference | Fall F1 difference | PPE F1 difference | False alarms per 100 negatives difference |
|---|---|---|---|---|
| GROVE minus single-pass gemma4:31b | -0.1364 [-0.1592, -0.1132] | -0.1828 [-0.2316, -0.1321] | -0.0024 [-0.0235, +0.0190] | +62.0 [+54.3, +69.7] |
| GROVE minus single-pass qwen3.5:27b | -0.1240 [-0.1474, -0.1007] | -0.1260 [-0.1727, -0.0785] | -0.0192 [-0.0404, +0.0020] | +61.6 [+53.3, +69.7] |
| main questions minus single-pass gemma4:31b | -0.0761 [-0.1017, -0.0518] | -0.1340 [-0.1754, -0.0902] | +0.0571 [+0.0239, +0.0886] | +11.2 [+3.8, +18.8] |
| main questions minus single-pass qwen3.5:27b | -0.0637 [-0.0901, -0.0372] | -0.0772 [-0.1178, -0.0362] | +0.0402 [+0.0046, +0.0758] | +10.8 [+2.3, +19.0] |

Numbers in `results_posthoc\first_freeze_scores.json`.

