"""POST HOC Part B scoring of 2026-11-10 (logs\\deviations.md D24), after code\\posthoc_runner.py has finished. No model calls here.
Reads runs_posthoc\\ and the run's saved outputs; writes new files only (reports\\posthoc_*, results_posthoc\\).
  second      Step 6: qwen3.5:27b single-pass on the final 1,000 (frozen prompt), scored like experiment 52/54, GROVE minus qwen3.5:27b with paired intervals.
  confidence  Step 7: confidence-prompt baselines (gemma4:31b, qwen3.5:27b): thresholds fit on the calibration 500 (grid and method of experiment 44),
              applied unchanged to the final 1,000; micro-F1, per category, false alarms, completion, intervals for GROVE minus each; average precision
              and precision-recall figures with the threshold-free analysis.
Usage: posthoc_partb.py second|confidence
"""
import json, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import offline_20261110 as off
from grove_common import MODE, G, read_json, now, CATS2, CATS3, SHORT, SEED, f_fall, f_ppe
import grove_data as gd, grove_score as gs, grove_stages as st, grove_calls as gcl
RP = os.path.join(G, 'results_posthoc'); new_file = off.new_file; DR = off.DRAWS
def t3(x): return '%+.4f [%+.4f, %+.4f]' % tuple(x)
def ph_load(exp, model, setname):
    p = os.path.join(G, 'runs_posthoc', exp, '%s__%s.jsonl' % (gcl.safe(model), setname)); h = read_json(p[:-6] + '.config.json')['config_hash']
    term, _, _ = gcl.read_job(p, h); return term, h
def statuses(term, ids):
    import collections; return dict(collections.Counter(term[i]['status'] if i in term else 'missing' for i in ids))
def base():
    f2 = read_json(MODE.path('freeze', 'freeze_2.json')); M = f2['selection']['main_model']; Bm = f2['best_baseline']['best']['model']; TH = f2['final_thresholds']['thresholds']
    out = {}
    for key, lst, eh, em, esp in (('calibration', 'calibration', 'e40', 'e41', 'e43'), ('final', 'final', 'e50', 'e51', 'e52')):
        ids = gd.list_ids(lst); Y = gd.Ycs(ids); grp = gd.cs_groups(ids); qh, vh, _ = st.load_q(eh, M, 'h', ids); qm, vm, _ = st.load_q(em, M, 'm', ids)
        SG = np.stack([f_fall(qh), f_ppe(qh)], 1); SM = st.mq_S(qm, CATS2)
        PG = gs.fixed(gs.ge(SG, np.array([TH['GROVE']['refit'][c] for c in CATS2])), Y); PM = gs.fixed(gs.ge(SM, np.array([TH['main_question']['refit'][c] for c in CATS2])), Y)
        Psp, vsp, _, _, _, _ = st.load_sp(esp, Bm, ids, cats=CATS2)
        out[key] = dict(ids=ids, Y=Y, grp=grp, SG=SG, SM=SM, PIG=PG, PIM=PM, vG=vh, vM=vm, Psp=Psp, PIsp=gs.fixed(Psp, Y), vsp=vsp)
    return f2, M, Bm, TH, out
def summ(PI, Y, v, r=None):
    s = gs.summary(PI, Y, CATS2); s['completion'] = float(v.mean())
    if r is not None: s['prevalence_standardized'] = gs.prevalence_std(PI, Y.any(1), r)
    return s
def srow(lab, s, ci=None):
    pc = s['per_category']
    return '| %s | %.4f%s | %.4f | %.4f | %.4f / %.4f | %.1f | %.3f |' % (lab, s['micro_f1'], (' [%.4f, %.4f]' % (ci[1], ci[2])) if ci else '', s['precision'], s['recall'], pc['Fall_Hazard']['f1'], pc['PPE_Violation']['f1'], s['false_alarms_per_100_negative'], s['completion'])
HEAD = ['| System | Micro-F1 [95% interval] | Precision | Recall | F1 Fall / PPE | False alarms per 100 negatives | Completion |', '|---|---|---:|---:|---|---:|---:|']

# ------------------------------------------------------------------ step 6
def run_second():
    f2, M, Bm, TH, B = base(); F = B['final']; ids, Y, grp = F['ids'], F['Y'], F['grp']; r = read_json(MODE.path('lists', 'final.json'))['reference_rate_r']
    term, h = ph_load('p06_final', 'qwen3.5:27b', 'sp'); h43 = read_json(os.path.join(G, 'runs', 'e43', 'qwen3.5_27b__sp.config.json'))['config_hash']
    P = np.zeros((len(ids), 2), bool); v = np.zeros(len(ids), bool); wr = {}
    for i, n in enumerate(ids):
        x = term.get(n)
        if x and x['status'] == 'valid':
            v[i] = True
            for j, c in enumerate(CATS2):
                P[i, j] = bool(x['output']['parsed'][c]['present']); b = x['output']['boxes'].get(c)
                if P[i, j] and b: wr[(n, c)] = [b]
    PIq = gs.fixed(P, Y); sq = summ(PIq, Y, v, r); sg = summ(F['PIG'], Y, F['vG'], r); sb = summ(F['PIsp'], Y, F['vsp'], r)
    ciq = gs.boot_ci(PIq, grp); d = gs.boot_diff(F['PIG'], PIq, grp); fa = gs.boot_fa_diff(F['PIG'], PIq, Y, grp); pc = {c: gs.boot_diff(F['PIG'], PIq, grp, cat=j) for j, c in enumerate(CATS2)}
    both = F['vG'] & v; dvo = gs.boot_diff(F['PIG'][both], PIq[both], grp[both]); dqb = gs.boot_diff(PIq, F['PIsp'], grp)
    # boxes: as written, 0-1000 grid reading, upper bound (same as reports\\box_upper_bound.md)
    T = st.true_cs(ids, CATS2); gt = off.grove_top('final'); rs = {}; cnt = dict(boxes=0, pixel=0, grid_only=0, neither=0)
    raw = {n: x['output'] for n, x in term.items() if x['status'] == 'valid'}
    import box_rescale as br
    for n in ids:
        o = raw.get(n)
        if not o: continue
        W, H = off.img_size(n, 'cs')
        for c in CATS2:
            if o['parsed'][c]['present'] is not True: continue
            b = o['parsed'][c]['bbox']; px, g_ = br.pixel_box(b, W, H), br.grid_box(b); cnt['boxes'] += 1
            cnt['pixel' if px else ('grid_only' if g_ else 'neither')] += 1
            if g_: rs[(n, c)] = [br.to_pixels(b, W, H)]
    boxes = {}
    for cut in (0.5, 0.3):
        Cg = off.per_image_counts(gt, T, ids, CATS2, cut); Cw = off.per_image_counts(wr, T, ids, CATS2, cut); Cr = off.per_image_counts(rs, T, ids, CATS2, cut)
        fw, fr = float(off.box_f1(Cw.sum(0))), float(off.box_f1(Cr.sum(0))); take, Cb = ('0-1000 grid', Cr) if fr > fw else ('as written', Cw)
        boxes[str(cut)] = dict(GROVE=float(off.box_f1(Cg.sum(0))), as_written=fw, grid=fr, taken=take, GROVE_minus_as_written=off.boot_box_diff(Cg, Cw, grp), GROVE_minus_upper_bound=off.boot_box_diff(Cg, Cb, grp))
    res = {'POST_HOC': 'second baseline run after final scoring (D24)', 'written': now(), 'config_hash': h, 'config_hash_equals_experiment_43': h == h43, 'statuses': statuses(term, ids),
           'qwen3.5:27b': sq, 'qwen3.5:27b_f1_ci': ciq, 'GROVE': sg, 'gemma4:31b': sb, 'GROVE_minus_qwen': d, 'GROVE_minus_qwen_false_alarms': fa, 'GROVE_minus_qwen_per_category': pc,
           'valid_only': {'images': int(both.sum()), 'difference': dvo}, 'qwen_minus_gemma4': dqb, 'box_counts': cnt, 'boxes': boxes}
    L = ['# POST HOC: second single-pass baseline, qwen3.5:27b on the final 1,000', '',
         '**Post hoc analysis** (D24). Written %s by `code\\posthoc_partb.py second`. qwen3.5:27b was one of the two single-pass models carried to calibration (experiment 43); experiment 46 chose gemma4:31b as the best single-pass, so the run never called qwen3.5:27b on the final set. It was run after final scoring (`code\\posthoc_runner.py`, `runs_posthoc\\p06_final`) with the frozen single-pass prompt and the run\'s own code path, options, image encoding, retries and context: its config_hash equals that of its experiment 43 job (%s). Scored like experiment 54 (fixed answers, Fall and PPE); GROVE uses its frozen refit thresholds. Nothing was refit or changed.' % (now(), 'yes' if h == h43 else 'NO'), '',
         'Statuses: %s.' % res['statuses'], ''] + HEAD + [srow('GROVE (%s, refit thresholds)' % M, sg, read_json(MODE.path('results', 'e54_final.json'))['GROVE'].get('f1_ci')), srow('single-pass qwen3.5:27b (post hoc)', sq, ciq), srow('single-pass gemma4:31b (best single-pass, experiment 52)', sb, read_json(MODE.path('results', 'e54_final.json'))['best single-pass'].get('f1_ci')), '',
         '## GROVE minus qwen3.5:27b (paired bootstrap, %d draws, seed %d, near-copy groups)' % (DR, SEED), '',
         '- Micro-F1: %s.' % t3(d), '- Per category: %s.' % '; '.join('%s %s' % (SHORT[c], t3(x)) for c, x in pc.items()),
         '- False alarms per 100 negative images: %+.1f [%+.1f, %+.1f].' % fa, '- Valid-only (%d images): %s.' % (both.sum(), t3(dvo)),
         '- For reference, qwen3.5:27b minus gemma4:31b micro-F1: %s.' % t3(dqb),
         '- Prevalence-standardized precision / F1: GROVE %.4f / %.4f; qwen3.5:27b %.4f / %.4f; gemma4:31b %.4f / %.4f.' % (sg['prevalence_standardized']['precision'], sg['prevalence_standardized']['f1'], sq['prevalence_standardized']['precision'], sq['prevalence_standardized']['f1'], sb['prevalence_standardized']['precision'], sb['prevalence_standardized']['f1']), '',
         '## Boxes, top box against top box', '', 'qwen3.5:27b boxes with present = true: %d; fit the pixel rule as written %d, fit only as 0-1000 grid %d, fit neither %d (rescaled rows are trusted only when more than half fit only the grid reading: %s).' % (cnt['boxes'], cnt['pixel'], cnt['grid_only'], cnt['neither'], 'trusted' if cnt['boxes'] and cnt['grid_only'] > cnt['boxes'] / 2 else 'not trusted'), '',
         '| Cutoff | GROVE | qwen3.5:27b as written | qwen3.5:27b 0-1000 grid | GROVE minus as written (95% interval) | Upper bound reading | GROVE minus upper bound (95% interval) |', '|---:|---:|---:|---:|---|---|---|']
    for cut, b in boxes.items(): L.append('| %s | %.4f | %.4f | %.4f | %s | %s | %s |' % (cut, b['GROVE'], b['as_written'], b['grid'], t3(b['GROVE_minus_as_written']), b['taken'], t3(b['GROVE_minus_upper_bound'])))
    L += ['', 'Numbers in `results_posthoc\\second_baseline.json`.', '']
    new_file(os.path.join(G, 'reports', 'posthoc_second_baseline.md'), '\n'.join(L) + '\n'); new_file(os.path.join(RP, 'second_baseline.json'), off.jdump(res))

# ------------------------------------------------------------------ step 7
def conf_scores(exp, model, ids):
    term, h = ph_load(exp, model, 'spc'); S = np.full((len(ids), 2), np.nan); Pr = np.zeros((len(ids), 2), bool); v = np.zeros(len(ids), bool)
    for i, n in enumerate(ids):
        x = term.get(n)
        if x and x['status'] == 'valid':
            v[i] = True
            for j, c in enumerate(CATS2): S[i, j] = x['output']['parsed'][c]['confidence'] / 100.0; Pr[i, j] = bool(x['output']['parsed'][c]['present'])
    return S, Pr, v, statuses(term, ids), h
def run_confidence():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    f2, M, Bm, TH, B = base(); models = ['gemma4:31b', 'qwen3.5:27b']; r_ = {k: read_json(MODE.path('lists', '%s.json' % k))['reference_rate_r'] for k in ('calibration', 'final')}
    C = {m: {k: conf_scores('p07_cal' if k == 'calibration' else 'p07_final', m, B[k]['ids']) for k in ('calibration', 'final')} for m in models}
    TH_C = {m: gs.fit(C[m]['calibration'][0], B['calibration']['Y']) for m in models}
    res = {'POST_HOC': 'confidence-score single-pass baselines after final scoring (D24)', 'written': now(), 'thresholds_fit_on_calibration': {m: dict(zip(CATS2, map(float, TH_C[m]))) for m in models}, 'sets': {}}
    new_file(os.path.join(RP, 'confidence_thresholds.json'), off.jdump({'POST_HOC': 'D24', 'method': 'grove_score.fit (grid 0.02-0.98 step 0.02, best single threshold then 2 rounds per category, micro-F1), as experiment 44', 'fit_on': 'calibration 500', 'score': 'confidence / 100; invalid response = no prediction', 'thresholds': res['thresholds_fit_on_calibration']}))
    L = ['# POST HOC: single-pass baselines with a confidence score and a fitted threshold', '',
         '**Post hoc analysis** (D24). Written %s by `code\\posthoc_partb.py confidence`, after final scoring. The frozen single-pass prompt and schema with one change, an integer "confidence" from 0 to 100 for each category ("confidence: how sure you are that this violation is present, 0 to 100"; prompt and schema in `freeze\\posthoc_confidence_prompt.txt`), were run on the calibration 500 and the final 1,000 for gemma4:31b and qwen3.5:27b (`runs_posthoc\\p07_cal`, `runs_posthoc\\p07_final`) with the run\'s code path, options, image encoding, retries and context. Score = confidence / 100 (an invalid response is no prediction). One threshold per category was fit on the calibration 500 with the grid and method of experiment 44 and applied unchanged to the final 1,000. GROVE and the main questions keep their frozen refit thresholds; nothing of GROVE changed.' % now(), '',
         'Thresholds fit on the calibration 500 (`results_posthoc\\confidence_thresholds.json`): %s.' % '; '.join('%s Fall %.2f, PPE %.2f' % (m, *TH_C[m]) for m in models), '']
    pr_data = {}
    for k in ('final', 'calibration'):
        S_ = B[k]; Y, grp = S_['Y'], S_['grp']; rows = {}
        sg = summ(S_['PIG'], Y, S_['vG'], r_[k]); sm = summ(S_['PIM'], Y, S_['vM'], r_[k]); sb = summ(S_['PIsp'], Y, S_['vsp'], r_[k])
        L += ['## %s' % ('Final 1,000 (thresholds from calibration, applied unchanged)' if k == 'final' else 'Calibration 500 (thresholds fit on these images: in-sample, not independent)'), ''] + HEAD
        L += [srow('GROVE (%s, refit thresholds)' % M, sg, gs.boot_ci(S_['PIG'], grp)), srow('main questions (%s, refit thresholds)' % M, sm, gs.boot_ci(S_['PIM'], grp)), srow('single-pass gemma4:31b, frozen prompt (fixed answers)' if True else '', sb, gs.boot_ci(S_['PIsp'], grp))]
        diffs = []
        for m in models:
            S, Pr, v, stt, h = C[m][k]; PI = gs.fixed(gs.ge(S, TH_C[m]), Y); PIp = gs.fixed(Pr, Y); s = summ(PI, Y, v, r_[k]); sp = summ(PIp, Y, v, r_[k])
            L.append(srow('%s confidence, fitted thresholds (post hoc)' % m, s, gs.boot_ci(PI, grp))); L.append(srow('%s confidence prompt, its own present answers (post hoc, for reference)' % m, sp, gs.boot_ci(PIp, grp)))
            d = gs.boot_diff(S_['PIG'], PI, grp); fa = gs.boot_fa_diff(S_['PIG'], PI, Y, grp); pc = {c: gs.boot_diff(S_['PIG'], PI, grp, cat=j) for j, c in enumerate(CATS2)}
            both = S_['vG'] & v; dvo = gs.boot_diff(S_['PIG'][both], PI[both], grp[both]) if both.sum() >= 2 else None
            diffs.append('- GROVE minus %s confidence baseline: micro-F1 %s; Fall %s; PPE %s; false alarms per 100 negatives %+.1f [%+.1f, %+.1f]; valid-only (%d images) %s. Statuses: %s.' % (m, t3(d), t3(pc['Fall_Hazard']), t3(pc['PPE_Violation']), *fa, both.sum(), t3(dvo) if dvo else '-', stt))
            rows[m] = {'fitted': s, 'present_answers': sp, 'GROVE_minus': d, 'GROVE_minus_per_category': pc, 'GROVE_minus_false_alarms': fa, 'valid_only': dvo, 'statuses': stt, 'config_hash': h}
        L += ['', '**Paired intervals** (bootstrap, %d draws, seed %d, near-copy groups):' % (DR, SEED), ''] + diffs + ['']
        # average precision (threshold-free), with the curves of reports\\posthoc_threshold_free.md
        ug, inv = np.unique(grp, return_inverse=True); Wd = gs._wmat(len(ug), DR, SEED)[:, inv]; W1 = np.ones((1, len(Y)))
        L += ['Average precision (threshold-free, post hoc; GROVE and main questions as in `reports\\posthoc_threshold_free.md`):', '', '| Category | GROVE | main questions | %s | GROVE minus %s |' % (' | '.join('%s confidence' % m for m in models), ' | GROVE minus '.join('%s confidence' % m for m in models)), '|---|---|---|' + '---|' * (2 * len(models))]
        apr = {}
        for j, cat in enumerate(CATS2):
            y = Y[:, j]; cur = {}
            for lab, s in [('GROVE', S_['SG'][:, j]), ('main questions', S_['SM'][:, j])] + [('%s confidence' % m, C[m][k][0][:, j]) for m in models]:
                s = np.nan_to_num(s, nan=-1.0); _, P1, R1 = off.curve(s, y, W1); _, Pd, Rd = off.curve(s, y, Wd); cur[lab] = (float(off.ap(P1, R1)[0]), off.ap(Pd, Rd), R1[0], P1[0])
            cells = ['%.4f [%.4f, %.4f]' % (cur[l][0], *off.pct(cur[l][1])) for l in cur]
            dd = ['%+.4f [%+.4f, %+.4f]' % (cur['GROVE'][0] - cur['%s confidence' % m][0], *off.pct(cur['GROVE'][1] - cur['%s confidence' % m][1])) for m in models]
            L.append('| %s | %s | %s |' % (SHORT[cat], ' | '.join(cells), ' | '.join(dd)))
            apr[cat] = {l: {'AP': cur[l][0], 'interval': off.pct(cur[l][1])} for l in cur}; apr[cat]['GROVE_minus'] = {m: [cur['GROVE'][0] - cur['%s confidence' % m][0]] + off.pct(cur['GROVE'][1] - cur['%s confidence' % m][1]) for m in models}
            pr_data[(k, cat)] = (cur, j)
        L += ['', 'Figure: `reports\\posthoc_pr_%s_with_confidence.png`.' % k, '']
        res['sets'][k] = {'GROVE': sg, 'main_question': sm, 'single_pass_gemma4_frozen_prompt': sb, 'confidence': rows, 'average_precision': apr}
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.8)); col = {'GROVE': '#1f5fbf', 'main questions': '#d9822b', 'gemma4:31b confidence': '#2a9d5c', 'qwen3.5:27b confidence': '#8e44ad'}
        for j, cat in enumerate(CATS2):
            cur, _ = pr_data[(k, cat)]; ax = axes[j]; y = Y[:, j]
            for lab, (a, _, R1, P1) in cur.items(): ax.step(R1, P1, where='post', color=col[lab], label='%s, AP %.3f' % (lab if lab != 'GROVE' else 'GROVE (h formula)', a))
            pp, rr = off.point(S_['Psp'][:, j], y, W1); ax.plot(rr[0], pp[0], marker='*', ms=14, ls='none', color='black', label='Single-pass %s (frozen prompt)' % Bm)
            for sysk, S2, mk, cl in (('GROVE', S_['SG'], 'o', col['GROVE']), ('main_question', S_['SM'], 's', col['main questions'])):
                pp, rr = off.point(S2[:, j] >= TH[sysk]['refit'][cat], y, W1); ax.plot(rr[0], pp[0], marker=mk, ms=8, ls='none', mfc='none', mec=cl, mew=2, label='%s, refit thresholds' % ('GROVE' if sysk == 'GROVE' else 'Main questions'))
            for m in models:
                pp, rr = off.point(np.nan_to_num(C[m][k][0][:, j], nan=-1.0) >= TH_C[m][j], y, W1); ax.plot(rr[0], pp[0], marker='D', ms=7, ls='none', mfc='none', mec=col['%s confidence' % m], mew=2, label='%s confidence, fitted threshold' % m)
            ax.set_xlim(0, 1.01); ax.set_ylim(0, 1.01); ax.set_xlabel('Recall'); ax.set_ylabel('Precision'); ax.set_title('%s (%d positive images)' % (SHORT[cat], int(y.sum()))); ax.grid(alpha=0.3); ax.legend(fontsize=6.5, loc='lower left')
        fig.suptitle('POST HOC, threshold-free, with confidence-score baselines: %s. Not a planned test; nothing fit or chosen from it except the stated thresholds.' % ('final 1,000' if k == 'final' else 'calibration 500 (thresholds fit on these images)'), fontsize=9)
        fig.tight_layout(rect=(0, 0, 1, 0.94)); p = os.path.join(G, 'reports', 'posthoc_pr_%s_with_confidence.png' % k)
        if os.path.exists(p): raise SystemExit('REFUSED: %s exists' % p)
        fig.savefig(p, dpi=150); plt.close(fig); print('written', p)
    L += ['Numbers in `results_posthoc\\confidence_baseline.json`. The figures add the confidence curves to the threshold-free figures of `reports\\posthoc_threshold_free.md` (those figures are unchanged).', '']
    new_file(os.path.join(G, 'reports', 'posthoc_confidence_baseline.md'), '\n'.join(L) + '\n'); new_file(os.path.join(RP, 'confidence_baseline.json'), off.jdump(res))

if __name__ == '__main__':
    {'second': run_second, 'confidence': run_confidence}[sys.argv[1]]()
