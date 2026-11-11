"""Experiments 54 and 55: final scoring and the primary test, once (Section 7.7, Section 14 Part 7 Stage J).
Usage: score_final.py [--mode main|pilot] [--i-have-approval]. Refuses if logs\\final_scored.lock exists.
Environment GROVE_TEST_STOP_BEFORE_LOCK=1 stops after the outputs and before the lock (pilot test only)."""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grove_common as gc
from grove_common import *
def attempt(msg):
    with open(MODE.path('logs', 'score_final_attempts.log'), 'a', encoding='utf-8') as f: f.write('%s  %s\n' % (now(), msg))
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--mode', default=os.environ.get('GROVE_MODE', 'main')); ap.add_argument('--i-have-approval', action='store_true'); a = ap.parse_args(argv)
    set_mode(a.mode); import grove_data as gd, grove_score as gs, grove_stages as st, grove_calls as gcl
    lock = MODE.path('logs', 'final_scored.lock'); attempt('start (approval flag %s)' % a.i_have_approval)
    if os.path.exists(lock): attempt('REFUSED: lock exists'); print('REFUSED: final scoring already done (lock exists)'); return 2
    f2p = MODE.path('freeze', 'freeze_2.json'); f2 = read_json(f2p)
    if f2 is None: attempt('REFUSED: no freeze_2.json'); return 4
    if open(f2p[:-5] + '.sha256').read().strip() != sha256_file(f2p): attempt('REFUSED: freeze_2.json changed'); print('REFUSED: freeze_2.json hash mismatch'); return 4
    if {k: sha256_file(MODE.path('lists', k)) for k in f2['list_hashes']} != f2['list_hashes']: attempt('REFUSED: lists changed'); print('REFUSED: list hash mismatch'); return 4
    inc = {k: os.path.exists(MODE.path('results', 'incomplete_%s.json' % k)) for k in ('GROVE', 'baseline')}
    if not (f2['auto_score_final'] and not any(inc.values())) and not a.i_have_approval:
        write_json(MODE.path('logs', 'final_held.json'), {'held': True, 'auto_score_final': f2['auto_score_final'], 'incomplete': inc, 'at': now()})
        attempt('HELD: auto_score_final=%s incomplete=%s' % (f2['auto_score_final'], inc)); print('HELD: final set not scored'); return 3
    M = f2['selection']['main_model']; B = (f2['best_baseline'] or {}).get('best', {}) or {}; Bm = B.get('model')
    preds = [gcl.job_path('e50', M, 'h'), gcl.job_path('e51', M, 'm'), MODE.path('results', 'e53_grounding_predictions.json')] + ([gcl.job_path('e52', Bm, 'sp')] if Bm else [])
    hashes = {'freeze_2.json': sha256_file(f2p), **{'list ' + k: v for k, v in f2['list_hashes'].items()}, **{os.path.relpath(p, MODE.root): (sha256_file(p) if os.path.exists(p) else None) for p in preds}}
    sp_ = MODE.path('logs', 'score_final_start.json'); s0 = read_json(sp_)
    if s0 and s0['hashes'] != hashes: attempt('REFUSED: inputs changed since the first start'); print('REFUSED: inputs changed since first start'); return 5
    if not s0: write_json(sp_, {'hashes': hashes, 'first_start': now()})
    ids = gd.list_ids('final'); Y = gd.Ycs(ids); grp = gd.cs_groups(ids); r = read_json(MODE.path('lists', 'final.json'))['reference_rate_r']; viol = Y.any(1)
    qh, vh, sh = st.load_q('e50', M, 'h', ids); qm, vm, sm = st.load_q('e51', M, 'm', ids)
    SYS = {'GROVE': (np.stack([f_fall(qh), f_ppe(qh)], 1), vh), 'main_question': (st.mq_S(qm, CATS2), vm), 'variant_no_fact_questions': (st.mq_S(qm, CATS2), vm),
           'variant_no_protection': (np.stack([f_fall(qh, protection=False), f_ppe(qh)], 1), vh), 'variant_no_worker': (np.stack([f_fall(qh), f_ppe(qh, worker=False)], 1), vh)}
    TH = f2['final_thresholds']['thresholds']; PI = {}; PIff = {}; valid = {}; R = {'n_images': len(ids), 'n_violation': int(viol.sum()), 'reference_rate_r': r}
    for k, (S, v) in SYS.items():
        t = np.array([TH[k]['refit'][c] for c in CATS2]); PI[k] = gs.fixed(gs.ge(S, t), Y); valid[k] = v
        if TH[k].get('first_freeze'): PIff[k] = gs.fixed(gs.ge(S, np.array([TH[k]['first_freeze'][c] for c in CATS2])), Y)
    if Bm:
        P, v, Bx, _, stt, _ = st.load_sp('e52', Bm, ids, cats=CATS2); PI['best single-pass'] = gs.fixed(P, Y); PIff['best single-pass'] = PI['best single-pass']; valid['best single-pass'] = v; R['baseline_statuses'] = stt
    for k in PI: R[k] = gs.summary(PI[k], Y, CATS2) | {'completion': float(valid[k].mean()), 'prevalence_standardized': gs.prevalence_std(PI[k], viol, r), 'f1_ci': gs.boot_ci(PI[k], grp)}
    R['statuses'] = {'GROVE': st.statuses('e50', M, 'h', ids), 'main_question': st.statuses('e51', M, 'm', ids)}
    crit = {}
    if Bm:
        d = gs.boot_diff(PI['GROVE'], PI['best single-pass'], grp); crit['primary'] = {'difference': d, 'met': bool(d[0] > 0 and d[1] > 0)}
        fa = gs.boot_fa_diff(PI['GROVE'], PI['best single-pass'], Y, grp); crit['secondary_false_alarms'] = {'difference_GROVE_minus_baseline': fa, 'met': bool(fa[0] < 0)}
        both = valid['GROVE'] & valid['best single-pass']; crit['valid_only_sensitivity'] = {'images': int(both.sum()), 'difference': gs.boot_diff(PI['GROVE'][both], PI['best single-pass'][both], grp[both]) if both.sum() >= 2 else None}
        crit['first_freeze_thresholds_sensitivity'] = gs.boot_diff(PIff['GROVE'], PI['best single-pass'], grp) if 'GROVE' in PIff else None
        crit['per_category'] = {c: gs.boot_diff(PI['GROVE'], PI['best single-pass'], grp, cat=j) for j, c in enumerate(CATS2)}
        G = read_json(MODE.path('results', 'e53_grounding_predictions.json'))['items']; top = {(x['image'], x['category']): x['boxes'][:1] for x in G if x['boxes']}
        T = st.true_cs(ids); eg, mg = gs.box_eval(top, T); eb, mb = gs.box_eval(Bx, T); crit['secondary_top_box'] = {'GROVE': eg, 'best single-pass': eb, 'met': bool(eg['iou_0.5']['f1'] >= eb['iou_0.5']['f1'])}
        up5 = {(x['image'], x['category']): x['boxes'][:5] for x in G if x['boxes']}; crit['GROVE_up_to_5_boxes'] = gs.box_eval(up5, T)[0]
    d = gs.boot_diff(PI['GROVE'], PI['main_question'], grp); crit['secondary_main_question'] = {'difference': d, 'met': bool(d[0] > 0)}
    R['criteria'] = crit
    R55 = {k: {'difference_from_GROVE': gs.boot_diff(PI[k], PI['GROVE'], grp), 'summary': R[k]} for k in ('variant_no_fact_questions', 'variant_no_protection', 'variant_no_worker')}
    outs = {MODE.path('results', 'e54_final.json'): json.dumps(R, indent=1, default=float), MODE.path('results', 'e55_removal_final.json'): json.dumps(R55, indent=1, default=float)}
    if Bm: outs[MODE.path('results', 'e54_matches.jsonl')] = '\n'.join(json.dumps(m) for ms in mg.values() for m in ms)
    for p, txt in outs.items():
        with open(p + '.tmp', 'w', encoding='utf-8') as f: f.write(txt)
    for p in outs: os.replace(p + '.tmp', p)
    attempt('outputs written: %s' % {os.path.basename(p): sha256_file(p) for p in outs})
    if os.environ.get('GROVE_TEST_STOP_BEFORE_LOCK') == '1': attempt('stopped before the lock (test)'); print('STOPPED BEFORE LOCK (test)'); return 6
    write_text(lock, json.dumps({'at': now(), 'outputs': {os.path.basename(p): sha256_file(p) for p in outs}, 'inputs': hashes}, indent=1)); attempt('DONE, lock written')
    print('FINAL SCORED: primary %s' % crit.get('primary')); return 0
if __name__ == '__main__': sys.exit(main())
