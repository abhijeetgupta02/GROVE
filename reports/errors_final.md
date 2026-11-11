# POST HOC: false alarms and misses on the final 1,000 (experiment 60 repeated)

**Post hoc analysis** (D24), written 2026-11-10T12:11:05 by `code\posthoc_parta.py errors`, after final scoring, from saved outputs; no model call; nothing refit. Same method as experiment 60 (calibration): every image-category error (Fall, PPE) is classed from keywords in the system's text and the dataset reason (`grove_stages.classify_error`), and 100 errors per system are sampled with `random.Random(20260422)`. GROVE uses its refit thresholds from `freeze_2.json` and its grounding phrase (experiment 53); single-pass gemma4:31b uses its fixed answers and its own evidence text in place of a phrase. Images are copied unchanged into `reports\errors_final` (file names start with the system), one CSV per system.

## GROVE (d3:27b, refit thresholds)

All errors: 314 (false alarms 176, misses 138). By category: Fall 54 false alarms / 53 misses, PPE 122 false alarms / 85 misses.

| Type | Class | All errors | In the sample of 100 |
|---|---|---:|---:|
| false alarm | helmet or vest | 121 | 39 |
| false alarm | inferred height or depth | 18 | 6 |
| false alarm | other or no text | 37 | 12 |
| miss | helmet or vest | 46 | 14 |
| miss | inferred height or depth | 69 | 22 |
| miss | other or no text | 23 | 7 |

Sample table: `reports\errors_final\errors_GROVE.csv`.

## Single-pass gemma4:31b (best single-pass, experiment 52)

All errors: 528 (false alarms 494, misses 34). By category: Fall 213 false alarms / 16 misses, PPE 281 false alarms / 18 misses.

| Type | Class | All errors | In the sample of 100 |
|---|---|---:|---:|
| false alarm | helmet or vest | 28 | 4 |
| false alarm | inferred height or depth | 394 | 73 |
| false alarm | other or no text | 72 | 14 |
| miss | helmet or vest | 6 | 2 |
| miss | inferred height or depth | 27 | 7 |
| miss | other or no text | 1 | 0 |

Sample table: `reports\errors_final\errors_singlepass_gemma4_31b.csv`.

## Overlap

Image-category errors made by both systems: 201 (GROVE 314, gemma4:31b 528).

Classes come from keywords and are only as good as the text allows: "other or no text" means no keyword matched (for single-pass false alarms the evidence text is used; for misses only the dataset reason exists).

