# POST HOC: threshold-free comparison of GROVE and the main questions (calibration 500 and final 1,000)

**Post hoc analysis.** Written 2026-11-10T10:52:37 by `code\offline_20261110.py posthoc` (D23), after final scoring and after the primary result was known. It was not planned in the design, it is not a test of any success criterion, and nothing was fit, chosen or changed from it: the frozen thresholds, the baseline choice and every reported result stay as they are. No model was called.

- **Scores:** the saved category scores of GROVE (d3:27b, set h, GROVE formula: experiments 40 and 50) and of the main-question model (d3:27b, set m: experiments 41 and 51). Fall and PPE.
- **Precision-recall curve:** precision and recall at every distinct score, flagging a category when its score is at or above that value. **Average precision (AP):** sum over those points of (recall step) x precision.
- **Operating points marked:** single-pass gemma4:31b (fixed answers, experiments 43 and 52); GROVE and main questions at their refit thresholds from `freeze_2.json` (fit once on the calibration 500, so on the calibration set these two points are in-sample).
- **GROVE precision at the single-pass recall:** the highest precision on GROVE's curve at any threshold whose recall is at least the single-pass recall. **GROVE recall at the single-pass precision:** the highest recall at any threshold whose precision is at least the single-pass precision. Both read the curve with that set's labels, so they describe the curve, not a threshold anyone could have set in advance.
- **Intervals:** paired bootstrap, 4000 draws, seed 20260422, by near-copy group; in every draw the curves, the single-pass point and the read-outs are all recomputed on the same resample.

## Calibration 500 (thresholds were refit on these images)

| Category | AP GROVE (95% interval) | AP main questions (95% interval) | AP GROVE minus main questions (95% interval) | Single-pass precision / recall | GROVE precision at single-pass recall (95% interval) | minus single-pass precision (95% interval) | GROVE recall at single-pass precision (95% interval) | minus single-pass recall (95% interval) |
|---|---|---|---|---|---|---|---|---|
| Fall | 0.3778 [0.2823, 0.5186] | 0.3602 [0.2655, 0.4959] | +0.0176 [-0.0434, +0.0816] | 0.2632 / 0.8654 | 0.2911 [0.2256, 0.3691] | +0.0280 [+0.0009, +0.0721] | 0.9231 [0.8298, 1.0000] | +0.0577 [+0.0000, +0.1833] |
| PPE | 0.8531 [0.8053, 0.8937] | 0.8623 [0.8162, 0.9010] | -0.0091 [-0.0173, -0.0013] | 0.5701 / 0.9257 | 0.6006 [0.5353, 0.6609] | +0.0305 [-0.0149, +0.0666] | 0.9455 [0.9100, 0.9856] | +0.0198 [-0.0135, +0.0739] |

Mean AP over Fall and PPE: GROVE 0.6155 [0.5671, 0.6860], main questions 0.6112 [0.5617, 0.6801], GROVE minus main questions +0.0042 [-0.0258, +0.0363].

Refit operating points (precision / recall): Fall GROVE 0.4225 / 0.5769, main questions 0.3875 / 0.5962; PPE GROVE 0.7571 / 0.7871, main questions 0.7466 / 0.8168.

Figure: `reports\posthoc_pr_calibration.png`.

## Final 1,000

| Category | AP GROVE (95% interval) | AP main questions (95% interval) | AP GROVE minus main questions (95% interval) | Single-pass precision / recall | GROVE precision at single-pass recall (95% interval) | minus single-pass precision (95% interval) | GROVE recall at single-pass precision (95% interval) | minus single-pass recall (95% interval) |
|---|---|---|---|---|---|---|---|---|
| Fall | 0.3956 [0.3147, 0.5039] | 0.4239 [0.3321, 0.5282] | -0.0283 [-0.0723, +0.0251] | 0.2705 / 0.8316 | 0.2687 [0.2192, 0.3475] | -0.0018 [-0.0361, +0.0646] | 0.8211 [0.7273, 0.9425] | -0.0105 [-0.0965, +0.1429] |
| PPE | 0.8645 [0.8352, 0.8912] | 0.8850 [0.8585, 0.9089] | -0.0206 [-0.0270, -0.0146] | 0.5843 / 0.9564 | 0.5733 [0.5311, 0.6168] | -0.0110 [-0.0358, +0.0178] | 0.9467 [0.9134, 0.9717] | -0.0097 [-0.0392, +0.0137] |

Mean AP over Fall and PPE: GROVE 0.6300 [0.5883, 0.6851], main questions 0.6545 [0.6078, 0.7071], GROVE minus main questions -0.0244 [-0.0465, +0.0022].

Refit operating points (precision / recall): Fall GROVE 0.4375 / 0.4421, main questions 0.3945 / 0.4526; PPE GROVE 0.7289 / 0.7942, main questions 0.7372 / 0.8354.

Figure: `reports\posthoc_pr_final.png`.

