# Calibration report, 500 new images (experiments 40 to 48)

Generated 2026-11-06T20:47:49. Fall and protective equipment only. These images tuned thresholds and choose the baseline, so they are not an independent test. Prevalence-standardized precision uses r = 0.1220 (tuning_sample natural violation rate) and is secondary.

## Frozen thresholds from the 203 images (first freeze)

| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE | 1.000 | 244.0/519.0/10.0 | 0.3198 | 0.9606 | 0.4798 | 0.4621 | 0.221 / 0.703 | 133.6 | 17.4 | prevalence-standardized P 0.0861 F1 0.1581 |
| main_question | 1.000 | 222.0/346.0/32.0 | 0.3908 | 0.8740 | 0.5401 | 0.5161 | 0.270 / 0.763 | 82.8 | 4.4 | prevalence-standardized P 0.1200 F1 0.2110 |
| variant_no_fact_questions | 1.000 | 222.0/346.0/32.0 | 0.3908 | 0.8740 | 0.5401 | 0.5161 | 0.270 / 0.763 | 82.8 | 4.4 | prevalence-standardized P 0.1200 F1 0.2110 |
| variant_no_protection | 1.000 | 244.0/531.0/10.0 | 0.3148 | 0.9606 | 0.4742 | 0.4593 | 0.215 / 0.703 | 134.8 | 17.4 | prevalence-standardized P 0.0852 F1 0.1565 |
| variant_no_worker | 1.000 | 242.0/496.0/12.0 | 0.3279 | 0.9528 | 0.4879 | 0.4751 | 0.221 / 0.729 | 126.4 | 17.4 | prevalence-standardized P 0.0898 F1 0.1641 |
| second_GROVE_questions | 1.000 | 241.0/505.0/13.0 | 0.3231 | 0.9488 | 0.4820 | 0.4837 | 0.207 / 0.761 | 123.6 | 3.0 | prevalence-standardized P 0.0906 F1 0.1654 |
| single-pass qwen3.5:27b | 1.000 | 237.0/294.0/17.0 | 0.4463 | 0.9331 | 0.6038 | 0.5347 | 0.347 / 0.723 | 72.0 | 6.2 | prevalence-standardized P 0.1439 F1 0.2494 |
| single-pass gemma4:31b | 1.000 | 232.0/267.0/22.0 | 0.4649 | 0.9134 | 0.6162 | 0.5546 | 0.404 / 0.706 | 71.6 | 4.8 | prevalence-standardized P 0.1443 F1 0.2492 |

- GROVE minus best single-pass (gemma4:31b), micro-F1: -0.1364 [-0.1592, -0.1132]; false alarms per 100 negatives: +62.00 [+54.32, +69.75] (paired bootstrap, 4,000 draws, near-copy groups).
- Valid-only sensitivity (500 images): -0.1364 [-0.1592, -0.1132]
- GROVE minus main-question model: -0.0603 [-0.0811, -0.0393]

## Thresholds refit once on these images (used on the final set)

| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (Fall, PPE) | False alarms per 100 negatives | Seconds per image | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE | 1.000 | 189.0/92.0/65.0 | 0.6726 | 0.7441 | 0.7065 | 0.6298 | 0.488 / 0.772 | 20.0 | 17.4 | prevalence-standardized P 0.3199 F1 0.4474 |
| main_question | 1.000 | 196.0/105.0/58.0 | 0.6512 | 0.7717 | 0.7063 | 0.6249 | 0.470 / 0.780 | 23.2 | 4.4 | prevalence-standardized P 0.2968 F1 0.4287 |
| variant_no_fact_questions | 1.000 | 196.0/105.0/58.0 | 0.6512 | 0.7717 | 0.7063 | 0.6249 | 0.470 / 0.780 | 23.2 | 4.4 | prevalence-standardized P 0.2968 F1 0.4287 |
| variant_no_protection | 1.000 | 191.0/100.0/63.0 | 0.6564 | 0.7520 | 0.7009 | 0.6265 | 0.481 / 0.772 | 20.8 | 17.4 | prevalence-standardized P 0.3115 F1 0.4405 |
| variant_no_worker | 1.000 | 190.0/95.0/64.0 | 0.6667 | 0.7480 | 0.7050 | 0.6285 | 0.488 / 0.769 | 21.2 | 17.4 | prevalence-standardized P 0.3097 F1 0.4381 |
| second_GROVE_questions | 1.000 | 178.0/66.0/76.0 | 0.7295 | 0.7008 | 0.7149 | 0.5234 | 0.257 / 0.790 | 19.2 | 3.0 | prevalence-standardized P 0.3288 F1 0.4475 |
| single-pass qwen3.5:27b | 1.000 | 237.0/294.0/17.0 | 0.4463 | 0.9331 | 0.6038 | 0.5347 | 0.347 / 0.723 | 72.0 | 6.2 | prevalence-standardized P 0.1439 F1 0.2494 |
| single-pass gemma4:31b | 1.000 | 232.0/267.0/22.0 | 0.4649 | 0.9134 | 0.6162 | 0.5546 | 0.404 / 0.706 | 71.6 | 4.8 | prevalence-standardized P 0.1443 F1 0.2492 |

- GROVE minus best single-pass (gemma4:31b), micro-F1: +0.0903 [+0.0521, +0.1285]; false alarms per 100 negatives: -51.60 [-59.92, -43.42] (paired bootstrap, 4,000 draws, near-copy groups).
- Valid-only sensitivity (500 images): +0.0903 [+0.0521, +0.1285]
- GROVE minus main-question model: +0.0002 [-0.0252, +0.0262]

#### Subgroups, GROVE, refit thresholds

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 483 | 0.7073 | 0.7595 | 20.0 |
| Hazard size below 1% of image (violation images) | 86 | 0.8302 | 0.7500 | 0.0 |
| Hazard size 1% to 10% (violation images) | 120 | 0.7563 | 0.7438 | 0.0 |
| Hazard size 10% or more (violation images) | 44 | 0.7500 | 0.7333 | 0.0 |
| camera_distance = long distance | 18 | 0.4000 | 0.2500 | 0.0 |
| camera_distance = mid distance | 369 | 0.7103 | 0.7344 | 16.6 |
| camera_distance = short distance | 113 | 0.7068 | 0.8103 | 36.4 |
| illumination = night | 37 | 0.5490 | 0.4000 | 0.0 |
| illumination = normal lighting | 388 | 0.7143 | 0.8011 | 22.5 |
| illumination = overexposed | 18 | 0.7368 | 0.8750 | 9.1 |
| illumination = underexposed | 57 | 0.7797 | 0.7667 | 7.1 |
| Rule-4-only negatives (false alarms) | 0 | - | - | - |

## Grounding on flagged categories (experiment 45, top box)

| System | Predicted boxes | True boxes | Matched at 0.5 | Box precision | Box recall | Box F1 at 0.5 | Box F1 at 0.3 | Unmatched predicted/true | Coverage IoG 0.5 | Coverage IoG 0.7 | Rates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GROVE top box | 281 | 470 | 112 | 0.3986 | 0.2383 | 0.2983 | 0.3169 | 169/358 | 0.260 | 0.247 |  no box 0.000, no visible evidence 0.000, GroundingDINO 0.932, fallback 0.068 |
| GROVE up to 5 boxes | 463 | 470 | 164 | 0.3542 | 0.3489 | 0.3516 | 0.3666 | 299/306 | 0.370 | 0.353 |  |
| single-pass qwen3.5:27b | 398 | 470 | 6 | 0.0151 | 0.0128 | 0.0138 | 0.0438 | 392/464 | 0.057 | 0.026 |  |
| single-pass gemma4:31b | 422 | 470 | 2 | 0.0047 | 0.0043 | 0.0045 | 0.0157 | 420/468 | 0.032 | 0.021 |  |

## Component sensitivity (experiment 47, reported only)

Thresholds fit with 5 grouped folds inside these images, held-out folds scored. This shows how much the score rests on these components, not the full effect of the definition difference. Night images: 37 (descriptive).

| Variant | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|
| GROVE | 0.6978 | 0.7362 | 21.2 |
| without f_ppe_novest | 0.7186 | 0.7992 | 26.8 |
| without f_fall_opening | 0.6629 | 0.6890 | 22.8 |
| night images only (GROVE) | 0.9722 | 1.0000 | 50.0 |
- illumination values: {'normal lighting': 388, 'underexposed': 57, 'night': 37, 'overexposed': 18}

## Response status (failure types)

- GROVE h: {'valid': 500}
- main m: {'valid': 500}
- single-pass qwen3.5:27b: {'valid': 500}
- single-pass gemma4:31b: {'valid': 500}
