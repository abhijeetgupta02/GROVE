"""Offline follow-up analyses after final scoring (owner's request of 2026-11-10; logs\\deviations.md D23).

No model call of any kind. Reads saved outputs only. Changes nothing in runs, freeze or lists; refits and changes no threshold,
model or setting. Writes new files only and refuses to overwrite an existing file.

  box        Step 2: single-pass boxes read as 0-1000 grid coordinates (D18 sensitivity), with fit counts and the trust rule.
             Writes reports\\box_rescale.md and results\\offline_box_rescale.json.
  intervals  Step 3: paired bootstrap intervals (4,000 draws, seed 20260422; same-scene groups on the 203, near-copy groups on new images)
             for top-box F1 at 0.5 and for false alarms on the 203. Writes reports\\intervals_addendum.md and results\\offline_intervals_addendum.json.
  posthoc    Step 7, POST HOC: threshold-free comparison (precision-recall curves, average precision, precision at the single-pass recall,
             recall at the single-pass precision) on the calibration 500 and final 1,000. Writes reports\\posthoc_threshold_free.md,
             reports\\posthoc_pr_calibration.png, reports\\posthoc_pr_final.png and results\\posthoc_threshold_free.json.
Usage: offline_20261110.py box|intervals|posthoc
"""
import json, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from grove_common import set_mode, read_json, now, CATS2, CATS3, SHORT, SEED, GENERATORS, PK, f_fall, f_ppe
MODE = set_mode('main')
import grove_data as gd, grove_score as gs, grove_stages as st, grove_calls as gcl
import box_rescale as br
DRAWS = 4000

def new_file(p, text, binary=False):
    if os.path.exists(p): raise SystemExit('REFUSED: %s exists; this script writes new files only' % p)
    with open(p, 'wb' if binary else 'w', **({} if binary else {'encoding': 'utf-8'})) as f: f.write(text)
    print('written', p)
def jdump(o): return json.dumps(o, indent=1, default=lambda x: float(x) if isinstance(x, (np.floating, np.integer)) else str(x))
def f4(x): return '-' if x is None or (isinstance(x, float) and np.isnan(x)) else '%.4f' % x
def ci(t): return '%+.4f [%+.4f, %+.4f]' % tuple(t)

# ------------------------------------------------------------------ shared: sets, boxes, per-image counts
_C = None
def ctx():
    global _C
    if _C is None: _C = st.Ctx()
    return _C
def grove_top(set_key):
    if set_key == '203': items = read_json(MODE.path('results', 'e31_38.json'))['items']['36 both, as designed']
    elif set_key == 'cal': items = read_json(MODE.path('results', 'e45.json'))['items']
    else: items = read_json(MODE.path('results', 'e53_grounding_predictions.json'))['items']
    return {(x['image'], x['category']): x['boxes'][:1] for x in items if x['boxes']}
def set_info(set_key):
    c = ctx()
    if set_key == '203': return dict(label='203 development images (Fall, Electrical, PPE)', names=list(c.names), cats=CATS3, src='203', exp='e09', T=st.true_203(list(c.names), CATS3), groups=c.groups, group_kind='same-scene groups')
    ids = c.cal if set_key == 'cal' else c.fin
    return dict(label=('Calibration 500 (Fall, PPE)' if set_key == 'cal' else 'Final 1,000 (Fall, PPE)'), names=list(ids), cats=CATS2, src='cs', exp=('e43' if set_key == 'cal' else 'e52'),
                T=st.true_cs(ids, CATS2), groups=gd.cs_groups(ids), group_kind='near-copy groups')
_SIZES = {}
def img_size(name, src):
    if (name, src) not in _SIZES:
        from PIL import Image
        p = os.path.join(PK, 'data', 'grove203', 'encoded_q95', name + '.q95.jpg') if src == '203' else os.path.join(gcl.CS_CACHE, '%s.q95.jpg' % name)
        with Image.open(p) as im: _SIZES[(name, src)] = im.size
    return _SIZES[(name, src)]
def sp_boxes(exp, model, names, cats, src):
    """As written (the frozen rule, saved at call time) and rescaled (0-1000 grid reading), plus fit counts."""
    _, valid, written, _, _, raw = st.load_sp(exp, model, names, cats=cats)
    resc = {}; n = dict(valid=int(valid.sum()), boxes=0, pixel=0, grid_only=0, neither=0, both=0)
    for name in names:
        r = raw.get(name)
        if r is None: continue
        W, H = img_size(name, src)
        for c in cats:
            if r['parsed'][c]['present'] is not True: continue
            b = r['parsed'][c]['bbox']; px, gr = br.pixel_box(b, W, H), br.grid_box(b); n['boxes'] += 1
            if px: n['pixel'] += 1
            elif gr: n['grid_only'] += 1
            else: n['neither'] += 1
            n['both'] += bool(px and gr)
            if gr: resc[(name, c)] = [br.to_pixels(b, W, H)]
    n['grid_only_share'] = n['grid_only'] / n['boxes'] if n['boxes'] else float('nan')
    n['trusted'] = bool(n['boxes'] and n['grid_only'] > 0.5 * n['boxes'])
    return written, resc, n
def per_image_counts(pred, T, names, cats, cut=0.5):
    """N x 3: matched, predicted boxes, true boxes (one-to-one within image and category, as grove_score.box_eval)."""
    out = np.zeros((len(names), 3))
    for i, n in enumerate(names):
        for c in cats:
            P = pred.get((n, c), []); Tb = T.get((n, c), [])
            out[i] += [len(gs.match_iou(gs.iou_matrix(P, Tb), cut)), len(P), len(Tb)]
    return out
def box_f1(C): return 2 * C[..., 0] / np.maximum(C[..., 1] + C[..., 2], 1e-9)
def boot_box_diff(Ca, Cb, groups):
    A, _, ng = gs._gsum(Ca, groups); B, _, _ = gs._gsum(Cb, groups); W = gs._wmat(ng, DRAWS, SEED)
    d = box_f1(W @ A) - box_f1(W @ B); pt = float(box_f1(A.sum(0)) - box_f1(B.sum(0)))
    return [pt, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]

# ------------------------------------------------------------------ step 2
def run_box():
    res = {'written': now(), 'sets': {}}
    L = ['# Single-pass boxes read as 0-1000 grid coordinates (sensitivity analysis, not the primary result)', '',
         'Written %s by `code\\offline_20261110.py box` (D23), after final scoring. **Sensitivity analysis only (planned as D18 before any full-run box score existed). The primary result is unchanged:** a single-pass box counts only if it is 4 integers inside the image in pixels, as the frozen rule says. No model was called; nothing in runs, freeze or lists was changed; no threshold or setting was refit.' % now(), '',
         '- `code\\box_rescale.py` was run first, unchanged; its full output is `reports\\box_rescale_sensitivity.md`. This report adds the fit counts, the trust rule and GROVE\'s top box beside each row.',
         '- **Boxes:** single-pass answers with present = true (each carries one raw box). **Fit pixel rule as written:** 4 integers with 0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height. **Fit only as 0-1000 grid:** fails the pixel rule but fits 0 <= x1 < x2 <= 1000 and 0 <= y1 < y2 <= 1000. **Fit neither:** fails both (including empty or malformed boxes).',
         '- **Rescaled:** every box that fits the grid reading (including boxes that also fit the pixel rule) is converted to pixels as x * width / 1000, y * height / 1000 of the image the model was sent; all other boxes count as no box.',
         '- **Trust rule:** a rescaled row is trusted only when most of that model\'s boxes in that set (more than half) fit only the grid reading. A box that fits both readings is no evidence either way, so it does not count towards trust. Rows that fail the rule are marked "not trusted"; their rescaled numbers are shown but should not be used.',
         '- **Scoring:** top box against top box, one-to-one within each image and category, intersection over union 0.5 (primary) and 0.3, the same matching as experiments 37, 45 and 54. GROVE\'s top box is the stored result (unchanged).', '']
    for key in ('203', 'cal', 'final'):
        S = set_info(key); names, cats, T = S['names'], S['cats'], S['T']; gt = grove_top(key); eg, _ = gs.box_eval(gt, T)
        rows = {}
        L += ['## ' + S['label'], '', 'Images %d; true boxes %d.' % (len(names), sum(len(v) for v in T.values())), '',
              '| System | Boxes | Fit pixel rule as written | Fit only as 0-1000 grid | Fit neither | Rescaled row | Top-box F1 at 0.5, as written | at 0.5, rescaled | at 0.3, as written | at 0.3, rescaled |',
              '|---|---:|---:|---:|---:|---|---:|---:|---:|---:|']
        L.append('| **GROVE top box** (stored) | - | - | - | - | - | %s | - | %s | - |' % (f4(eg['iou_0.5']['f1']), f4(eg['iou_0.3']['f1'])))
        rows['GROVE top box'] = {'iou_0.5': eg['iou_0.5'], 'iou_0.3': eg['iou_0.3']}
        for m in GENERATORS:
            if not os.path.exists(gcl.job_path(S['exp'], m, 'sp')):
                if key != '203' and m in ('qwen3.5:27b', 'gemma4:31b'): L.append('| single-pass %s | not run in experiment %d (no model call allowed) | | | | | | | | |' % (m, int(S['exp'][1:])))
                continue
            wr, rs, n = sp_boxes(S['exp'], m, names, cats, S['src']); ew, _ = gs.box_eval(wr, T); er, _ = gs.box_eval(rs, T)
            L.append('| single-pass %s | %d | %d | %d | %d | %s | %s | %s | %s | %s |' % (m, n['boxes'], n['pixel'], n['grid_only'], n['neither'],
                     'trusted (%.0f%% grid only)' % (100 * n['grid_only_share']) if n['trusted'] else 'not trusted (%.0f%% grid only)' % (100 * n['grid_only_share']),
                     f4(ew['iou_0.5']['f1']), f4(er['iou_0.5']['f1']), f4(ew['iou_0.3']['f1']), f4(er['iou_0.3']['f1'])))
            rows['single-pass ' + m] = {'counts': n, 'as_written': {'iou_0.5': ew['iou_0.5'], 'iou_0.3': ew['iou_0.3']}, 'rescaled': {'iou_0.5': er['iou_0.5'], 'iou_0.3': er['iou_0.3']}}
        if key != '203':
            L += ['', 'On these images most boxes fit both readings (%s), so the counts cannot show which reading a model used; by the rule above those rows are not trusted.' % ', '.join('%s: %d of %d' % (k.replace('single-pass ', ''), v['counts']['both'], v['counts']['boxes']) for k, v in rows.items() if 'counts' in v)]
        L.append(''); res['sets'][key] = rows
    L += ['## Reading', '', '- The as-written single-pass top-box F1 values match the stored experiment 37, 45 and 54 results (checked by `code\\box_rescale.py`).',
          '- Not trusted rows are reported for completeness only. Interval estimates for trusted rows are in `reports\\intervals_addendum.md`.', '']
    new_file(MODE.path('reports', 'box_rescale.md'), '\n'.join(L) + '\n'); new_file(MODE.path('results', 'offline_box_rescale.json'), jdump(res))

# ------------------------------------------------------------------ step 3
def run_intervals():
    res = {'written': now(), 'draws': DRAWS, 'seed': SEED, 'top_box_f1_0.5': {}, 'false_alarms_203': {}}
    box = read_json(MODE.path('results', 'offline_box_rescale.json'))
    if box is None: raise SystemExit('run the box step first')
    L = ['# Interval addendum (offline, after final scoring)', '',
         'Written %s by `code\\offline_20261110.py intervals` (D23). Paired bootstrap, %d draws, seed %d, resampled by same-scene group on the 203 images and by near-copy group on the calibration and final images (every other image is its own group), the same resampling code as the run (`grove_score._wmat`). No model call; no threshold, model or setting refit or changed. Intervals are 95%% percentile intervals.' % (now(), DRAWS, SEED), '',
         '## A. Top-box F1 at intersection over union 0.5, GROVE minus single-pass', '',
         'Box F1 = 2 x matched / (predicted boxes + true boxes), recomputed in every draw from per-image counts. "Rescaled" uses the 0-1000 grid reading of `reports\\box_rescale.md` and is shown only for trusted rows. As written is the frozen rule and the primary comparison.', '',
         '| Set | Single-pass model | Reading | GROVE top-box F1 | Single-pass top-box F1 | GROVE minus single-pass (95% interval) |', '|---|---|---|---:|---:|---|']
    for key in ('203', 'cal', 'final'):
        S = set_info(key); names, cats, T, grp = S['names'], S['cats'], S['T'], S['groups']
        Cg = per_image_counts(grove_top(key), T, names, cats); rows = {}
        for m in GENERATORS:
            if not os.path.exists(gcl.job_path(S['exp'], m, 'sp')): continue
            wr, rs, n = sp_boxes(S['exp'], m, names, cats, S['src'])
            readings = [('as written', wr)] + ([('rescaled', rs)] if n['trusted'] else [])
            for lab, pred in readings:
                Cs = per_image_counts(pred, T, names, cats); d = boot_box_diff(Cg, Cs, grp)
                L.append('| %s | %s | %s | %s | %s | %s |' % (S['label'].split(' (')[0], m, lab, f4(box_f1(Cg.sum(0))), f4(box_f1(Cs.sum(0))), ci(d)))
                rows['%s %s' % (m, lab)] = {'GROVE': float(box_f1(Cg.sum(0))), 'single_pass': float(box_f1(Cs.sum(0))), 'difference': d}
            if not n['trusted']: L.append('| %s | %s | rescaled | - | - | not trusted, no interval |' % (S['label'].split(' (')[0], m))
        res['top_box_f1_0.5'][key] = rows
        res.setdefault('groups', {})[key] = {'images': len(names), 'groups': int(len(np.unique(grp))), 'kind': S['group_kind']}
    L += ['', 'Groups: ' + '; '.join('%s %d images in %d %s' % (k, v['images'], v['groups'], v['kind']) for k, v in res['groups'].items()) + '.', '']
    # false alarms on the 203
    c = ctx(); names, Y, grp = c.names, c.Y3, c.groups; sel = st.selection(); M = sel['main_model']; bb = (st.best_baseline() or {}).get('model'); rk = st.sp_rank(c)
    Sg, vg, _ = st.grove_203(c); PIg, _ = gs.cv(Sg, Y, grp); qm, vm, _ = st.load_q('e11', M, 'm', names); PIm, _ = gs.cv(st.mq_S(qm, CATS3), Y, grp)
    fa = lambda PI: gs.summary(PI, Y, CATS3)['false_alarms_per_100_negative']
    L += ['## B. False alarms per 100 negative images, 203 images (Fall, Electrical, PPE)', '',
          'GROVE and main questions: held-out predictions (10 repeats of 5 grouped folds, seed %d, thresholds fit on training folds only), averaged over repeats, exactly as in `reports\\screening.md`. Single-pass: fixed answers. Negative images: no scored violation (%d of 203).' % (SEED, int((~Y.any(1)).sum())), '',
          '| Comparison | GROVE | Other system | GROVE minus other (95% interval) |', '|---|---:|---:|---|']
    comps = [('main questions only (m), %s' % M, PIm)]
    if bb: P, v, _, _, _, _ = st.load_sp('e09', bb, names); comps.append(('best single-pass, %s (experiment 46 choice, frozen)' % bb, gs.fixed(P, Y)))
    if rk and rk[0] != bb: P, v, _, _, _, _ = st.load_sp('e09', rk[0], names); comps.append(('single-pass %s (highest micro-F1 on the 203)' % rk[0], gs.fixed(P, Y)))
    for lab, PI in comps:
        d = gs.boot_fa_diff(PIg, PI, Y, grp); L.append('| GROVE minus %s | %.1f | %.1f | %+.1f [%+.1f, %+.1f] |' % (lab, fa(PIg), fa(PI), *d))
        res['false_alarms_203'][lab] = {'GROVE': fa(PIg), 'other': fa(PI), 'difference': list(d)}
    L += ['', 'Check: GROVE %.1f, main questions %.1f per 100 negatives, the same values as `reports\\screening.md`.' % (fa(PIg), fa(PIm)), '']
    new_file(MODE.path('reports', 'intervals_addendum.md'), '\n'.join(L) + '\n'); new_file(MODE.path('results', 'offline_intervals_addendum.json'), jdump(res))

# ------------------------------------------------------------------ step 7 (post hoc)
def curve(s, y, W):
    """Weighted precision-recall points at every distinct score threshold (flag if score >= t). W: draws x N (or 1 x N)."""
    o = np.argsort(-s, kind='mergesort'); s_, y_ = s[o], y[o].astype(float); Wo = W[:, o]
    tp = np.cumsum(Wo * y_, 1); fp = np.cumsum(Wo * (1 - y_), 1); last = np.r_[s_[1:] != s_[:-1], True]
    tp, fp = tp[:, last], fp[:, last]; pos = (Wo * y_).sum(1, keepdims=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        P = np.where(tp + fp > 0, tp / (tp + fp), np.nan); R = tp / np.maximum(pos, 1e-12)
    return s_[last], P, R
def ap(P, R):
    dR = np.diff(np.concatenate([np.zeros((R.shape[0], 1)), R], 1), axis=1)
    return np.nansum(dR * np.nan_to_num(P), 1)
def prec_at_recall(P, R, r):
    ok = R >= (r[:, None] - 1e-12); return np.nanmax(np.where(ok, P, np.nan), 1)
def rec_at_prec(P, R, p):
    ok = np.nan_to_num(P, nan=-1) >= (p[:, None] - 1e-12); return np.nanmax(np.where(ok, R, np.nan), 1)
def point(pred, y, W):
    tp = (W * (pred & y)).sum(1); fp = (W * (pred & ~y)).sum(1); fn = (W * (~pred & y)).sum(1)
    return tp / np.maximum(tp + fp, 1e-12), tp / np.maximum(tp + fn, 1e-12)
def pct(v): return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
def run_posthoc():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    c = ctx(); f2 = read_json(MODE.path('freeze', 'freeze_2.json')); TH = f2['final_thresholds']['thresholds']; M = f2['selection']['main_model']; Bm = (f2['best_baseline'] or {}).get('best', {}).get('model')
    res = {'POST_HOC': 'post hoc analysis after final scoring; not planned in the design; fits nothing and chooses nothing', 'written': now(), 'draws': DRAWS, 'seed': SEED, 'sets': {}}
    L = ['# POST HOC: threshold-free comparison of GROVE and the main questions (calibration 500 and final 1,000)', '',
         '**Post hoc analysis.** Written %s by `code\\offline_20261110.py posthoc` (D23), after final scoring and after the primary result was known. It was not planned in the design, it is not a test of any success criterion, and nothing was fit, chosen or changed from it: the frozen thresholds, the baseline choice and every reported result stay as they are. No model was called.' % now(), '',
         '- **Scores:** the saved category scores of GROVE (%s, set h, GROVE formula: experiments 40 and 50) and of the main-question model (%s, set m: experiments 41 and 51). Fall and PPE.' % (M, M),
         '- **Precision-recall curve:** precision and recall at every distinct score, flagging a category when its score is at or above that value. **Average precision (AP):** sum over those points of (recall step) x precision.',
         '- **Operating points marked:** single-pass %s (fixed answers, experiments 43 and 52); GROVE and main questions at their refit thresholds from `freeze_2.json` (fit once on the calibration 500, so on the calibration set these two points are in-sample).' % Bm,
         '- **GROVE precision at the single-pass recall:** the highest precision on GROVE\'s curve at any threshold whose recall is at least the single-pass recall. **GROVE recall at the single-pass precision:** the highest recall at any threshold whose precision is at least the single-pass precision. Both read the curve with that set\'s labels, so they describe the curve, not a threshold anyone could have set in advance.',
         '- **Intervals:** paired bootstrap, %d draws, seed %d, by near-copy group; in every draw the curves, the single-pass point and the read-outs are all recomputed on the same resample.' % (DRAWS, SEED), '']
    for key, ids, eh, em, esp in (('calibration', c.cal, 'e40', 'e41', 'e43'), ('final', c.fin, 'e50', 'e51', 'e52')):
        Y = gd.Ycs(ids); grp = gd.cs_groups(ids); qh, vh, _ = st.load_q(eh, M, 'h', ids); qm, vm, _ = st.load_q(em, M, 'm', ids)
        SG = np.nan_to_num(np.stack([f_fall(qh), f_ppe(qh)], 1), nan=-1.0); SM = np.nan_to_num(st.mq_S(qm, CATS2), nan=-1.0)
        Psp, vsp, _, _, _, _ = st.load_sp(esp, Bm, ids, cats=CATS2)
        ug, inv = np.unique(grp, return_inverse=True); Wg = gs._wmat(len(ug), DRAWS, SEED); Wd = Wg[:, inv]; W1 = np.ones((1, len(ids)))
        out = {'images': len(ids), 'completion': {'GROVE': float(vh.mean()), 'main_question': float(vm.mean()), 'single_pass': float(vsp.mean())}, 'categories': {}}
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
        L += ['## %s' % ('Calibration 500 (thresholds were refit on these images)' if key == 'calibration' else 'Final 1,000'), '',
              '| Category | AP GROVE (95% interval) | AP main questions (95% interval) | AP GROVE minus main questions (95% interval) | Single-pass precision / recall | GROVE precision at single-pass recall (95% interval) | minus single-pass precision (95% interval) | GROVE recall at single-pass precision (95% interval) | minus single-pass recall (95% interval) |',
              '|---|---|---|---|---|---|---|---|---|']
        apd_all = []
        for j, cat in enumerate(CATS2):
            y = Y[:, j]; pr = Psp[:, j]
            tg, PG, RG = curve(SG[:, j], y, W1); tm, PM, RM = curve(SM[:, j], y, W1)
            _, PGd, RGd = curve(SG[:, j], y, Wd); _, PMd, RMd = curve(SM[:, j], y, Wd)
            apg, apm = float(ap(PG, RG)[0]), float(ap(PM, RM)[0]); apgd, apmd = ap(PGd, RGd), ap(PMd, RMd); apd_all.append((apg - apm, apgd - apmd, apg, apm, apgd, apmd))
            psp, rsp = point(pr, y, W1); pspd, rspd = point(pr, y, Wd)
            pg_at = float(prec_at_recall(PG, RG, rsp)[0]); pg_atd = prec_at_recall(PGd, RGd, rspd)
            rg_at = float(rec_at_prec(PG, RG, psp)[0]); rg_atd = rec_at_prec(PGd, RGd, pspd)
            refit = {}
            for sysk, S_ in (('GROVE', SG), ('main_question', SM)):
                t = TH[sysk]['refit'][cat]; pp, rr = point(S_[:, j] >= t, y, W1); refit[sysk] = {'threshold': t, 'precision': float(pp[0]), 'recall': float(rr[0])}
            o = {'AP_GROVE': [apg] + pct(apgd), 'AP_main_question': [apm] + pct(apmd), 'AP_GROVE_minus_main_question': [apg - apm] + pct(apgd - apmd),
                 'single_pass_point': {'precision': float(psp[0]), 'recall': float(rsp[0])}, 'GROVE_precision_at_single_pass_recall': [pg_at] + pct(pg_atd),
                 'GROVE_precision_at_single_pass_recall_minus_single_pass_precision': [pg_at - float(psp[0])] + pct(pg_atd - pspd),
                 'GROVE_recall_at_single_pass_precision': [rg_at] + pct(rg_atd), 'GROVE_recall_at_single_pass_precision_minus_single_pass_recall': [rg_at - float(rsp[0])] + pct(rg_atd - rspd),
                 'refit_points': refit, 'n_positive': int(y.sum())}
            out['categories'][cat] = o
            L.append('| %s | %.4f [%.4f, %.4f] | %.4f [%.4f, %.4f] | %+.4f [%+.4f, %+.4f] | %.4f / %.4f | %.4f [%.4f, %.4f] | %+.4f [%+.4f, %+.4f] | %.4f [%.4f, %.4f] | %+.4f [%+.4f, %+.4f] |' % (
                SHORT[cat], *o['AP_GROVE'], *o['AP_main_question'], *o['AP_GROVE_minus_main_question'], psp[0], rsp[0], *o['GROVE_precision_at_single_pass_recall'],
                *o['GROVE_precision_at_single_pass_recall_minus_single_pass_precision'], *o['GROVE_recall_at_single_pass_precision'], *o['GROVE_recall_at_single_pass_precision_minus_single_pass_recall']))
            ax = axes[j]; ax.step(RG[0], PG[0], where='post', label='GROVE (h formula), AP %.3f' % apg, color='#1f5fbf'); ax.step(RM[0], PM[0], where='post', label='Main questions (m), AP %.3f' % apm, color='#d9822b')
            ax.plot(rsp[0], psp[0], marker='*', ms=14, ls='none', color='black', label='Single-pass %s' % Bm)
            ax.plot(refit['GROVE']['recall'], refit['GROVE']['precision'], marker='o', ms=8, ls='none', mfc='none', mec='#1f5fbf', mew=2, label='GROVE, refit thresholds')
            ax.plot(refit['main_question']['recall'], refit['main_question']['precision'], marker='s', ms=8, ls='none', mfc='none', mec='#d9822b', mew=2, label='Main questions, refit thresholds')
            ax.set_xlim(0, 1.01); ax.set_ylim(0, 1.01); ax.set_xlabel('Recall'); ax.set_ylabel('Precision'); ax.set_title('%s (%d positive images)' % (SHORT[cat], int(y.sum()))); ax.grid(alpha=0.3); ax.legend(fontsize=7, loc='lower left')
        mg = np.mean([a[2] for a in apd_all]); mm = np.mean([a[3] for a in apd_all]); md = np.mean([a[1] for a in apd_all], 0)
        out['mean_AP'] = {'GROVE': [float(mg)] + pct(np.mean([a[4] for a in apd_all], 0)), 'main_question': [float(mm)] + pct(np.mean([a[5] for a in apd_all], 0)), 'GROVE_minus_main_question': [float(mg - mm)] + pct(md)}
        L += ['', 'Mean AP over Fall and PPE: GROVE %.4f [%.4f, %.4f], main questions %.4f [%.4f, %.4f], GROVE minus main questions %+.4f [%+.4f, %+.4f].' % (*out['mean_AP']['GROVE'], *out['mean_AP']['main_question'], *out['mean_AP']['GROVE_minus_main_question']),
              '', 'Refit operating points (precision / recall): ' + '; '.join('%s GROVE %.4f / %.4f, main questions %.4f / %.4f' % (SHORT[cat], v['refit_points']['GROVE']['precision'], v['refit_points']['GROVE']['recall'], v['refit_points']['main_question']['precision'], v['refit_points']['main_question']['recall']) for cat, v in out['categories'].items()) + '.', '',
              'Figure: `reports\\posthoc_pr_%s.png`.' % key, '']
        fig.suptitle('POST HOC, threshold-free: %s (%d images). Not a planned test; nothing fit or chosen from it.' % ('calibration 500, thresholds refit on these images' if key == 'calibration' else 'final 1,000', len(ids)), fontsize=10)
        fig.tight_layout(rect=(0, 0, 1, 0.94)); p = MODE.path('reports', 'posthoc_pr_%s.png' % key)
        if os.path.exists(p): raise SystemExit('REFUSED: %s exists' % p)
        fig.savefig(p, dpi=150); plt.close(fig); print('written', p); res['sets'][key] = out
    new_file(MODE.path('reports', 'posthoc_threshold_free.md'), '\n'.join(L) + '\n'); new_file(MODE.path('results', 'posthoc_threshold_free.json'), jdump(res))

if __name__ == '__main__':
    {'box': run_box, 'intervals': run_intervals, 'posthoc': run_posthoc}[sys.argv[1]]()
