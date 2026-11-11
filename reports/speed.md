# Experiment 56. Speed and memory (Table 7)

## Batch runs (seconds per image, valid responses)

| Experiment | File | Images | Valid | Mean seconds per image | Total hours |
|---|---|---:|---:|---:|---:|
| e09 | gemma4_31b__sp.jsonl | 203 | 203 | 4.02 | 0.23 |
| e09 | ministral-3_14b__sp.jsonl | 203 | 203 | 2.44 | 0.14 |
| e09 | mistral-small3.2_24b__sp.jsonl | 203 | 203 | 3.53 | 0.20 |
| e09 | qwen3-vl_32b__sp.jsonl | 203 | 202 | 51.95 | 2.98 |
| e09 | qwen3.5_27b__sp.jsonl | 203 | 203 | 5.30 | 0.30 |
| e09 | qwen3.5_9b__sp.jsonl | 203 | 203 | 2.23 | 0.13 |
| e10 | gemma4_31b__sp.jsonl | 20 | 20 | 4.09 | 0.02 |
| e10 | qwen3.5_27b__sp.jsonl | 20 | 20 | 5.11 | 0.03 |
| e10 | qwen3.5_9b__sp.jsonl | 20 | 20 | 2.09 | 0.01 |
| e11 | clef-flash_9b__m.jsonl | 203 | 203 | 0.54 | 0.03 |
| e11 | clef_27b__m.jsonl | 203 | 203 | 1.10 | 0.06 |
| e11 | d3_27b__m.jsonl | 203 | 203 | 2.51 | 0.14 |
| e11 | d3_9b__m.jsonl | 203 | 203 | 1.25 | 0.07 |
| e11 | pplx-decider_27b__m.jsonl | 203 | 201 | 1.23 | 0.07 |
| e12 | clef-flash_9b__h.jsonl | 203 | 203 | 0.80 | 0.05 |
| e12 | clef_27b__h.jsonl | 203 | 203 | 1.94 | 0.11 |
| e12 | d3_27b__h.jsonl | 203 | 203 | 9.91 | 0.56 |
| e12 | d3_9b__h.jsonl | 203 | 203 | 4.90 | 0.28 |
| e12 | pplx-decider_27b__h.jsonl | 203 | 203 | 2.35 | 0.13 |
| e13 | clef-flash_9b__S0.jsonl | 203 | 203 | 0.60 | 0.03 |
| e13 | clef_27b__S0.jsonl | 203 | 203 | 1.31 | 0.07 |
| e13 | d3_27b__S0.jsonl | 203 | 203 | 4.35 | 0.25 |
| e13 | d3_9b__S0.jsonl | 203 | 203 | 2.16 | 0.12 |
| e13 | pplx-decider_27b__S0.jsonl | 203 | 203 | 1.56 | 0.09 |
| e23_rep1 | d3_27b__h.jsonl | 203 | 203 | 9.87 | 0.56 |
| e23_rep2 | d3_27b__h.jsonl | 203 | 203 | 9.87 | 0.56 |
| e31_32_phrases | qwen3.5_9b__phrase.jsonl | 144 | 144 | 0.63 | 0.03 |
| e40 | d3_27b__h.jsonl | 500 | 500 | 17.44 | 2.42 |
| e41 | d3_27b__m.jsonl | 500 | 500 | 4.42 | 0.61 |
| e42 | pplx-decider_27b__h.jsonl | 500 | 500 | 3.00 | 0.42 |
| e43 | gemma4_31b__sp.jsonl | 500 | 500 | 4.77 | 0.66 |
| e43 | qwen3.5_27b__sp.jsonl | 500 | 500 | 6.21 | 0.86 |
| e50 | d3_27b__h.jsonl | 1000 | 1000 | 17.61 | 4.89 |
| e51 | d3_27b__m.jsonl | 1000 | 1000 | 4.47 | 1.24 |
| e52 | gemma4_31b__sp.jsonl | 1000 | 1000 | 4.76 | 1.32 |

## Peak graphics memory (MiB, sampled every minute by nvidia-smi)

- e09|gemma4:31b: 25071
- e09|ministral-3:14b: 14915
- e09|mistral-small3.2:24b: 20933
- e09|qwen3-vl:32b: 32663
- e09|qwen3.5:27b: 19877
- e09|qwen3.5:9b: 8587
- e10|gemma4:31b: 24789
- e10|qwen3.5:27b: 19495
- e10|qwen3.5:9b: 8253
- e11|clef-flash:9b: 14452
- e11|clef:27b: 25292
- e11|d3:27b: 31840
- e11|d3:9b: 11864
- e11|pplx-decider:27b: 21096
- e12|clef-flash:9b: 14468
- e12|clef:27b: 25316
- e12|d3:27b: 31866
- e12|d3:9b: 11878
- e12|pplx-decider:27b: 21098
- e13|clef-flash:9b: 14456
- e13|clef:27b: 25298
- e13|d3:27b: 31840
- e13|d3:9b: 11864
- e13|pplx-decider:27b: 21098
- e23_rep1|d3:27b: 31866
- e23_rep2|d3:27b: 31866
- e31_32_phrases|qwen3.5:9b: 16908
- e40|d3:27b: 32150
- e41|d3:27b: 32150
- e42|pplx-decider:27b: 21406
- e43|gemma4:31b: 25346
- e43|qwen3.5:27b: 20156
- e50|d3:27b: 32161
- e51|d3:27b: 32150
- e52|gemma4:31b: 25352
- |: 31840

## Single-image speed of the whole GROVE pipeline (20 calibration images, one at a time)

- Seconds per image with models loaded: mean 19.12, max 29.95.
- main model h: {'model': 'd3:27b', 'first_call_seconds': 24.38, 'warm_median_seconds': 18.499, 'load_seconds_estimate': 5.881}
- grounding models: {'load_seconds': 2.1340794563293457}

Batch speed is not single-image speed: batch runs keep one model loaded for the whole set.
