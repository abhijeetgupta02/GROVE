# POST HOC: second single-pass baseline, qwen3.5:27b on the final 1,000

**Post hoc analysis** (D24). Written 2026-11-10T19:40:42 by `code\posthoc_partb.py second`. qwen3.5:27b was one of the two single-pass models carried to calibration (experiment 43); experiment 46 chose gemma4:31b as the best single-pass, so the run never called qwen3.5:27b on the final set. It was run after final scoring (`code\posthoc_runner.py`, `runs_posthoc\p06_final`) with the frozen single-pass prompt and the run's own code path, options, image encoding, retries and context: its config_hash equals that of its experiment 43 job (yes). Scored like experiment 54 (fixed answers, Fall and PPE); GROVE uses its frozen refit thresholds. Nothing was refit or changed.

Statuses: {'valid': 1000}.

| System | Micro-F1 [95% interval] | Precision | Recall | F1 Fall / PPE | False alarms per 100 negatives | Completion |
|---|---|---:|---:|---|---:|---:|
| GROVE (d3:27b, refit thresholds) | 0.7021 [0.6699, 0.7329] | 0.6777 | 0.7283 | 0.4398 / 0.7601 | 22.8 | 1.000 |
| single-pass qwen3.5:27b (post hoc) | 0.6076 [0.5814, 0.6333] | 0.4509 | 0.9311 | 0.3696 / 0.7074 | 71.8 | 1.000 |
| single-pass gemma4:31b (best single-pass, experiment 52) | 0.6423 [0.6131, 0.6698] | 0.4897 | 0.9331 | 0.4083 / 0.7254 | 71.6 | 1.000 |

## GROVE minus qwen3.5:27b (paired bootstrap, 4000 draws, seed 20260422, near-copy groups)

- Micro-F1: +0.0945 [+0.0651, +0.1252].
- Per category: Fall +0.0702 [-0.0131, +0.1520]; PPE +0.0528 [+0.0234, +0.0836].
- False alarms per 100 negative images: -49.0 [-55.6, -42.4].
- Valid-only (1000 images): +0.0945 [+0.0651, +0.1252].
- For reference, qwen3.5:27b minus gemma4:31b micro-F1: -0.0347 [-0.0517, -0.0182].
- Prevalence-standardized precision / F1: GROVE 0.2881 / 0.4129; qwen3.5:27b 0.1402 / 0.2437; gemma4:31b 0.1443 / 0.2499.

## Boxes, top box against top box

qwen3.5:27b boxes with present = true: 1049; fit the pixel rule as written 814, fit only as 0-1000 grid 235, fit neither 0 (rescaled rows are trusted only when more than half fit only the grid reading: not trusted).

| Cutoff | GROVE | qwen3.5:27b as written | qwen3.5:27b 0-1000 grid | GROVE minus as written (95% interval) | Upper bound reading | GROVE minus upper bound (95% interval) |
|---:|---:|---:|---:|---|---|---|
| 0.5 | 0.3333 | 0.0176 | 0.3253 | +0.3158 [+0.2843, +0.3487] | 0-1000 grid | +0.0081 [-0.0212, +0.0371] |
| 0.3 | 0.3514 | 0.0492 | 0.3654 | +0.3022 [+0.2689, +0.3367] | 0-1000 grid | -0.0140 [-0.0431, +0.0149] |

Numbers in `results_posthoc\second_baseline.json`.

