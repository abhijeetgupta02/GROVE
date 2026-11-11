# Experiment 5. ConstructionSite10k label audit (labels only, no model calls)

Generated 2026-11-05T10:57:20 from `packet\data\constructionsite10k\train` (7009 rows) and `splits\train_splits.json` (seed 20260422).

## Box format

`rule_k_violation` is null when the rule is not violated, otherwise `{bounding_box, reason}`. `bounding_box` is a list of boxes, each `[x1, y1, x2, y2]` as fractions of image width and height (1540 boxes; all of length 4: True; values 0.00 to 1.00; x1<x2 and y1<y2 in 99.9%). Parsed as normalized xyxy and multiplied by the decoded image size.

## Counts per split

| Split | Images | Rule 1 | Rule 2 | Rule 3 | Rule 4 | Violation (1-3) | No rule 1-3 | Rule 4 only | Natural violation rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tuning_sample | 500 | 51 | 6 | 5 | 3 | 61 | 439 | 1 | 0.1220 |
| validation | 1500 | 145 | 9 | 25 | 9 | 177 | 1323 | 8 | 0.1180 |
| tuning_rest | 5009 | 481 | 44 | 79 | 34 | 594 | 4415 | 25 | 0.1186 |

## Largest scored box (rules 1-3) as a share of image area, violation images

| Split | min | 10th pct | median | 90th pct | max |
|---|---:|---:|---:|---:|---:|
| tuning_sample | 0.0016 | 0.0035 | 0.0207 | 0.1400 | 0.3136 |
| validation | 0.0012 | 0.0030 | 0.0184 | 0.1656 | 0.4161 |
| tuning_rest | 0.0000 | 0.0030 | 0.0182 | 0.1565 | 0.6100 |

Mapping (Section 6.2): rule 1 = PPE_Violation; rules 2 and 3 = Fall_Hazard; rule 4 not scored. No Electrical label exists in this dataset.
