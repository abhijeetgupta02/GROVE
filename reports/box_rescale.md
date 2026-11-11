# Single-pass boxes read as 0-1000 grid coordinates (sensitivity analysis, not the primary result)

Written 2026-11-10T10:52:13 by `code\offline_20261110.py box` (D23), after final scoring. **Sensitivity analysis only (planned as D18 before any full-run box score existed). The primary result is unchanged:** a single-pass box counts only if it is 4 integers inside the image in pixels, as the frozen rule says. No model was called; nothing in runs, freeze or lists was changed; no threshold or setting was refit.

- `code\box_rescale.py` was run first, unchanged; its full output is `reports\box_rescale_sensitivity.md`. This report adds the fit counts, the trust rule and GROVE's top box beside each row.
- **Boxes:** single-pass answers with present = true (each carries one raw box). **Fit pixel rule as written:** 4 integers with 0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height. **Fit only as 0-1000 grid:** fails the pixel rule but fits 0 <= x1 < x2 <= 1000 and 0 <= y1 < y2 <= 1000. **Fit neither:** fails both (including empty or malformed boxes).
- **Rescaled:** every box that fits the grid reading (including boxes that also fit the pixel rule) is converted to pixels as x * width / 1000, y * height / 1000 of the image the model was sent; all other boxes count as no box.
- **Trust rule:** a rescaled row is trusted only when most of that model's boxes in that set (more than half) fit only the grid reading. A box that fits both readings is no evidence either way, so it does not count towards trust. Rows that fail the rule are marked "not trusted"; their rescaled numbers are shown but should not be used.
- **Scoring:** top box against top box, one-to-one within each image and category, intersection over union 0.5 (primary) and 0.3, the same matching as experiments 37, 45 and 54. GROVE's top box is the stored result (unchanged).

## 203 development images (Fall, Electrical, PPE)

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

## Calibration 500 (Fall, PPE)

Images 500; true boxes 470.

| System | Boxes | Fit pixel rule as written | Fit only as 0-1000 grid | Fit neither | Rescaled row | Top-box F1 at 0.5, as written | at 0.5, rescaled | at 0.3, as written | at 0.3, rescaled |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| **GROVE top box** (stored) | - | - | - | - | - | 0.2983 | - | 0.3169 | - |
| single-pass qwen3.5:27b | 531 | 398 | 133 | 0 | not trusted (25% grid only) | 0.0138 | 0.2977 | 0.0438 | 0.3317 |
| single-pass gemma4:31b | 499 | 422 | 72 | 5 | not trusted (14% grid only) | 0.0045 | 0.0187 | 0.0157 | 0.0436 |

On these images most boxes fit both readings (qwen3.5:27b: 398 of 531, gemma4:31b: 422 of 499), so the counts cannot show which reading a model used; by the rule above those rows are not trusted.

## Final 1,000 (Fall, PPE)

Images 1000; true boxes 894.

| System | Boxes | Fit pixel rule as written | Fit only as 0-1000 grid | Fit neither | Rescaled row | Top-box F1 at 0.5, as written | at 0.5, rescaled | at 0.3, as written | at 0.3, rescaled |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| **GROVE top box** (stored) | - | - | - | - | - | 0.3333 | - | 0.3514 | - |
| single-pass qwen3.5:27b | not run in experiment 52 (no model call allowed) | | | | | | | | |
| single-pass gemma4:31b | 968 | 788 | 175 | 5 | not trusted (18% grid only) | 0.0036 | 0.0108 | 0.0178 | 0.0302 |

On these images most boxes fit both readings (gemma4:31b: 786 of 968), so the counts cannot show which reading a model used; by the rule above those rows are not trusted.

## Reading

- The as-written single-pass top-box F1 values match the stored experiment 37, 45 and 54 results (checked by `code\box_rescale.py`).
- Not trusted rows are reported for completeness only. Interval estimates for trusted rows are in `reports\intervals_addendum.md`.

