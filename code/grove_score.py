"""Metrics: thresholds, grouped folds, bootstrap, prevalence-standardized precision, box matching (Section 7, Section 14 Part 7)."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from grove_common import SEED
np.seterr(invalid='ignore')
GRID = np.round(np.arange(0.02, 0.99, 0.02), 2)

def c3(P, Y): return np.array([(P & Y).sum(), (P & ~Y).sum(), (~P & Y).sum()], float)
def f1(c): return 2 * c[0] / max(2 * c[0] + c[1] + c[2], 1e-9)
def prec(c): return c[0] / max(c[0] + c[1], 1e-9)
def rec(c): return c[0] / max(c[0] + c[2], 1e-9)
def ge(S, th):
    with np.errstate(invalid='ignore'): return np.nan_to_num(S, nan=-1.0) >= th
def fit(S, Y, per_category=True):
    """Best single threshold for micro-F1, then 2 rounds per category. Ties keep the first (lowest) value, as the Mac code does."""
    K = S.shape[1]; g = max(GRID, key=lambda x: f1(c3(ge(S, x), Y))); th = np.full(K, g)
    if per_category:
        for _ in range(2):
            for c in range(K):
                best, bv = th[c], -1
                for x in GRID:
                    t2 = th.copy(); t2[c] = x; v = f1(c3(ge(S, t2), Y))
                    if v > bv + 1e-12: best, bv = x, v
                th[c] = best
    return th
def fit_single(S, Y): return fit(S, Y, per_category=False)
def per_image(P, Y):
    """N x K x 3 counts (TP, FP, FN)."""
    return np.stack([P & Y, P & ~Y, ~P & Y], 2).astype(float)
def splits(groups, k, rng):
    u = rng.permutation(np.unique(groups)); pos = {g: q % k for q, g in enumerate(u)}; a = np.array([pos[g] for g in groups])
    return [(np.where(a != q)[0], np.where(a == q)[0]) for q in range(k)]
def cv(S, Y, groups, reps=10, k=5, seed=SEED, fitfn=fit):
    """Held-out per-image counts averaged over repeats, plus micro-F1 of each repeat."""
    N, K = Y.shape; PI = np.zeros((N, K, 3)); rng = np.random.RandomState(seed); per = []
    for _ in range(reps):
        R = np.zeros((N, K, 3))
        for tr, te in splits(groups, min(k, len(np.unique(groups))), rng):
            th = fitfn(S[tr], Y[tr]); R[te] += per_image(ge(S[te], th), Y[te])
        PI += R; per.append(f1(R.sum((0, 1))))
    return PI / reps, per
def blocks_cv(S, Y, nums, blocks, fitfn=fit):
    N, K = Y.shape; PI = np.zeros((N, K, 3))
    for lo, hi in blocks:
        te = (nums >= lo) & (nums <= hi)
        if te.any() and (~te).any(): PI[te] = per_image(ge(S[te], fitfn(S[~te], Y[~te])), Y[te])
    return PI
def fixed(P, Y): return per_image(P, Y)

def summary(PI, Y, cats):
    """Metrics from N x K x 3 counts."""
    T = PI.sum((0, 1)); neg = ~Y.any(1); out = {'TP': T[0], 'FP': T[1], 'FN': T[2], 'precision': prec(T), 'recall': rec(T), 'micro_f1': f1(T)}
    pc = {}
    for j, c in enumerate(cats):
        t = PI[:, j].sum(0); pc[c] = {'TP': t[0], 'FP': t[1], 'FN': t[2], 'precision': prec(t), 'recall': rec(t), 'f1': f1(t)}
    out['per_category'] = pc; out['macro_f1'] = float(np.mean([v['f1'] for v in pc.values()])) if pc else 0.0
    out['n_images'] = int(len(Y)); out['n_negative_images'] = int(neg.sum())
    out['false_alarms_per_100_negative'] = 100 * PI[neg, :, 1].sum() / max(neg.sum(), 1)
    return out

def _gsum(PI, groups):
    ug, inv = np.unique(groups, return_inverse=True); A = np.zeros((len(ug),) + PI.shape[1:]); np.add.at(A, inv, PI); return A, inv, len(ug)
def _wmat(n_groups, draws, seed):
    rng = np.random.RandomState(seed); idx = rng.randint(0, n_groups, (draws, n_groups)); W = np.zeros((draws, n_groups))
    for d in range(draws): W[d] = np.bincount(idx[d], minlength=n_groups)
    return W
def micro_f1_rows(C): return 2 * C[:, 0] / np.maximum(2 * C[:, 0] + C[:, 1] + C[:, 2], 1e-9)
def boot_diff(PIa, PIb, groups, draws=4000, seed=SEED, cat=None):
    """Paired bootstrap by group. Returns (point difference, low, high) of micro-F1 (or one category's F1)."""
    a = PIa if cat is None else PIa[:, [cat]]; b = PIb if cat is None else PIb[:, [cat]]
    A, _, n = _gsum(a.sum(1), groups); B, _, _ = _gsum(b.sum(1), groups); W = _wmat(n, draws, seed)
    d = micro_f1_rows(W @ A) - micro_f1_rows(W @ B); pt = f1(A.sum(0)) - f1(B.sum(0))
    return float(pt), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
def boot_ci(PI, groups, draws=4000, seed=SEED, cat=None):
    a = PI if cat is None else PI[:, [cat]]; A, _, n = _gsum(a.sum(1), groups); W = _wmat(n, draws, seed); v = micro_f1_rows(W @ A)
    return float(f1(A.sum(0))), float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))
def fa_rate_rows(Wfp, Wneg): return 100 * Wfp / np.maximum(Wneg, 1e-9)
def boot_fa_diff(PIa, PIb, Y, groups, draws=4000, seed=SEED):
    neg = (~Y.any(1)).astype(float); fa = PIa[:, :, 1].sum(1) * neg; fb = PIb[:, :, 1].sum(1) * neg
    M = np.stack([fa, fb, neg], 1); A, _, n = _gsum(M, groups); W = _wmat(n, draws, seed); C = W @ A
    d = fa_rate_rows(C[:, 0], C[:, 2]) - fa_rate_rows(C[:, 1], C[:, 2]); t = A.sum(0)
    return float(fa_rate_rows(t[0], t[2]) - fa_rate_rows(t[1], t[2])), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))

def prevalence_std(PI, viol, r):
    """Weights r/p for images with a violation and (1-r)/(1-p) for the others (Section 7.3). Returns precision, recall, F1."""
    p = viol.mean(); w = np.where(viol, r / max(p, 1e-9), (1 - r) / max(1 - p, 1e-9)); T = (PI.sum(1) * w[:, None]).sum(0)
    return {'precision': prec(T), 'recall': rec(T), 'f1': f1(T), 'r': float(r), 'p': float(p)}
def boot_prevalence(PI, viol, r, groups, draws=4000, seed=SEED):
    v = viol.astype(float); C = PI.sum(1); M = np.concatenate([C * v[:, None], C * (1 - v)[:, None], v[:, None], (1 - v)[:, None]], 1)
    A, _, n = _gsum(M, groups); W = _wmat(n, draws, seed); S = W @ A
    p = S[:, 6] / np.maximum(S[:, 6] + S[:, 7], 1e-9)
    wt = (r / np.maximum(p, 1e-9))[:, None] * S[:, 0:3] + ((1 - r) / np.maximum(1 - p, 1e-9))[:, None] * S[:, 3:6]
    pr = wt[:, 0] / np.maximum(wt[:, 0] + wt[:, 1], 1e-9); f = micro_f1_rows(wt)
    return [float(np.percentile(pr, 2.5)), float(np.percentile(pr, 97.5))], [float(np.percentile(f, 2.5)), float(np.percentile(f, 97.5))]

# ---------------------------------------------------------------- boxes
def iou_matrix(P, T):
    P = np.asarray(P, float).reshape(-1, 4); T = np.asarray(T, float).reshape(-1, 4)
    if not len(P) or not len(T): return np.zeros((len(P), len(T)))
    x1 = np.maximum(P[:, None, 0], T[None, :, 0]); y1 = np.maximum(P[:, None, 1], T[None, :, 1])
    x2 = np.minimum(P[:, None, 2], T[None, :, 2]); y2 = np.minimum(P[:, None, 3], T[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    ap = (P[:, 2] - P[:, 0]) * (P[:, 3] - P[:, 1]); at = (T[:, 2] - T[:, 0]) * (T[:, 3] - T[:, 1])
    return inter / np.maximum(ap[:, None] + at[None, :] - inter, 1e-9)
def iog_matrix(P, T):
    P = np.asarray(P, float).reshape(-1, 4); T = np.asarray(T, float).reshape(-1, 4)
    if not len(P) or not len(T): return np.zeros((len(P), len(T)))
    x1 = np.maximum(P[:, None, 0], T[None, :, 0]); y1 = np.maximum(P[:, None, 1], T[None, :, 1])
    x2 = np.minimum(P[:, None, 2], T[None, :, 2]); y2 = np.minimum(P[:, None, 3], T[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None); at = (T[:, 2] - T[:, 0]) * (T[:, 3] - T[:, 1])
    return inter / np.maximum(at[None, :], 1e-9)
def match_iou(iou, cutoff):
    """Weight 0 below the cutoff, K+1+IoU at or above it (K = smaller box count); keep assigned pairs at or above the cutoff."""
    iou = np.asarray(iou, float)
    if iou.size == 0: return []
    K = min(iou.shape); W = np.where(iou >= cutoff, K + 1 + iou, 0.0)
    r, c = linear_sum_assignment(W, maximize=True)
    return [(int(i), int(j), float(iou[i, j])) for i, j in zip(r, c) if iou[i, j] >= cutoff]
def box_eval(pred, true, cutoffs=(0.5, 0.3)):
    """pred, true: dict (image, category) -> list of xyxy boxes. One-to-one within each image and category."""
    keys = sorted(set(pred) | set(true), key=str); res = {}; matches = {}
    for cut in cutoffs:
        npred = ntrue = nm = 0; ms = []
        for k in keys:
            P = pred.get(k, []); T = true.get(k, []); npred += len(P); ntrue += len(T)
            m = match_iou(iou_matrix(P, T), cut); nm += len(m)
            ms += [{'image': k[0], 'category': k[1], 'pred': int(i), 'true': int(j), 'iou': v, 'cutoff': cut} for i, j, v in m]
        p = nm / max(npred, 1e-9); r = nm / max(ntrue, 1e-9)
        res['iou_%.1f' % cut] = {'pred_boxes': npred, 'true_boxes': ntrue, 'matched': nm, 'precision': p, 'recall': r, 'f1': 2 * p * r / max(p + r, 1e-9),
                                 'unmatched_pred': npred - nm, 'unmatched_true': ntrue - nm}
        matches[cut] = ms
    for x in (0.5, 0.7):
        cov = tot = 0
        for k in keys:
            T = true.get(k, []); tot += len(T)
            if T and pred.get(k): cov += int((iog_matrix(pred[k], T).max(0) >= x).sum())
        res['coverage_iog_%.1f' % x] = cov / max(tot, 1e-9)
    return res, matches
