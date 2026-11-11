# POST HOC: box upper bound for the single-pass baselines

**Post hoc analysis** (D24), written 2026-11-10T12:11:03 by `code\posthoc_parta.py upper` from saved outputs; no model call. For each single-pass model and set, the reading of its saved raw boxes that gives the higher top-box F1 (as written under the frozen pixel rule, or read as 0-1000 grid coordinates) is taken, whatever the trust rule of `reports\box_rescale.md` says. Choosing the better reading with the labels favours the baseline, so GROVE minus this is a conservative (lower-bound) comparison for GROVE. The primary result (frozen pixel rule) is unchanged.

- Top box against top box, one-to-one within image and category, intersection over union 0.5 (primary) and 0.3, as in experiments 37, 45 and 54. The reading is chosen separately at each cutoff, once on the full set (not again inside each bootstrap draw).
- Intervals: paired bootstrap, 4000 draws, seed 20260422, by same-scene group on the 203 and by near-copy group on the calibration and final images, the run's resampling code.
- qwen3.5:27b was not run on the final set by the run; its post hoc final-set run (Part B, step 6) is scored in `reports\posthoc_second_baseline.md`, with the same upper bound.

| Set | Single-pass model | Cutoff | GROVE top-box F1 | As written | 0-1000 grid | Reading taken | GROVE minus upper bound (95% interval) |
|---|---|---:|---:|---:|---:|---|---|
| 203 development images | qwen3.5:9b | 0.5 | 0.4396 | 0.0755 | 0.3761 | 0-1000 grid | +0.0635 [-0.0253, +0.1514] |
| 203 development images | qwen3.5:9b | 0.3 | 0.5128 | 0.1006 | 0.4530 | 0-1000 grid | +0.0598 [-0.0257, +0.1412] |
| 203 development images | qwen3.5:27b | 0.5 | 0.4396 | 0.0494 | 0.2909 | 0-1000 grid | +0.1487 [+0.0652, +0.2373] |
| 203 development images | qwen3.5:27b | 0.3 | 0.5128 | 0.0988 | 0.3818 | 0-1000 grid | +0.1310 [+0.0317, +0.2312] |
| 203 development images | gemma4:31b | 0.5 | 0.4396 | 0.0117 | 0.0909 | 0-1000 grid | +0.3487 [+0.2703, +0.4292] |
| 203 development images | gemma4:31b | 0.3 | 0.5128 | 0.0351 | 0.2314 | 0-1000 grid | +0.2814 [+0.1813, +0.3765] |
| 203 development images | mistral-small3.2:24b | 0.5 | 0.4396 | 0.0214 | 0.0000 | as written | +0.4182 [+0.3368, +0.5014] |
| 203 development images | mistral-small3.2:24b | 0.3 | 0.5128 | 0.1176 | 0.0432 | as written | +0.3952 [+0.2999, +0.4893] |
| 203 development images | ministral-3:14b | 0.5 | 0.4396 | 0.0513 | 0.0104 | as written | +0.3883 [+0.2961, +0.4781] |
| 203 development images | ministral-3:14b | 0.3 | 0.5128 | 0.1641 | 0.0622 | as written | +0.3487 [+0.2360, +0.4524] |
| 203 development images | qwen3-vl:32b | 0.5 | 0.4396 | 0.0674 | 0.2188 | 0-1000 grid | +0.2208 [+0.1292, +0.3189] |
| 203 development images | qwen3-vl:32b | 0.3 | 0.5128 | 0.1348 | 0.2969 | 0-1000 grid | +0.2159 [+0.1175, +0.3194] |
| Calibration 500 | qwen3.5:27b | 0.5 | 0.2983 | 0.0138 | 0.2977 | 0-1000 grid | +0.0006 [-0.0410, +0.0427] |
| Calibration 500 | qwen3.5:27b | 0.3 | 0.3169 | 0.0438 | 0.3317 | 0-1000 grid | -0.0148 [-0.0558, +0.0264] |
| Calibration 500 | gemma4:31b | 0.5 | 0.2983 | 0.0045 | 0.0187 | 0-1000 grid | +0.2796 [+0.2394, +0.3200] |
| Calibration 500 | gemma4:31b | 0.3 | 0.3169 | 0.0157 | 0.0436 | 0-1000 grid | +0.2733 [+0.2311, +0.3162] |
| Final 1,000 | gemma4:31b | 0.5 | 0.3333 | 0.0036 | 0.0108 | 0-1000 grid | +0.3226 [+0.2910, +0.3550] |
| Final 1,000 | gemma4:31b | 0.3 | 0.3514 | 0.0178 | 0.0302 | 0-1000 grid | +0.3212 [+0.2883, +0.3543] |

Same numbers in `results_posthoc\box_upper_bound.json`.

## Final set, qwen3.5:27b

**Post hoc** (D24 addendum), written 2026-11-10T14:05:54 by `code\posthoc_addendum.py boxv2`. qwen3.5:27b was run on the final 1,000 only after final scoring (`runs_posthoc\p06_final`, frozen single-pass prompt, same config_hash as its experiment 43 job). Boxes with present = true: 1049; fit the pixel rule as written 814, fit only as 0-1000 grid 235, fit neither 0. Same scoring, reading choice and bootstrap (4000 draws, seed 20260422, near-copy groups) as above; everything above this section is the unchanged content of `reports\box_upper_bound.md`.

| Cutoff | GROVE top-box F1 | qwen3.5:27b as written | qwen3.5:27b 0-1000 grid | GROVE minus as written (95% interval) | Better reading | GROVE minus better reading (95% interval) |
|---:|---:|---:|---:|---|---|---|
| 0.5 | 0.3333 | 0.0176 | 0.3253 | +0.3158 [+0.2843, +0.3487] | 0-1000 grid | +0.0081 [-0.0212, +0.0371] |
| 0.3 | 0.3514 | 0.0492 | 0.3654 | +0.3022 [+0.2689, +0.3367] | 0-1000 grid | -0.0140 [-0.0431, +0.0149] |

Numbers in `results_posthoc\box_upper_bound_v2_qwen_final.json`.

