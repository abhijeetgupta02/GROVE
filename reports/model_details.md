# Experiment 4. What each model is built on

From `POST /api/show` on the frozen Ollama 0.40.14 (2026-11-05T11:13:16). Fields as reported by each model package; "-" means not shown. Each needs a citable source before submission (open item).

| Tag | ID | Family | Families | Parameter size | Quantization | Format | Architecture (model_info) | Base model / FROM | License (first line) |
|---|---|---|---|---|---|---|---|---|---|
| clef:27b | 7885241a86db | clef | clef | 27.0B | Q4_K_M | gguf | clef | Qwen3.8 27B C:\Users\Shruti Singh\.ollama\models\blobs\sha256-bd9b8 | - |
| clef-flash:9b | 73e026ff389b | clef | clef | 9.1B | Q8_0 | gguf | clef | Qwen3.5 9B C:\Users\Shruti Singh\.ollama\models\blobs\sha256-d7c35 | - |
| pplx-decider:27b | 733585a9ebb6 | qwen35 | qwen35 | 26.9B | Q4_K_M | gguf | qwen35 | pplx C:\Users\Shruti Singh\.ollama\models\blobs\sha256-c5789 | - |
| d3:9b | 0f459473f035 | qwen35 | qwen35 | 9.0B | Q8_0 | gguf | qwen35 | Qwen3.5 9B C:\Users\Shruti Singh\.ollama\models\blobs\sha256-2d93d | Apache License |
| d3:27b | bdde0a6212d6 | qwen35 | qwen35 | 26.9B | Q8_0 | gguf | qwen35 | Qwen3.8 27B C:\Users\Shruti Singh\.ollama\models\blobs\sha256-497a0 | Apache License |
| qwen3.5:9b | 6488c96fa5fa | qwen35 | qwen35 | 9.7B | Q4_K_M | gguf | qwen35 | C:\Users\Shruti Singh\.ollama\models\blobs\sha256-dec52 | Apache License |
| qwen3.5:27b | 7653528ba5cb | qwen35 | qwen35 | 27.8B | Q4_K_M | gguf | qwen35 | C:\Users\Shruti Singh\.ollama\models\blobs\sha256-d4b8b | Apache License |
| gemma4:31b | 6316f0629137 | gemma4 | gemma4 | 31.3B | Q4_K_M | gguf | gemma4 | C:\Users\Shruti Singh\.ollama\models\blobs\sha256-280af | Apache License |
| mistral-small3.2:24b | 5a408ab55df5 | mistral3 | mistral3 | 24.0B | Q4_K_M | gguf | mistral3 | C:\Users\Shruti Singh\.ollama\models\blobs\sha256-41a5b | Apache License |
| ministral-3:14b | 4760c35aeb9d | mistral3 | mistral3 | 13.9B | Q4_K_M | gguf | mistral3 | C:\Users\Shruti Singh\.ollama\models\blobs\sha256-bfb40 | Apache License |
| qwen3-vl:32b | ff2e46876908 | qwen3vl | qwen3vl | 33.4B | Q4_K_M | gguf | qwen3vl | C:\Users\Shruti Singh\.ollama\models\blobs\sha256-6e416 | Apache License |

Capabilities per model: clef:27b: decision,vision; clef-flash:9b: decision,vision; pplx-decider:27b: decision,vision; d3:9b: decision,vision; d3:27b: decision,vision; qwen3.5:9b: completion,vision,tools,thinking; qwen3.5:27b: completion,vision,tools,thinking; gemma4:31b: completion,vision,tools,thinking; mistral-small3.2:24b: completion,vision,tools; ministral-3:14b: completion,vision,tools; qwen3-vl:32b: completion,vision,tools,thinking
