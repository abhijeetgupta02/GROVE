# Interval addendum (offline, after final scoring)

Written 2026-11-10T10:52:24 by `code\offline_20261110.py intervals` (D23). Paired bootstrap, 4000 draws, seed 20260422, resampled by same-scene group on the 203 images and by near-copy group on the calibration and final images (every other image is its own group), the same resampling code as the run (`grove_score._wmat`). No model call; no threshold, model or setting refit or changed. Intervals are 95% percentile intervals.

## A. Top-box F1 at intersection over union 0.5, GROVE minus single-pass

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

## B. False alarms per 100 negative images, 203 images (Fall, Electrical, PPE)

GROVE and main questions: held-out predictions (10 repeats of 5 grouped folds, seed 20260422, thresholds fit on training folds only), averaged over repeats, exactly as in `reports\screening.md`. Single-pass: fixed answers. Negative images: no scored violation (111 of 203).

| Comparison | GROVE | Other system | GROVE minus other (95% interval) |
|---|---:|---:|---|
| GROVE minus main questions only (m), d3:27b | 17.7 | 18.5 | -0.7 [-6.6, +4.7] |
| GROVE minus best single-pass, gemma4:31b (experiment 46 choice, frozen) | 17.7 | 16.2 | +1.5 [-4.9, +7.3] |
| GROVE minus single-pass qwen3.5:27b (highest micro-F1 on the 203) | 17.7 | 3.6 | +14.1 [+6.2, +22.2] |

Check: GROVE 17.7, main questions 18.5 per 100 negatives, the same values as `reports\screening.md`.

