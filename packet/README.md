# GROVE packet for the Windows PC, 2026-11-04

- `data/grove203/`: 203 images, labels. `encoded_q95/` holds the exact JPEG bytes sent to the models on the Mac (Pillow 11.3.0).
- `data/constructionsite10k/`: training parquet and `splits/train_splits.json`, seed 20260422: tuning_sample 500, validation 1500, tuning_rest 5009 (unused). The locked test set and the upstream test-set predictions are not in this packet.
- `prompts/prompts.json`: every prompt set. `h` is the clean set.
- `models/models.csv`: tags and Mac digests. Mac Ollama 0.40.14.
- `reference_mac/`: Mac scores, for comparing runs.
- `code/check_match.py`: 5-image comparison with the Mac. `code/reference_mac/`: Mac scripts, for reference only; they hold Mac paths.
- `MANIFEST.sha256`: SHA-256 of every file here.

Do not run experiments until the run instructions arrive. Do not change these files; write results outside this folder or in `logs/`.
