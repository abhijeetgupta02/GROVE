"""POST HOC check and rescoring of the Part B confidence baselines (owner's request of 2026-11-11 08:10; logs\\deviations.md D29).
No model call. Reads runs_posthoc\\p07_cal and p07_final (gemma4:31b, qwen3.5:27b) and the run's saved outputs, with the labels, near-copy groups,
GROVE and main-question scores exactly as code\\posthoc_partb.py uses them (its own functions are imported, not copied).
  1. Diagnostic of the saved confidence values by answer (present true/false) and by reference label.
  2. Signed score s = confidence/100 if present = true, 1 - confidence/100 if present = false (invalid response = no prediction); one threshold per
     category fit on the calibration 500 with grove_score.fit (experiment 44), applied unchanged to the final 1,000; same tables as
     reports\\posthoc_confidence_baseline.md, paired intervals and average precision.
  3. The original confidence/100 rows are recomputed with the saved thresholds and checked equal to results_posthoc\\confidence_baseline.json.
Writes new files only: reports\\posthoc_confidence_signed.md, results_posthoc\\confidence_signed.json, reports\\posthoc_pr_final_signed.png.
"""
import collections, json, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import posthoc_partb as pb
from posthoc_partb import off, gs, gd, read_json, now, CATS2, SHORT, SEED, G, RP, MODE, t3, summ, srow, HEAD, base, ph_load
DR = off.DRAWS
OUT_MD = os.path.join(G, 'reports', 'posthoc_confidence_signed.md'); OUT_JS = os.path.join(RP, 'confidence_signed.json'); OUT_PNG = os.path.join(G, 'reports', 'posthoc_pr_final_signed.png')
for p in (OUT_MD, OUT_JS, OUT_PNG):
    if os.path.exists(p): raise SystemExit('REFUSED: %s exists' % p)
NEW = 'signed confidence (post hoc; score redefined after the first scoring)'
MODELS = ['gemma4:31b', 'qwen3.5:27b']; SETS = ('calibration', 'final'); EXP = {'calibration': 'p07_cal', 'final': 'p07_final'}

def raw(exp, model, ids):
    """Confidence (integer), present answer and validity per image and category, from the saved post hoc outputs."""
    term, h = ph_load(exp, model, 'spc'); conf = np.full((len(ids), 2), np.nan); Pr = np.zeros((len(ids), 2), bool); v = np.zeros(len(ids), bool)
    for i, n in enumerate(ids):
        x = term.get(n)
        if x and x['status'] == 'valid':
            v[i] = True
            for j, c in enumerate(CATS2): conf[i, j] = float(x['output']['parsed'][c]['confidence']); Pr[i, j] = bool(x['output']['parsed'][c]['present'])
    return conf, Pr, v, h
def stats(x):
    x = np.asarray(x, float)
    if not len(x): return {'n': 0}
    q1, md, q3 = np.percentile(x, [25, 50, 75])
    return {'n': int(len(x)), 'mean': float(x.mean()), 'median': float(md), 'q1': float(q1), 'q3': float(q3)}
def fs(d): return '%d | %s | %s | %s' % (d['n'], '%.1f' % d['mean'] if d['n'] else '-', '%.1f' % d['median'] if d['n'] else '-', '%.1f-%.1f' % (d['q1'], d['q3']) if d['n'] else '-')

f2, M, Bm, TH, B = base()
r_ = {k: read_json(MODE.path('lists', '%s.json' % k))['reference_rate_r'] for k in SETS}
R = {m: {k: raw(EXP[k], m, B[k]['ids']) for k in SETS} for m in MODELS}
# the original scores, exactly as posthoc_partb.conf_scores builds them, and the signed scores
ORIG = {m: {k: pb.conf_scores(EXP[k], m, B[k]['ids']) for k in SETS} for m in MODELS}
SIGN = {}
for m in MODELS:
    for k in SETS:
        conf, Pr, v, h = R[m][k]; S0 = ORIG[m][k][0]
        assert np.array_equal(np.isnan(S0), ~v[:, None].repeat(2, 1)) and np.allclose(S0[v], conf[v] / 100.0) and np.array_equal(ORIG[m][k][1], Pr)
        SIGN.setdefault(m, {})[k] = np.where(Pr, conf / 100.0, 1.0 - conf / 100.0)   # NaN stays NaN for invalid responses
TH0 = read_json(os.path.join(RP, 'confidence_thresholds.json'))['thresholds']; TH0 = {m: np.array([TH0[m][c] for c in CATS2]) for m in MODELS}
for m in MODELS: assert np.allclose(gs.fit(ORIG[m]['calibration'][0], B['calibration']['Y']), TH0[m]), 'original thresholds not reproduced'
TH_S = {m: gs.fit(SIGN[m]['calibration'], B['calibration']['Y']) for m in MODELS}

# ------------------------------------------------------------------ 1. diagnostic
DIAG = {}; D1 = []; D2 = []
for m in MODELS:
    for k in SETS:
        conf, Pr, v, h = R[m][k]; Y = B[k]['Y']
        for j, c in enumerate(CATS2):
            a, y = Pr[:, j], Y[:, j]
            d = {'answer_present': stats(conf[v & a, j]), 'answer_absent': stats(conf[v & ~a, j]),
                 'label_present': stats(conf[v & y, j]), 'label_absent': stats(conf[v & ~y, j]),
                 'answer_absent_confidence_50_or_more': int((v & ~a & (conf[:, j] >= 50)).sum()),
                 'crossed_label_by_answer': {'%s|%s' % (ly, la): stats(conf[v & (y == (ly == 'label_present')) & (a == (la == 'answer_present')), j])
                                             for ly in ('label_present', 'label_absent') for la in ('answer_present', 'answer_absent')},
                 'valid': int(v.sum())}
            DIAG['%s|%s|%s' % (m, k, c)] = d
            D1.append('| %s | %s | %s | %s | %s | %d |' % (m, k, SHORT[c], fs(d['answer_present']), fs(d['answer_absent']), d['answer_absent_confidence_50_or_more']))
            D2.append('| %s | %s | %s | %s | %s |' % (m, k, SHORT[c], fs(d['label_present']), fs(d['label_absent'])))

# ------------------------------------------------------------------ 2. tables
OJ = read_json(os.path.join(RP, 'confidence_baseline.json'))
def same(a, b): return abs(a['micro_f1'] - b['micro_f1']) < 1e-12 and abs(a['precision'] - b['precision']) < 1e-12 and abs(a['recall'] - b['recall']) < 1e-12 and abs(a['false_alarms_per_100_negative'] - b['false_alarms_per_100_negative']) < 1e-9
res = {'POST_HOC': 'signed confidence score, defined after the first scoring of the confidence baselines (D29); no model call', 'written': now(),
       'signed_score': 'confidence/100 if present = true; 1 - confidence/100 if present = false; invalid response = no prediction',
       'method': 'grove_score.fit (grid 0.02-0.98 step 0.02, best single threshold then 2 rounds per category, micro-F1), as experiment 44; fit on the calibration 500; applied unchanged to the final 1,000',
       'thresholds_signed': {m: dict(zip(CATS2, map(float, TH_S[m]))) for m in MODELS}, 'thresholds_original': {m: dict(zip(CATS2, map(float, TH0[m]))) for m in MODELS},
       'diagnostic': DIAG, 'sets': {}, 'original_rows_reproduced': True}
T = {}; PR = {}
for k in ('final', 'calibration'):
    S_ = B[k]; Y, grp = S_['Y'], S_['grp']; rows = {}; L_ = []
    sg = summ(S_['PIG'], Y, S_['vG'], r_[k]); sm = summ(S_['PIM'], Y, S_['vM'], r_[k]); sb = summ(S_['PIsp'], Y, S_['vsp'], r_[k])
    L_ += HEAD + [srow('GROVE (%s, refit thresholds)' % M, sg, gs.boot_ci(S_['PIG'], grp)), srow('main questions (%s, refit thresholds)' % M, sm, gs.boot_ci(S_['PIM'], grp)),
                  srow('single-pass gemma4:31b, frozen prompt (fixed answers)', sb, gs.boot_ci(S_['PIsp'], grp))]
    diffs = []
    for m in MODELS:
        S0, Pr, v, stt, h = ORIG[m][k]; PI0 = gs.fixed(gs.ge(S0, TH0[m]), Y); PIp = gs.fixed(Pr, Y); s0 = summ(PI0, Y, v, r_[k]); sp = summ(PIp, Y, v, r_[k])
        ok = same(s0, OJ['sets'][k]['confidence'][m]['fitted']) and same(sp, OJ['sets'][k]['confidence'][m]['present_answers'])
        if not ok: res['original_rows_reproduced'] = False; raise SystemExit('original row not reproduced: %s %s' % (m, k))
        SS = SIGN[m][k]; PI = gs.fixed(gs.ge(SS, TH_S[m]), Y); ss = summ(PI, Y, v, r_[k])
        L_ += [srow('%s confidence, fitted thresholds (post hoc)' % m, s0, gs.boot_ci(PI0, grp)), srow('%s confidence prompt, its own present answers (post hoc, for reference)' % m, sp, gs.boot_ci(PIp, grp)),
               srow('**%s %s, fitted thresholds**' % (m, NEW), ss, gs.boot_ci(PI, grp))]
        d = gs.boot_diff(S_['PIG'], PI, grp); fa = gs.boot_fa_diff(S_['PIG'], PI, Y, grp); pc = {c: gs.boot_diff(S_['PIG'], PI, grp, cat=j) for j, c in enumerate(CATS2)}
        both = S_['vG'] & v; dvo = gs.boot_diff(S_['PIG'][both], PI[both], grp[both]) if both.sum() >= 2 else None
        diffs.append('- GROVE minus %s %s: micro-F1 %s; Fall %s; PPE %s; false alarms per 100 negatives %+.1f [%+.1f, %+.1f]; valid-only (%d images) %s. Statuses: %s.' % (m, NEW, t3(d), t3(pc['Fall_Hazard']), t3(pc['PPE_Violation']), *fa, both.sum(), t3(dvo) if dvo else '-', stt))
        rows[m] = {'signed_fitted': ss, 'signed_ci': gs.boot_ci(PI, grp), 'GROVE_minus_signed': d, 'GROVE_minus_signed_per_category': pc, 'GROVE_minus_signed_false_alarms': fa, 'valid_only': dvo, 'statuses': stt,
                   'original_fitted_unchanged': s0, 'original_present_answers_unchanged': sp}
    # average precision
    ug, inv = np.unique(grp, return_inverse=True); Wd = gs._wmat(len(ug), DR, SEED)[:, inv]; W1 = np.ones((1, len(Y)))
    A_ = ['| Category | GROVE | main questions | %s | %s | %s |' % (' | '.join('%s confidence/100' % m for m in MODELS), ' | '.join('%s signed' % m for m in MODELS), ' | '.join('GROVE minus %s signed' % m for m in MODELS)),
          '|---|---|---|' + '---|' * (3 * len(MODELS))]
    apr = {}
    for j, cat in enumerate(CATS2):
        y = Y[:, j]; cur = {}
        for lab, s in [('GROVE', S_['SG'][:, j]), ('main questions', S_['SM'][:, j])] + [('%s confidence/100' % m, ORIG[m][k][0][:, j]) for m in MODELS] + [('%s signed' % m, SIGN[m][k][:, j]) for m in MODELS]:
            s = np.nan_to_num(s, nan=-1.0); _, P1, R1 = off.curve(s, y, W1); _, Pd, Rd = off.curve(s, y, Wd); cur[lab] = (float(off.ap(P1, R1)[0]), off.ap(Pd, Rd), R1[0], P1[0])
        for m in MODELS:
            o = OJ['sets'][k]['average_precision'][cat]['%s confidence' % m]['AP']
            if abs(o - cur['%s confidence/100' % m][0]) > 1e-12: raise SystemExit('original AP not reproduced: %s %s %s' % (m, k, cat))
        cells = ['%.4f [%.4f, %.4f]' % (cur[l][0], *off.pct(cur[l][1])) for l in cur]
        dd = ['%+.4f [%+.4f, %+.4f]' % (cur['GROVE'][0] - cur['%s signed' % m][0], *off.pct(cur['GROVE'][1] - cur['%s signed' % m][1])) for m in MODELS]
        A_.append('| %s | %s | %s |' % (SHORT[cat], ' | '.join(cells), ' | '.join(dd)))
        apr[cat] = {l: {'AP': cur[l][0], 'interval': off.pct(cur[l][1])} for l in cur}
        apr[cat]['GROVE_minus_signed'] = {m: [cur['GROVE'][0] - cur['%s signed' % m][0]] + off.pct(cur['GROVE'][1] - cur['%s signed' % m][1]) for m in MODELS}
        PR[(k, cat)] = cur
    T[k] = (L_, diffs, A_); res['sets'][k] = {'GROVE': sg, 'main_question': sm, 'single_pass_gemma4_frozen_prompt': sb, 'models': rows, 'average_precision': apr}

# ------------------------------------------------------------------ figure (final 1,000)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S_ = B['final']; Y = S_['Y']; W1 = np.ones((1, len(Y)))
col = {'GROVE': '#1f5fbf', 'main questions': '#d9822b', 'gemma4:31b': '#2a9d5c', 'qwen3.5:27b': '#8e44ad'}
fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
for j, cat in enumerate(CATS2):
    cur = PR[('final', cat)]; ax = axes[j]; y = Y[:, j]
    for lab, (a, _, R1, P1) in cur.items():
        mdl = lab.split(' ')[0]; c_ = col.get(lab, col.get(mdl)); ls = '--' if lab.endswith('signed') else (':' if lab.endswith('confidence/100') else '-')
        name = 'GROVE (h formula)' if lab == 'GROVE' else (lab.replace('signed', 'signed confidence (post hoc, redefined)') if lab.endswith('signed') else lab)
        ax.step(R1, P1, where='post', color=c_, ls=ls, label='%s, AP %.3f' % (name, a))
    pp, rr = off.point(S_['Psp'][:, j], y, W1); ax.plot(rr[0], pp[0], marker='*', ms=14, ls='none', color='black', label='Single-pass %s (frozen prompt)' % Bm)
    for sysk, S2, mk, cl in (('GROVE', S_['SG'], 'o', col['GROVE']), ('main_question', S_['SM'], 's', col['main questions'])):
        pp, rr = off.point(S2[:, j] >= TH[sysk]['refit'][cat], y, W1); ax.plot(rr[0], pp[0], marker=mk, ms=8, ls='none', mfc='none', mec=cl, mew=2, label='%s, refit thresholds' % ('GROVE' if sysk == 'GROVE' else 'Main questions'))
    for m in MODELS:
        pp, rr = off.point(np.nan_to_num(ORIG[m]['final'][0][:, j], nan=-1.0) >= TH0[m][j], y, W1); ax.plot(rr[0], pp[0], marker='D', ms=7, ls='none', mfc='none', mec=col[m], mew=2, label='%s confidence/100, fitted threshold' % m)
        pp, rr = off.point(np.nan_to_num(SIGN[m]['final'][:, j], nan=-1.0) >= TH_S[m][j], y, W1); ax.plot(rr[0], pp[0], marker='^', ms=8, ls='none', color=col[m], label='%s signed, fitted threshold' % m)
    ax.set_xlim(0, 1.01); ax.set_ylim(0, 1.01); ax.set_xlabel('Recall'); ax.set_ylabel('Precision'); ax.set_title('%s (%d positive images)' % (SHORT[cat], int(y.sum()))); ax.grid(alpha=0.3); ax.legend(fontsize=5.8, loc='lower left')
fig.suptitle('POST HOC: final 1,000 with signed confidence scores added (score redefined after the first scoring; thresholds fit on the calibration 500). Not a planned test.', fontsize=8.5)
fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(OUT_PNG + '.tmp.png', dpi=150); plt.close(fig)

# ------------------------------------------------------------------ report
L = ['# POST HOC: confidence baselines checked and rescored with a signed score', '',
     '**Post hoc analysis, twice over** (D29). Written %s by `code\\posthoc_signed.py`. No model was called. The confidence baselines of `reports\\posthoc_confidence_baseline.md` (D24, Part B) used score = confidence / 100. After that first scoring, the saved answers showed that the models\' confidence describes how sure they are of their own answer, not how likely the violation is (part 1). This report redefines the score **after seeing the first scoring and the diagnostic**: s = confidence / 100 when present = true and s = 1 - confidence / 100 when present = false (an invalid response is no prediction). Every new row is labelled "%s". The original confidence / 100 rows are recomputed from the saved files and thresholds and are identical to `results_posthoc\\confidence_baseline.json` (checked); they are kept unchanged. GROVE, its thresholds, the baseline choice and every frozen result are unchanged; nothing in runs, runs_posthoc, freeze, lists, results or the existing reports changed.' % (now(), NEW), '',
     'Inputs: `runs_posthoc\\p07_cal` and `runs_posthoc\\p07_final` (gemma4:31b and qwen3.5:27b, confidence prompt in `freeze\\posthoc_confidence_prompt.txt`); labels, near-copy groups, GROVE and main-question scores and the single-pass gemma4:31b answers exactly as `code\\posthoc_partb.py` builds them (its functions are imported).', '',
     '## 1. Diagnostic: confidence by answer and by label', '',
     'Valid responses only (all %s). Confidence is the saved integer 0-100. Quartiles: numpy linear interpolation.' % ', '.join('%s %s %d' % (m, k, R[m][k][2].sum()) for m in MODELS for k in SETS), '',
     '### By the model\'s answer', '',
     '| Model | Set | Category | Answer present: n | mean | median | quartiles | Answer absent: n | mean | median | quartiles | Answer absent with confidence >= 50 |',
     '|---|---|---|---:|---:|---:|---|---:|---:|---:|---|---:|'] + D1 + ['', '### By the reference label', '',
     '| Model | Set | Category | Violation present: n | mean | median | quartiles | Violation absent: n | mean | median | quartiles |', '|---|---|---|---:|---:|---:|---|---:|---:|---:|---|'] + D2 + ['',
     'The counts of all four label-by-answer cells, with the same statistics, are in `results_posthoc\\confidence_signed.json` (diagnostic, crossed_label_by_answer).', '',
     '## 2. Signed score: thresholds and results', '',
     'One threshold per category fit on the calibration 500 with `grove_score.fit` (grid 0.02-0.98 step 0.02, best single threshold then 2 rounds per category, micro-F1; the method of experiment 44), applied unchanged to the final 1,000.', '',
     '| Model | Original confidence/100: Fall | PPE | %s: Fall | PPE |' % NEW, '|---|---:|---:|---:|---:|'] + ['| %s | %.2f | %.2f | %.2f | %.2f |' % (m, *TH0[m], *TH_S[m]) for m in MODELS] + ['']
for k in ('final', 'calibration'):
    L_, diffs, A_ = T[k]
    L += ['### %s' % ('Final 1,000 (thresholds from calibration, applied unchanged)' if k == 'final' else 'Calibration 500 (thresholds fit on these images: in-sample, not independent)'), ''] + L_
    L += ['', '**Paired intervals, GROVE minus each signed baseline** (bootstrap, %d draws, seed %d, near-copy groups). The intervals for the original confidence/100 baselines are in `reports\\posthoc_confidence_baseline.md`.' % (DR, SEED), ''] + diffs + ['']
    L += ['Average precision (threshold-free; intervals from the same %d paired draws):' % DR, ''] + A_ + ['']
L += ['Figure: `reports\\posthoc_pr_final_signed.png` (final 1,000; dotted lines confidence/100, dashed lines signed). Numbers in `results_posthoc\\confidence_signed.json`.', '']
os.replace(OUT_PNG + '.tmp.png', OUT_PNG); print('written', OUT_PNG)
pb.new_file(OUT_MD, '\n'.join(L) + '\n'); pb.new_file(OUT_JS, off.jdump(res))
print('thresholds signed', res['thresholds_signed'])
for m in MODELS: print(m, 'final micro-F1 signed %.4f' % res['sets']['final']['models'][m]['signed_fitted']['micro_f1'], 'GROVE minus', t3(res['sets']['final']['models'][m]['GROVE_minus_signed']))
