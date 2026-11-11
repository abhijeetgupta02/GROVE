# Single-pass box sensitivity: raw boxes read as 0-1000 grid coordinates

Written 2026-11-10T10:48:53 by code\box_rescale.py (main mode). **Sensitivity only.** The frozen rule (a box counts only if it is 4 integers inside the image in pixels) stays the primary result; nothing here changes any result, report, threshold, selection, freeze file or criterion.

- Rescaled: every answer with present = true whose raw box is 4 integers with 0 <= x1 < x2 <= 1000 and 0 <= y1 < y2 <= 1000 is converted to pixels as (x * width / 1000, y * height / 1000), using the size of the image the model was sent. Other boxes count as no box, as in the frozen rule.
- Scoring: the same one-to-one top-box matching as experiments 37, 45 and 54 (grove_score.box_eval), IoU 0.5 (primary) and 0.3, against the same true boxes (all boxes in the scored categories).
- As written: recomputed with the experiment code path (grove_stages.load_sp, then box_eval) and checked against the stored result.
- Final images: included (logs\final_scored.lock exists).
- code\box_rescale.py SHA-256 now fce603d9ec96b7f573ce1dd0b1f73932b60e38a28a134d5f68eb614ec260e461; in freeze_1.json code hashes: same; in freeze_2.json: same.

## 203 images (experiment 9; Fall, Electrical, PPE)

Images 203; true boxes 132.

| Model | Valid answers | Answers with present = true | Raw boxes inside the image as pixels | Raw boxes inside the 0-1000 grid | Inside both | Inside neither | Box F1 at 0.5, as written | Box F1 at 0.5, rescaled | Box F1 at 0.3, as written | Box F1 at 0.3, rescaled | Precision / recall at 0.5, as written | Precision / recall at 0.5, rescaled | As written equals stored result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.5:9b | 203 | 102 | 27 | 102 | 27 | 0 | 0.0755 | 0.3761 | 0.1006 | 0.4530 | 0.2222 / 0.0455 | 0.4314 / 0.3333 | yes |
| qwen3.5:27b | 203 | 88 | 30 | 88 | 30 | 0 | 0.0494 | 0.2909 | 0.0988 | 0.3818 | 0.1333 / 0.0303 | 0.3636 / 0.2424 | yes |
| gemma4:31b | 203 | 110 | 39 | 110 | 39 | 0 | 0.0117 | 0.0909 | 0.0351 | 0.2314 | 0.0256 / 0.0076 | 0.1000 / 0.0833 | yes |
| mistral-small3.2:24b | 203 | 58 | 55 | 53 | 50 | 0 | 0.0214 | 0.0000 | 0.1176 | 0.0432 | 0.0364 / 0.0152 | 0.0000 / 0.0000 | yes |
| ministral-3:14b | 203 | 66 | 63 | 61 | 58 | 0 | 0.0513 | 0.0104 | 0.1641 | 0.0622 | 0.0794 / 0.0379 | 0.0164 / 0.0076 | yes |
| qwen3-vl:32b | 202 | 124 | 46 | 124 | 46 | 0 | 0.0674 | 0.2188 | 0.1348 | 0.2969 | 0.1304 / 0.0455 | 0.2258 / 0.2121 | yes |

For reference (stored result, unchanged): GROVE top box F1 at 0.5 0.4396, at 0.3 0.5128.

## Calibration images (experiment 43; Fall, PPE)

Images 500; true boxes 470.

| Model | Valid answers | Answers with present = true | Raw boxes inside the image as pixels | Raw boxes inside the 0-1000 grid | Inside both | Inside neither | Box F1 at 0.5, as written | Box F1 at 0.5, rescaled | Box F1 at 0.3, as written | Box F1 at 0.3, rescaled | Precision / recall at 0.5, as written | Precision / recall at 0.5, rescaled | As written equals stored result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.5:9b | not run in experiment 43 | | | | | | | | | | | | |
| qwen3.5:27b | 500 | 531 | 398 | 531 | 398 | 0 | 0.0138 | 0.2977 | 0.0438 | 0.3317 | 0.0151 / 0.0128 | 0.2806 / 0.3170 | yes |
| gemma4:31b | 500 | 499 | 422 | 494 | 422 | 5 | 0.0045 | 0.0187 | 0.0157 | 0.0436 | 0.0047 / 0.0043 | 0.0182 / 0.0191 | yes |
| mistral-small3.2:24b | not run in experiment 43 | | | | | | | | | | | | |
| ministral-3:14b | not run in experiment 43 | | | | | | | | | | | | |
| qwen3-vl:32b | not run in experiment 43 | | | | | | | | | | | | |

For reference (stored result, unchanged): GROVE top box F1 at 0.5 0.2983, at 0.3 0.3169.

## Final images (experiment 52; Fall, PPE)

Images 1000; true boxes 894.

| Model | Valid answers | Answers with present = true | Raw boxes inside the image as pixels | Raw boxes inside the 0-1000 grid | Inside both | Inside neither | Box F1 at 0.5, as written | Box F1 at 0.5, rescaled | Box F1 at 0.3, as written | Box F1 at 0.3, rescaled | Precision / recall at 0.5, as written | Precision / recall at 0.5, rescaled | As written equals stored result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.5:9b | not run in experiment 52 | | | | | | | | | | | | |
| qwen3.5:27b | not run in experiment 52 | | | | | | | | | | | | |
| gemma4:31b | 1000 | 968 | 788 | 961 | 786 | 5 | 0.0036 | 0.0108 | 0.0178 | 0.0302 | 0.0038 / 0.0034 | 0.0104 / 0.0112 | yes |
| mistral-small3.2:24b | not run in experiment 52 | | | | | | | | | | | | |
| ministral-3:14b | not run in experiment 52 | | | | | | | | | | | | |
| qwen3-vl:32b | not run in experiment 52 | | | | | | | | | | | | |

For reference (stored result, unchanged): GROVE top box F1 at 0.5 0.3333, at 0.3 0.3514.

