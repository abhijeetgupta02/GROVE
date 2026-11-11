# Grounding on the 203 images (experiments 31 to 38)

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
