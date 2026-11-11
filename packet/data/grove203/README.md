# Development images (203)

| File | Contents |
|---|---|
| `annotations.coco.json` | Ground truth in COCO format: 247 boxes in seven OSHA-aligned categories over the 105 images with a hazard. The other 98 images have no box and count as hazard-free. |
| `image_list.csv` | File names of the 203 images. |
| `iaa_matched_pairs.csv` | The 54 matched box pairs of the inter-annotator agreement (21 images): each annotator's category, match flag and overlaps. |

The images come from three sources: 96 hazard-free images from public construction-safety datasets on Kaggle, 78 hazard images collected through Google Images, and 29 images generated with Google Gemini (27 with hazards, 2 without). The images are not stored in this folder; the Kaggle and Google Images files remain subject to the terms of their sources.

GROVE scores three of the seven categories: Fall, Electrical and protective equipment. That gives 125 positive image-category pairs (Fall 61, Electrical 24, protective equipment 40) and 132 boxes. The mapping from the raw category names is in `packet/category_mapping.md`.
