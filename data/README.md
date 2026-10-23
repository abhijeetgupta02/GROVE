# Evaluation Dataset

The benchmark is **203 construction-site images**: 105 contain at least one
hazard and 98 are hazard-free (included so that systems are penalised for
over-predicting). The images come from three sources: 96 hazard-free images from
public Kaggle construction-safety datasets, 78 hazard images from Google Images,
and 29 images generated with Google Gemini (27 with hazards, 2 without). They
were selected to span
the seven OSHA-aligned hazard categories below. Annotations were made in
Roboflow and exported in COCO format.

## Files

- `iaa_matched_pairs.csv` — the 54 matched box pairs behind the inter-annotator
  agreement statistics (each annotator's category, match flag, IoU, IoG and IoP).
- `image_list.csv` — the file names of the 203 evaluation images. The images
  themselves are not redistributed here (see Provenance below).
- `annotations.coco.json` — ground truth in COCO format. It contains **247
  bounding boxes** over the 105 hazard images. The 98 hazard-free images carry
  no annotations; during scoring they are treated as images with an empty
  ground-truth category set, so any predicted hazard on them counts as a false
  positive.

## Hazard categories

Annotations use a seven-class, OSHA-aligned taxonomy. The raw COCO category
names in `annotations.coco.json` are collapsed to these seven canonical classes
by the evaluation scripts (see `code/evaluation/eval_config.py` and
`code/inference/shared/hazard_taxonomy.py`):

| Raw COCO category | Canonical class |
|---|---|
| Fall from Height | Fall_Hazard |
| Falling Object Hazard | StruckBy_Hazard |
| Electrical Hazard | Electrocution_Hazard |
| Equipment and Machine Safety | CaughtInBetween_hazard |
| PPE Deficiency | PPE_Violation |
| Housekeeping | Housekeeping_Storage |
| Slip and Trip Hazard | Housekeeping_Storage |
| Signage and Communication | Other |
| Hazards / Other | Other |

Per-category ground-truth distribution (paper Table 1): Fall 63, Struck-by 3,
Electrocution 24, Caught-in/Between 10, PPE 45, Housekeeping/Storage 77, Other
25 — 247 boxes total over 210 image-category instances. The Struck-by (3) and
Caught-in/Between (10) classes are sparse; per-category metrics for them are
reported with that caveat in the paper.

## Image-name normalisation

Some filenames carry Roboflow export suffixes (`.rf.<hash>.<ext>`) or
underscored extensions (`3_jpeg`). The evaluation scripts normalise these so
that prediction rows and ground-truth images align; the logic is in
`normalize_image_name` (`code/inference/shared/hazard_taxonomy.py`).

## Annotation and validation

A primary annotator (A1) labeled all 203 images, and a second annotator (A2)
independently labeled a randomly selected 21-image subset. Over the 54 matched
box pairs, the two annotators reach Cohen's κ = 0.8051 and 85.2% exact category
agreement. A six-member expert panel led by a Chartered Civil Engineer reviewed
all 247 boxes: 205 were confirmed as hazards in the correct category at first
review, the 25 boxes assigned to a different category were relabeled before
scoring, and 17 boxes flagged as ambiguous or non-hazardous were retained as
potential falling-object regions. All systems are scored against these
post-review annotations (paper appendices on expert validation and
inter-annotator agreement).

## Provenance / terms

The images are not redistributed in this repository because most come from
third-party sources (Kaggle datasets and Google Images) with their own terms.
The annotations and predictions are released under CC BY 4.0 (see
`../LICENSE`); the evaluation scripts need only these files, not the images.
The images are available from the authors on request, subject to the terms of
their original sources.
