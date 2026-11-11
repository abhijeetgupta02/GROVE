# Experiment 6. Related scenes across all sets

Difference hash, 16 by 16 (256 bits), on the 203 images (encoded_q95 bytes) and all 7009 training images. Pairs at 66 bits or fewer are near copies.

- Files 63 and 79 (identical): distance 0 bits -> match.
- Near-copy pairs: 1146 in total; across datasets 0; within ConstructionSite10k 1139; within the 203 7.
- ConstructionSite10k images that are near copies of a 203 image (removed from candidates): 0 []

## Cutoff validation (viewed before any model ran)

Viewed before any model ran (2026-11-05 11:15): the 20 within-ConstructionSite10k pairs closest to the cutoff on each side, the 20 closest cross-dataset pairs, and random samples of 12 pairs at 64-66 and 69-72 bits. Files 63 and 79 match (0 bits). No cross-dataset pair is at 67 bits or fewer (closest 68 bits, clearly unrelated), so no ConstructionSite10k image is removed as a near copy of a 203 image. At 59-60 bits about 8 of 20 pairs were unrelated low-detail images (haze, night), and at 61 bits about 6 of 10 pairs were still true near copies (consecutive frames from one camera); at 64-66 bits 4 of 12 sampled pairs were near copies and at 69-72 bits none of 12. Both kinds of error occur near 60, so the cutoff was changed once, from 60 to 66 bits, to catch copies between the calibration and final sets (the error that would leak information into the final test). The remaining error is that some unrelated low-detail images are treated as near copies: they are removed from later candidate pools (the final pool still had about 563 violation candidates for 500) or share a bootstrap group, which only widens intervals.

Contact sheets: `scene_check_cross_below.png`, `scene_check_cross_above.png`, `scene_check_cs_below.png`, `scene_check_cs_above.png`.

This catches near copies, not the same site photographed from another angle.
