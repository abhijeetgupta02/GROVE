# Experiments 57 to 59. Per-category results, subgroups, false alarms and prevalence-standardized precision

Intervals: paired bootstrap, 4,000 draws, seed 20260422, resampled by related-scene group.

## Calibration (500 images, not independent)

| System | Category | F1 (95% interval) | Precision | Recall |
|---|---|---|---:|---:|
| GROVE | Fall | 0.4878 [0.3731, 0.5865] | 0.4225 | 0.5769 |
| GROVE | PPE | 0.7718 [0.7260, 0.8145] | 0.7571 | 0.7871 |
| main_question | Fall | 0.4697 [0.3564, 0.5714] | 0.3875 | 0.5962 |
| main_question | PPE | 0.7801 [0.7342, 0.8227] | 0.7466 | 0.8168 |
| single-pass gemma4:31b | Fall | 0.4036 [0.3220, 0.4828] | 0.2632 | 0.8654 |
| single-pass gemma4:31b | PPE | 0.7057 [0.6610, 0.7486] | 0.5701 | 0.9257 |

| System | False alarms per 100 negative images | Prevalence-standardized precision (95% interval) | Prevalence-standardized F1 (95% interval) | Completion |
|---|---:|---|---|---:|
| GROVE | 20.0 | 0.3199 [0.2700, 0.3857] | 0.4474 [0.3924, 0.5105] | 1.000 |
| main_question | 23.2 | 0.2968 [0.2524, 0.3535] | 0.4287 [0.3783, 0.4872] | 1.000 |
| single-pass gemma4:31b | 71.6 | 0.1443 [0.1302, 0.1609] | 0.2492 [0.2275, 0.2742] | 1.000 |
- r = 0.1220 (natural violation rate of the main pool), p = 0.5000 in this sample. Top-up images count in their group, so this is performance standardized to that rate under the assumption that the pools are comparable within the violation and no-violation groups.

#### Subgroups, Calibration (500 images, not independent), GROVE

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

#### Subgroups, Calibration (500 images, not independent), main_question

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 483 | 0.6947 | 0.7679 | 23.2 |
| Hazard size below 1% of image (violation images) | 86 | 0.8941 | 0.8636 | 0.0 |
| Hazard size 1% to 10% (violation images) | 120 | 0.7521 | 0.7521 | 0.0 |
| Hazard size 10% or more (violation images) | 44 | 0.6824 | 0.6444 | 0.0 |
| camera_distance = long distance | 18 | 0.5714 | 0.5000 | 7.1 |
| camera_distance = mid distance | 369 | 0.7022 | 0.7552 | 21.0 |
| camera_distance = short distance | 113 | 0.7259 | 0.8448 | 34.5 |
| illumination = night | 37 | 0.5185 | 0.4000 | 0.0 |
| illumination = normal lighting | 388 | 0.7299 | 0.8508 | 24.9 |
| illumination = overexposed | 18 | 0.5556 | 0.6250 | 18.2 |
| illumination = underexposed | 57 | 0.7541 | 0.7667 | 14.3 |
| Rule-4-only negatives (false alarms) | 0 | - | - | - |

#### Subgroups, Calibration (500 images, not independent), single-pass gemma4:31b

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 483 | 0.5981 | 0.9072 | 71.6 |
| Hazard size below 1% of image (violation images) | 86 | 0.8615 | 0.9545 | 0.0 |
| Hazard size 1% to 10% (violation images) | 120 | 0.7914 | 0.9091 | 0.0 |
| Hazard size 10% or more (violation images) | 44 | 0.7525 | 0.8444 | 0.0 |
| camera_distance = long distance | 18 | 0.3750 | 0.7500 | 57.1 |
| camera_distance = mid distance | 369 | 0.6135 | 0.9010 | 70.7 |
| camera_distance = short distance | 113 | 0.6474 | 0.9655 | 78.2 |
| illumination = night | 37 | 0.6667 | 0.6571 | 0.0 |
| illumination = normal lighting | 388 | 0.6014 | 0.9503 | 73.7 |
| illumination = overexposed | 18 | 0.5333 | 1.0000 | 100.0 |
| illumination = underexposed | 57 | 0.7073 | 0.9667 | 50.0 |
| Rule-4-only negatives (false alarms) | 0 | - | - | - |

## Final test (1000 images)

| System | Category | F1 (95% interval) | Precision | Recall |
|---|---|---|---:|---:|
| GROVE | Fall | 0.4398 [0.3509, 0.5269] | 0.4375 | 0.4421 |
| GROVE | PPE | 0.7601 [0.7273, 0.7914] | 0.7289 | 0.7942 |
| main_question | Fall | 0.4216 [0.3333, 0.5025] | 0.3945 | 0.4526 |
| main_question | PPE | 0.7832 [0.7521, 0.8131] | 0.7372 | 0.8354 |
| single-pass gemma4:31b | Fall | 0.4083 [0.3440, 0.4700] | 0.2705 | 0.8316 |
| single-pass gemma4:31b | PPE | 0.7254 [0.6950, 0.7553] | 0.5843 | 0.9564 |

| System | False alarms per 100 negative images | Prevalence-standardized precision (95% interval) | Prevalence-standardized F1 (95% interval) | Completion |
|---|---:|---|---|---:|
| GROVE | 22.8 | 0.2881 [0.2555, 0.3276] | 0.4129 [0.3760, 0.4549] | 1.000 |
| main_question | 25.0 | 0.2799 [0.2493, 0.3157] | 0.4096 [0.3740, 0.4500] | 1.000 |
| single-pass gemma4:31b | 71.6 | 0.1443 [0.1334, 0.1563] | 0.2499 [0.2333, 0.2680] | 1.000 |
- r = 0.1180 (natural violation rate of the main pool), p = 0.5000 in this sample. Top-up images count in their group, so this is performance standardized to that rate under the assumption that the pools are comparable within the violation and no-violation groups.

#### Subgroups, Final test (1000 images), GROVE

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 942 | 0.6953 | 0.7378 | 22.8 |
| Hazard size below 1% of image (violation images) | 201 | 0.8571 | 0.7761 | 0.0 |
| Hazard size 1% to 10% (violation images) | 200 | 0.7725 | 0.7192 | 0.0 |
| Hazard size 10% or more (violation images) | 99 | 0.6869 | 0.6538 | 0.0 |
| camera_distance = long distance | 46 | 0.7647 | 0.7222 | 7.1 |
| camera_distance = mid distance | 727 | 0.6933 | 0.7046 | 20.9 |
| camera_distance = short distance | 227 | 0.7185 | 0.8017 | 33.3 |
| illumination = night | 58 | 0.5385 | 0.3889 | 0.0 |
| illumination = normal lighting | 794 | 0.7191 | 0.7775 | 23.2 |
| illumination = overexposed | 42 | 0.6047 | 0.6842 | 26.1 |
| illumination = underexposed | 106 | 0.7290 | 0.7358 | 20.4 |
| Rule-4-only negatives (false alarms) | 2 | 0.0000 | 0.0000 | 0.0 |

#### Subgroups, Final test (1000 images), main_question

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 942 | 0.6960 | 0.7556 | 25.0 |
| Hazard size below 1% of image (violation images) | 201 | 0.9171 | 0.8806 | 0.0 |
| Hazard size 1% to 10% (violation images) | 200 | 0.7853 | 0.7389 | 0.0 |
| Hazard size 10% or more (violation images) | 99 | 0.6354 | 0.5865 | 0.0 |
| camera_distance = long distance | 46 | 0.7778 | 0.7778 | 10.7 |
| camera_distance = mid distance | 727 | 0.7103 | 0.7507 | 24.5 |
| camera_distance = short distance | 227 | 0.7212 | 0.8017 | 30.6 |
| illumination = night | 58 | 0.5122 | 0.3889 | 0.0 |
| illumination = normal lighting | 794 | 0.7318 | 0.8141 | 26.0 |
| illumination = overexposed | 42 | 0.5714 | 0.6316 | 30.4 |
| illumination = underexposed | 106 | 0.7928 | 0.8302 | 16.7 |
| Rule-4-only negatives (false alarms) | 2 | 0.0000 | 0.0000 | 0.0 |

#### Subgroups, Final test (1000 images), single-pass gemma4:31b

| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |
|---|---:|---:|---:|---:|
| Clearly visible (negatives + violations with largest box share >= 0.0030) | 942 | 0.6164 | 0.9267 | 71.6 |
| Hazard size below 1% of image (violation images) | 201 | 0.9061 | 0.9602 | 0.0 |
| Hazard size 1% to 10% (violation images) | 200 | 0.8168 | 0.9113 | 0.0 |
| Hazard size 10% or more (violation images) | 99 | 0.8033 | 0.9231 | 0.0 |
| camera_distance = long distance | 46 | 0.6071 | 0.9444 | 60.7 |
| camera_distance = mid distance | 727 | 0.6369 | 0.9268 | 72.3 |
| camera_distance = short distance | 227 | 0.6647 | 0.9504 | 72.2 |
| illumination = night | 58 | 0.7193 | 0.7593 | 0.0 |
| illumination = normal lighting | 794 | 0.6309 | 0.9555 | 74.9 |
| illumination = overexposed | 42 | 0.5538 | 0.9474 | 87.0 |
| illumination = underexposed | 106 | 0.7143 | 0.9434 | 44.4 |
| Rule-4-only negatives (false alarms) | 2 | 0.0000 | 0.0000 | 100.0 |
