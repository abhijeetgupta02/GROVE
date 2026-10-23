# Model Identifiers

This table maps each system label used in the paper to (a) its key in
`code/inference/config.py::MODELS`, (b) the model tag it was served under, and
(c) the prediction file in `predictions/` that backs its reported numbers.

Models were served locally through **Ollama** using the tags below. Because the
reported tables are reproduced from the cached predictions in `predictions/`
(see the top-level `README.md`), exact local availability of these model tags is
**not** required to verify the results — only to regenerate predictions from the
raw images.

## GROVE (modular pipeline)

| Paper label | config key | Backbone tag | Prediction file |
|---|---|---|---|
| GROVE (Ours) | `modular_qwen9b` | `qwen3.5:9b` | `predictions/grove/grove_qwen35_9b_run1.{xlsx,jsonl}` |

GROVE uses the `qwen3.5:9b` backbone for both text stages (scene
captioning and OSHA-aligned hazard analysis), paired with
GroundingDINO Swin-T/OGC as the primary grounder and a DETR-ResNet-50 +
OpenCLIP ViT-B/32 semantic fallback.

## Single-pass baselines (Table 2 / Table 4)

| Paper label | config key | Model tag | Prediction file (`predictions/single_pass/`) |
|---|---|---|---|
| Qwen 3.5 2B | `e2e_qwen35_2b` | `qwen3.5:2b` | `qwen35_2b_run1.*` |
| Qwen 3.5 4B | `e2e_qwen35_4b` | `qwen3.5:4b` | `qwen35_4b_run1.*` |
| Qwen 3.5 9B | `e2e_qwen35_9b` | `qwen3.5:9b` | `qwen35_9b_run1.*` |
| Qwen 3.5 27B | `e2e_qwen35_27b` | `qwen3.5:27b` | `qwen35_27b_run1.*` |
| Qwen 3.6 35B | `e2e_qwen36_35b` | `qwen3.6:35b` | `qwen36_35b_run1.*` |
| Gemma 4 E2B | `e2e_gemma4_e2b` | `gemma4:e2b` | `gemma4_e2b_run1.*` |
| Gemma 4 E4B | `e2e_gemma4_e4b` | `gemma4:e4b` | `gemma4_e4b_run1.*` |
| Gemma 4 26B | `e2e_gemma4_26b` | `gemma4:26b` | `gemma4_26b_run1.*` |
| Gemma 4 31B | `e2e_gemma4_31b` | `gemma4:31b` | `gemma4_31b_run1.*` |
| Llama 3.2 Vision 11B | `e2e_llama32_vision_11b_apr2026` | `llama3.2-vision:11b` | `llama32_vision_11b_apr2026_run1.*` |
| InternVL 3.5 8B | `e2e_internvl3_5_8b` | `blaifa/InternVL3_5:8b` | `internvl3_5_8b_run1.*` |

## Modular-backbone ablation (Table 9)

The ablation re-runs the GROVE modular pipeline with each backbone above in
place of `qwen3.5:9b`. Predictions are in `predictions/modular_ablation/`
(file stem = backbone, e.g. `gemma4_31b_run1.xlsx`). The Qwen 3.5 9B row of
Table 9 is the GROVE system itself (`predictions/grove/`); the Qwen 3.5 27B row
corresponds to `qwen35_27b_patch1_run1.*`.
