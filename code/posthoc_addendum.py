"""POST HOC addendum of 2026-11-10 13:12 (logs\\deviations.md, D24 addendum). Offline: no model calls, no refits, new files only.
Needs runs_posthoc\\p06_final (qwen3.5:27b single-pass on the final 1,000, post hoc) to be complete.
  boxv2       reports\\box_upper_bound_v2.md: reports\\box_upper_bound.md unchanged plus a "Final set, qwen3.5:27b" section.
  firstfreeze reports\\first_freeze_scores.md: GROVE and main questions with the first-freeze thresholds (freeze_1.json, unchanged) on the
              calibration 500 and final 1,000, with paired intervals against gemma4:31b and qwen3.5:27b.
  tablesv2    reports\\PAPER_TABLES_v2.md: reports\\PAPER_TABLES.md with the final-set first-freeze entries filled from first_freeze_scores.
Usage: posthoc_addendum.py boxv2|firstfreeze|tablesv2
"""
import json, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import offline_20261110 as off
from grove_common import MODE, G, read_json, now, CATS2, SHORT, SEED, f_fall, f_ppe
import grove_data as gd, grove_score as gs, grove_stages as st, grove_calls as gcl
import box_rescale as br
RP = os.path.join(G, 'results_posthoc'); new_file = off.new_file; t3 = lambda x: '%+.4f [%+.4f, %+.4f]' % tuple(x)
def qwen_final():
    p = os.path.join(G, 'runs_posthoc', 'p06_final', 'qwen3.5_27b__sp.jsonl'); h = read_json(p[:-6] + '.config.json')['config_hash']
    term, _, _ = gcl.read_job(p, h); ids = gd.list_ids('final')
    if len(term) < len(ids): raise SystemExit('p06_final not complete: %d of %d terminal lines' % (len(term), len(ids)))
    return term, ids

def run_boxv2():
    term, ids = qwen_final(); T = st.true_cs(ids, CATS2); grp = gd.cs_groups(ids); gt = off.grove_top('final'); wr, rs = {}, {}; cnt = dict(boxes=0, pixel=0, grid_only=0, neither=0)
    for n in ids:
        x = term[n]
        if x['status'] != 'valid': continue
        W, H = off.img_size(n, 'cs'); p = x['output']['parsed']
        for c in CATS2:
            if p[c]['present'] is not True: continue
            b = p[c]['bbox']; bw = x['output']['boxes'].get(c); px, g_ = br.pixel_box(b, W, H), br.grid_box(b); cnt['boxes'] += 1
            cnt['pixel' if px else ('grid_only' if g_ else 'neither')] += 1
            if bw: wr[(n, c)] = [bw]
            if g_: rs[(n, c)] = [br.to_pixels(b, W, H)]
    res = {'POST_HOC': 'box upper bound, final set, qwen3.5:27b (post hoc run p06_final)', 'written': now(), 'counts': cnt, 'cutoffs': {}}
    L = open(os.path.join(G, 'reports', 'box_upper_bound.md'), encoding='utf-8').read().rstrip('\n').splitlines()
    L += ['', '## Final set, qwen3.5:27b', '',
          '**Post hoc** (D24 addendum), written %s by `code\\posthoc_addendum.py boxv2`. qwen3.5:27b was run on the final 1,000 only after final scoring (`runs_posthoc\\p06_final`, frozen single-pass prompt, same config_hash as its experiment 43 job). Boxes with present = true: %d; fit the pixel rule as written %d, fit only as 0-1000 grid %d, fit neither %d. Same scoring, reading choice and bootstrap (%d draws, seed %d, near-copy groups) as above; everything above this section is the unchanged content of `reports\\box_upper_bound.md`.' % (now(), cnt['boxes'], cnt['pixel'], cnt['grid_only'], cnt['neither'], off.DRAWS, SEED), '',
          '| Cutoff | GROVE top-box F1 | qwen3.5:27b as written | qwen3.5:27b 0-1000 grid | GROVE minus as written (95% interval) | Better reading | GROVE minus better reading (95% interval) |', '|---:|---:|---:|---:|---|---|---|']
    for cut in (0.5, 0.3):
        Cg = off.per_image_counts(gt, T, ids, CATS2, cut); Cw = off.per_image_counts(wr, T, ids, CATS2, cut); Cr = off.per_image_counts(rs, T, ids, CATS2, cut)
        fg, fw, fr = (float(off.box_f1(C.sum(0))) for C in (Cg, Cw, Cr)); take, Cb = ('0-1000 grid', Cr) if fr > fw else ('as written', Cw)
        dw = off.boot_box_diff(Cg, Cw, grp); db = off.boot_box_diff(Cg, Cb, grp)
        L.append('| %.1f | %.4f | %.4f | %.4f | %s | %s | %s |' % (cut, fg, fw, fr, t3(dw), take, t3(db)))
        res['cutoffs'][str(cut)] = {'GROVE': fg, 'as_written': fw, 'grid': fr, 'better': take, 'GROVE_minus_as_written': dw, 'GROVE_minus_better': db}
    L += ['', 'Numbers in `results_posthoc\\box_upper_bound_v2_qwen_final.json`.', '']
    new_file(os.path.join(G, 'reports', 'box_upper_bound_v2.md'), '\n'.join(L) + '\n'); new_file(os.path.join(RP, 'box_upper_bound_v2_qwen_final.json'), off.jdump(res))

def first_freeze_rows():
    f1 = read_json(MODE.path('freeze', 'freeze_1.json'))['thresholds_fit_on_all_203']; f2 = read_json(MODE.path('freeze', 'freeze_2.json')); M = f2['selection']['main_model']
    out = {}; qterm, _ = qwen_final()
    for key, lst, eh, em, esp in (('calibration', 'calibration', 'e40', 'e41', 'e43'), ('final', 'final', 'e50', 'e51', 'e52')):
        ids = gd.list_ids(lst); Y = gd.Ycs(ids); grp = gd.cs_groups(ids); qh, vh, _ = st.load_q(eh, M, 'h', ids); qm, vm, _ = st.load_q(em, M, 'm', ids)
        sysS = {'GROVE': (np.stack([f_fall(qh), f_ppe(qh)], 1), vh), 'main_question': (st.mq_S(qm, CATS2), vm)}
        PI = {k: gs.fixed(gs.ge(S, np.array([f1[k][c] for c in CATS2])), Y) for k, (S, v) in sysS.items()}; V = {k: v for k, (S, v) in sysS.items()}
        Pg, vg, _, _, _, _ = st.load_sp(esp, 'gemma4:31b', ids, cats=CATS2); PI['gemma4:31b'] = gs.fixed(Pg, Y); V['gemma4:31b'] = vg
        if key == 'calibration': Pq, vq, _, _, _, _ = st.load_sp('e43', 'qwen3.5:27b', ids, cats=CATS2)
        else:
            Pq = np.zeros((len(ids), 2), bool); vq = np.zeros(len(ids), bool)
            for i, n in enumerate(ids):
                x = qterm[n]
                if x['status'] == 'valid': vq[i] = True; Pq[i] = [bool(x['output']['parsed'][c]['present']) for c in CATS2]
        PI['qwen3.5:27b'] = gs.fixed(Pq, Y); V['qwen3.5:27b'] = vq
        S_ = {k: gs.summary(PI[k], Y, CATS2) | {'completion': float(V[k].mean()), 'f1_ci': gs.boot_ci(PI[k], grp)} for k in PI}
        D = {}
        for a in ('GROVE', 'main_question'):
            for b in ('gemma4:31b', 'qwen3.5:27b'):
                D['%s minus %s' % (a, b)] = {'micro_f1': gs.boot_diff(PI[a], PI[b], grp), 'per_category': {c: gs.boot_diff(PI[a], PI[b], grp, cat=j) for j, c in enumerate(CATS2)},
                                            'false_alarms': gs.boot_fa_diff(PI[a], PI[b], Y, grp)}
        out[key] = {'summary': S_, 'differences': D, 'thresholds': {k: {c: f1[k][c] for c in CATS2} for k in ('GROVE', 'main_question')}}
    return out, M
def run_firstfreeze():
    out, M = first_freeze_rows(); e48 = read_json(MODE.path('results', 'e48.json'))['results']['first_freeze']
    chk = {k: (round(out['calibration']['summary'][k]['micro_f1'], 10) == round(e48[k]['micro_f1'], 10)) for k in ('GROVE', 'main_question')}
    lab = {'GROVE': 'GROVE (%s, h formula)' % M, 'main_question': 'main questions (%s, m)' % M, 'gemma4:31b': 'single-pass gemma4:31b (fixed answers)', 'qwen3.5:27b': 'single-pass qwen3.5:27b (fixed answers)'}
    L = ['# POST HOC: first-freeze thresholds on the calibration 500 and final 1,000', '',
         '**Post hoc reporting** (D24 addendum), written %s by `code\\posthoc_addendum.py firstfreeze`, after final scoring. GROVE and the main questions are scored with the first-freeze thresholds from `freeze\\freeze_1.json` (fit on all 203 images, unchanged; GROVE Fall %.2f, PPE %.2f; main questions Fall %.2f, PPE %.2f). The design reports first-freeze thresholds as a sensitivity check (Section 7.6); the run saved only GROVE minus best single-pass for them on the final set. The refit thresholds remain primary. Single-pass models give fixed answers. qwen3.5:27b on the final set is the post hoc run `runs_posthoc\\p06_final`. Paired bootstrap, %d draws, seed %d, near-copy groups. No model call, nothing refit.' % (
             now(), out['final']['thresholds']['GROVE']['Fall_Hazard'], out['final']['thresholds']['GROVE']['PPE_Violation'], out['final']['thresholds']['main_question']['Fall_Hazard'], out['final']['thresholds']['main_question']['PPE_Violation'], off.DRAWS, SEED), '',
         'Check: the calibration first-freeze micro-F1 equals the run\'s saved value in `results\\e48.json` (GROVE %s, main questions %s).' % ('yes' if chk['GROVE'] else 'NO', 'yes' if chk['main_question'] else 'NO'), '']
    for key, title in (('final', 'Final 1,000'), ('calibration', 'Calibration 500 (not independent)')):
        o = out[key]; L += ['## ' + title, '', '| System | Thresholds | Micro-F1 [95% interval] | Precision | Recall | F1 Fall | F1 PPE | False alarms per 100 negatives | Completion |', '|---|---|---|---:|---:|---:|---:|---:|---:|']
        for k in ('GROVE', 'main_question', 'gemma4:31b', 'qwen3.5:27b'):
            s = o['summary'][k]; pc = s['per_category']
            L.append('| %s | %s | %.4f [%.4f, %.4f] | %.4f | %.4f | %.4f | %.4f | %.1f | %.3f |' % (lab[k], 'first-freeze' if k in ('GROVE', 'main_question') else 'none (fixed)', s['micro_f1'], s['f1_ci'][1], s['f1_ci'][2], s['precision'], s['recall'], pc['Fall_Hazard']['f1'], pc['PPE_Violation']['f1'], s['false_alarms_per_100_negative'], s['completion']))
        L += ['', '| Comparison (first-freeze thresholds) | Micro-F1 difference | Fall F1 difference | PPE F1 difference | False alarms per 100 negatives difference |', '|---|---|---|---|---|']
        for k, d in o['differences'].items():
            a, b = k.split(' minus '); L.append('| %s minus %s | %s | %s | %s | %+.1f [%+.1f, %+.1f] |' % (lab[a].split(' (')[0], lab[b].split(' (')[0], t3(d['micro_f1']), t3(d['per_category']['Fall_Hazard']), t3(d['per_category']['PPE_Violation']), *d['false_alarms']))
        L.append('')
    L += ['Numbers in `results_posthoc\\first_freeze_scores.json`.', '']
    new_file(os.path.join(G, 'reports', 'first_freeze_scores.md'), '\n'.join(L) + '\n'); new_file(os.path.join(RP, 'first_freeze_scores.json'), off.jdump(out))

def run_tablesv2():
    ff = read_json(os.path.join(RP, 'first_freeze_scores.json'))
    if ff is None: raise SystemExit('run firstfreeze first')
    M = read_json(MODE.path('freeze', 'freeze_2.json'))['selection']['main_model']
    src = open(os.path.join(G, 'reports', 'PAPER_TABLES.md'), encoding='utf-8').read()
    old = '| Final 1,000 | first-freeze | per-system scores | not saved by the run; only GROVE minus best single-pass below | | | | | | - |'
    assert src.count(old) == 1
    rows = []
    for k, lab in (('GROVE', 'GROVE'), ('main_question', 'main questions (%s)' % M)):
        s = ff['final']['summary'][k]; pc = s['per_category']
        rows.append('| Final 1,000 (Fall, PPE) | first-freeze (from the 203; post hoc reporting) | %s | %.4f [%.4f, %.4f] | %.4f | %.4f | %.4f / %.4f | %.1f | %.3f | `reports\\first_freeze_scores.md` (`results_posthoc\\first_freeze_scores.json`) |' % (lab, s['micro_f1'], s['f1_ci'][1], s['f1_ci'][2], s['precision'], s['recall'], pc['Fall_Hazard']['f1'], pc['PPE_Violation']['f1'], s['false_alarms_per_100_negative'], s['completion']))
    out = src.replace(old, '\n'.join(rows))
    head = src.splitlines()[0]
    out = out.replace(head, '# Paper tables, version 2: every number with its source', 1)
    note = ('\n**Version 2** (D24 addendum, written %s by `code\\posthoc_addendum.py tablesv2`): `reports\\PAPER_TABLES.md` unchanged except that the final-set first-freeze entries, not saved by the run, are filled from `reports\\first_freeze_scores.md` (post hoc reporting, thresholds from `freeze_1.json` unchanged). The 203-image first-freeze entry stays marked: the held-out numbers are the right ones there. Box upper bound including qwen3.5:27b on the final set: `reports\\box_upper_bound_v2.md`.\n' % now())
    i = out.index('\n## 1. Datasets'); out = out[:i] + note + out[i:]
    new_file(os.path.join(G, 'reports', 'PAPER_TABLES_v2.md'), out)

if __name__ == '__main__':
    {'boxv2': run_boxv2, 'firstfreeze': run_firstfreeze, 'tablesv2': run_tablesv2}[sys.argv[1]]()
