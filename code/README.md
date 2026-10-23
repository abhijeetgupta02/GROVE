# Code

Two independent parts:

- **`evaluation/`** — scores prediction workbooks against the ground truth and
  produces the paper's metric tables. Pure-Python, offline, no GPU. This is what
  reproduces the reported numbers.
- **`inference/`** — the GROVE pipeline and the single-pass baseline runners
  that *generated* the predictions. Requires a GPU, a local Ollama server, and a
  GroundingDINO checkout. Not needed to reproduce the tables.

## evaluation/

| Script | Produces | Paper table |
|---|---|---|
| `identification_eval.py` | `results/identification/identification_results.csv` | 3, 4, 9 |
| `grounding_eval.py` | `results/grounding/master_grounding_summary.csv` | 5, 6, 10 |
| `cataware_gt_covers_pred.py` | `results/grounding/gt_covers_pred_comparison.csv` | 5 (containment) |
| `run_evaluation.py` | runs all three | — |
| `eval_config.py` | shared paths + system manifest + category mapper | — |

Run everything:

```bash
cd code/evaluation
python run_evaluation.py
```

Each script also runs standalone and accepts `--gt`, `--predictions-dir`, and
`--out-dir`; defaults resolve to the bundled `data/` and `predictions/`
directories, so no arguments are needed. Each prediction workbook is read from
its `Full_Results` sheet (`image_name`, `hazards_json`, and per-hazard
`bbox_xyxy`). Category strings are mapped to the seven canonical classes by the
shared `hazard_taxonomy` module so that evaluation and inference use one mapping
source of truth.

## inference/

| Entry point | Role |
|---|---|
| `grove_pipeline/run_experiment.py` | the GROVE pipeline: captioning → hazard analysis → GroundingDINO with DETR + OpenCLIP fallback (the code behind the reported run) |
| `run_baseline.py` | any single-pass baseline (`--list` to see keys) |
| `shared/datasets.py` | image listing helpers |
| `shared/e2e_runner.py` | single-pass image→hazards runner |
| `shared/vlm_caller.py` | Ollama chat wrapper (retries, GPU cooldown) |
| `shared/data_schema.py` | JSONL/XLSX record schema and writers |
| `shared/hazard_taxonomy.py` | canonical category mapping (shared with eval) |
| `config.py` | paths, model registry, thresholds, decoding settings |

External requirements for re-running inference (none are bundled):

- **Ollama** serving the model tags in `MODEL_IDENTIFIERS.md`.
- **GroundingDINO** (Swin-T/OGC weights) — clone it and set
  `GROUNDINGDINO_HOME` (and optionally `GROUNDINGDINO_WEIGHTS`).
- `transformers` fetches `facebook/detr-resnet-50`; `open_clip` fetches
  ViT-B/32 — both on first use.

Paths and thresholds are environment-overridable (`GROVE_ROOT`,
`GROVE_IMAGE_DIR`, `GROVE_GT_JSON`, `GROVE_RESULTS_DIR`, `GROUNDINGDINO_HOME`);
defaults point inside this package.

```bash
cd code/inference
python grove_pipeline/run_experiment.py --start 1 --end 5
python run_baseline.py --model e2e_qwen35_27b
```
