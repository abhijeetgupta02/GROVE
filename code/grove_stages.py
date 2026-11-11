"""Stages C to K of Section 14 Part 7. Each experiment saves its outputs; finished experiments are skipped on resume."""
import collections, glob, io, json, math, os, random, shutil, time
import numpy as np
from grove_common import *
import grove_common as gc, grove_calls as gcl, grove_data as gd, grove_score as gs

# ---------------------------------------------------------------- context
class Ctx:
    def __init__(self):
        d = gd.g203(); self.d = d
        self.names = read_json(MODE.path('lists', 'g203_subset.json'))['ids'] if MODE.name == 'pilot' else list(d['names'])
        self.idx = np.array([d['ID'][n] for n in self.names]); self.Y3 = d['Y'](CATS3)[self.idx]; self.groups = d['groups'][self.idx]; self.nums = d['nums'][self.idx]
        self.items = [gcl.item(n, '203') for n in self.names]; self.rep = sorted(self.names)[:20 if MODE.name == 'main' else 10]
        self.cal = gd.list_ids('calibration'); self.fin = gd.list_ids('final')
        self.cal_items = [gcl.item(i, 'cs') for i in self.cal]; self.fin_items = [gcl.item(i, 'cs') for i in self.fin]
        self.ground_limit = None if MODE.name == 'main' else 5; self.e56_n = 20 if MODE.name == 'main' else 3
def done_marker(exp): return MODE.path('results', '%s.done.json' % exp)
def is_done(exp): return os.path.exists(done_marker(exp))
def mark_done(exp, info=None): write_json(done_marker(exp), {'at': now(), **(info or {})})
def save_report(name, lines): write_text(MODE.path('reports', name), '\n'.join(lines) + '\n'); log('report written: ' + name)

def load_q(exp, model, setname, names):
    """Decision outputs as arrays (NaN where not valid). Returns (q, valid, mean seconds)."""
    R = gcl.load_results(exp, model, setname, set(names)); keys = list(SETS[setname]['questions'])
    q = {k: np.full(len(names), np.nan) for k in keys}; valid = np.zeros(len(names), bool); secs = []
    for i, n in enumerate(names):
        r = R.get(n)
        if r and r['status'] == 'valid':
            valid[i] = True; secs.append(r['seconds'])
            for k in keys: q[k][i] = r['output']['probs'][k]
    return q, valid, (float(np.mean(secs)) if secs else float('nan'))
def load_sp(exp, model, names, cats=CATS3):
    R = gcl.load_results(exp, model, 'sp', set(names)); P = np.zeros((len(names), len(cats)), bool); valid = np.zeros(len(names), bool)
    boxes = {}; secs = []; status = collections.Counter(); raw = {}
    for i, n in enumerate(names):
        r = R.get(n); status[r['status'] if r else 'missing'] += 1
        if r and r['status'] == 'valid':
            valid[i] = True; secs.append(r['seconds']); p = r['output']['parsed']; raw[n] = r['output']
            for j, c in enumerate(cats):
                P[i, j] = bool(p[c]['present'])
                b = r['output']['boxes'].get(c)
                if P[i, j] and b: boxes[(n, c)] = [b]
    return P, valid, boxes, (float(np.mean(secs)) if secs else float('nan')), dict(status), raw
def statuses(exp, model, setname, names):
    R = gcl.load_results(exp, model, setname, set(names)); c = collections.Counter(R[n]['status'] if n in R else 'missing' for n in names); return dict(c)
def failed(exp, model, setname): return gcl.model_failed(exp, model, setname)
def run_dec(exp, model, setname, items):
    if failed(exp, model, setname): log('skip %s %s %s: model marked failed' % (exp, model, setname)); return None
    return gcl.run_job(exp, 'decision', model, setname, items)
def run_sp(exp, model, items, setname='sp'):
    if failed(exp, model, setname): log('skip %s %s: model marked failed' % (exp, model)); return None
    return gcl.run_job(exp, 'sp', model, setname, items)

def elec_source(option, model, names, exp_h='e12', exp_m='e11', exp_s0='e13'):
    if option == 'formula': q, v, s = load_q(exp_h, model, 'h', names); return f_elec(q), v, s
    if option == 'S0': q, v, s = load_q(exp_s0, model, 'S0', names); return q['Electrocution_Hazard'], v, s
    q, v, s = load_q(exp_m, model, 'm', names); return q['Electrocution_Hazard'], v, s
def grove_S(qh, E, cats):
    cols = {'Fall_Hazard': f_fall(qh), 'PPE_Violation': f_ppe(qh), 'Electrocution_Hazard': E}; return np.stack([cols[c] for c in cats], 1)
def mq_S(qm, cats): return np.stack([qm[c] for c in cats], 1)
def fmt(x, n=4): return '-' if x is None or (isinstance(x, float) and math.isnan(x)) else ('%.*f' % (n, x))
def row_metrics(name, PI, Y, cats, completion, secs=None, extra=''):
    m = gs.summary(PI, Y, cats)
    return '| %s | %s | %.1f/%.1f/%.1f | %s | %s | %s | %s | %s | %s | %s |%s' % (name, fmt(completion, 3), m['TP'], m['FP'], m['FN'], fmt(m['precision']), fmt(m['recall']), fmt(m['micro_f1']),
        fmt(m['macro_f1']), ' / '.join(fmt(m['per_category'][c]['f1'], 3) for c in cats), fmt(m['false_alarms_per_100_negative'], 1), fmt(secs, 1), ' %s |' % extra.strip().replace('|', '/'))
def table_head(cats): return ['| System | Completion | TP/FP/FN | Precision | Recall | Micro-F1 | Macro-F1 | F1 per category (%s) | False alarms per 100 negatives | Seconds per image | Notes |' % ', '.join(SHORT[c] for c in cats),
                              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']

# ---------------------------------------------------------------- Stage C
def stage_C(c):
    for m in GENERATORS: run_sp('e09', m, c.items)
    rep = [gcl.item(n, '203') for n in c.rep]
    for m in ['qwen3.5:9b', 'qwen3.5:27b', 'gemma4:31b']: run_sp('e10', m, rep)
    for exp, st in (('e11', 'm'), ('e12', 'h'), ('e13', 'S0')):
        for m in DECISION: run_dec(exp, m, st, c.items)
    if not is_done('e14'): e14(c)
    if not is_done('e15'): e15(c)

def available_decision(names):
    out = []
    for m in DECISION:
        if failed('e12', m, 'h'): continue
        _, v, _ = load_q('e12', m, 'h', names)
        if v.any(): out.append(m)
    return out
def choose(rows):
    """Section 7.5: best held-out micro-F1; differences of 0.005 or less are ties; ties go to fewer models, then lower runtime."""
    best = max(r['f1'] for r in rows); cand = [r for r in rows if r['f1'] >= best - 0.005 - 1e-12]
    return sorted(cand, key=lambda r: (r['n_models'], r['runtime'], -r['f1']))[0]
def e14(c):
    names, Y, grp = c.names, c.Y3, c.groups; mains = available_decision(names); H = {m: load_q('e12', m, 'h', names) for m in mains}; src = {}
    for m in DECISION:
        for opt, (exp, st) in (('formula', ('e12', 'h')), ('S0', ('e13', 'S0')), ('m', ('e11', 'm'))):
            if failed(exp, m, st): continue
            E, v, s = elec_source(opt, m, names)
            if v.any(): src[(opt, m)] = (E, s)
    rows = []
    for M in mains:
        qh, vh, sh = H[M]
        for (opt, sm), (E, ss) in src.items():
            S = grove_S(qh, E, CATS3); PI, per = gs.cv(S, Y, grp); extra = 0.0 if (opt == 'formula' and sm == M) else (0.0 if math.isnan(ss) else ss)
            rows.append({'main': M, 'electrical_option': opt, 'electrical_model': sm, 'f1': float(gs.f1(PI.sum((0, 1)))), 'repeat_f1': [float(x) for x in per],
                         'n_models': len({M, sm}), 'runtime': (0.0 if math.isnan(sh) else sh) + extra})
    if not rows: raise RuntimeError('experiment 14: no decision model produced valid h outputs')
    sel = choose(rows); others = [r for r in rows if r['main'] != sel['main']]; ru = choose(others) if others else None
    counts = collections.Counter(); rng = np.random.RandomState(SEED)
    for _ in range(10):
        for tr, te in gs.splits(grp, min(5, len(np.unique(grp))), rng):
            tr_rows = []
            for r in rows:
                S = grove_S(H[r['main']][0], src[(r['electrical_option'], r['electrical_model'])][0], CATS3)[tr]
                tr_rows.append(dict(r, f1=float(gs.f1(gs.c3(gs.ge(S, gs.fit(S, Y[tr])), Y[tr])))))
            w = choose(tr_rows); counts['%s + Electrical %s(%s)' % (w['main'], w['electrical_option'], w['electrical_model'])] += 1
    out = {'main_model': sel['main'], 'electrical_source': {'option': sel['electrical_option'], 'model': sel['electrical_model']}, 'held_out_micro_f1': sel['f1'],
           'n_models': sel['n_models'], 'runtime_seconds_per_image': sel['runtime'], 'runner_up_main_model': ru['main'] if ru else None, 'runner_up_pair': ru,
           'rule': 'Section 7.5: held-out micro-F1 (10 repeats of 5 grouped folds, seed %d); differences <= 0.005 are ties; ties to fewer models, then lower runtime' % SEED,
           'fold_selection_counts': dict(counts.most_common()), 'all_pairs': sorted(rows, key=lambda r: -r['f1']), 'excluded_failed': [m for m in DECISION if m not in mains], 'at': now()}
    write_json(MODE.path('freeze', 'selection.json'), out); mark_done('e14', {'main': sel['main']}); log('selection: %s + Electrical %s(%s) F1 %.4f' % (sel['main'], sel['electrical_option'], sel['electrical_model'], sel['f1']))
def selection(): return read_json(MODE.path('freeze', 'selection.json'))
def grove_203(c, names=None, exp_h='e12'):
    s = selection(); names = names or c.names; qh, vh, sh = load_q(exp_h, s['main_model'], 'h', names); E, ve, se = elec_source(s['electrical_source']['option'], s['electrical_source']['model'], names)
    S = grove_S(qh, E, CATS3); return S, vh & ve, qh
def sp_rank(c):
    """Single-pass models ranked by experiment 9 micro-F1 on the 203 (fixed answers)."""
    out = []
    for m in GENERATORS:
        if failed('e09', m, 'sp'): continue
        P, v, _, s, _, _ = load_sp('e09', m, c.names)
        if v.any(): out.append((float(gs.f1(gs.fixed(P, c.Y3).sum((0, 1)))), float(v.mean()), m))
    return [m for f, cm, m in sorted(out, key=lambda x: (-x[0], -x[1]))]
def e15(c):
    names, Y, grp = c.names, c.Y3, c.groups; L = ['# Screening on the 203 images (experiments 9, 11, 12, 13, 14, 15)', '', 'Generated %s. Held-out scores: 10 repeats of 5 grouped folds (seed %d), thresholds fit on training folds only. Single-pass models give fixed answers (no thresholds). A failed response counts as no prediction.' % (now(), SEED), '']
    L += ['## Table 2. Model screening, Fall, Electrical, PPE', ''] + table_head(CATS3); res = {}; PIs = {}; valid = {}
    for m in GENERATORS:
        P, v, _, s, st, _ = load_sp('e09', m, names); PI = gs.fixed(P, Y); PIs['sp ' + m] = PI; valid['sp ' + m] = v
        L.append(row_metrics('Single-pass %s' % m, PI, Y, CATS3, v.mean(), s, ' statuses %s' % st)); res['single-pass ' + m] = gs.summary(PI, Y, CATS3) | {'completion': float(v.mean()), 'statuses': st}
    for m in DECISION:
        qm, vm, sm = load_q('e11', m, 'm', names); qh, vh, shh = load_q('e12', m, 'h', names); q0, v0, s0 = load_q('e13', m, 'S0', names)
        for lab, S, v, s in (('Main questions only (m) %s' % m, mq_S(qm, CATS3), vm, sm), ('GROVE questions and formula (h) %s' % m, grove_S(qh, f_elec(qh), CATS3), vh, shh), ('Original 7 questions (S0) %s' % m, mq_S(q0, CATS3), v0, s0)):
            if not v.any(): L.append('| %s | 0 | no valid outputs | | | | | | | |' % lab); continue
            PI, per = gs.cv(S, Y, grp); PIs[lab] = PI; valid[lab] = v; L.append(row_metrics(lab, PI, Y, CATS3, v.mean(), s)); res[lab] = gs.summary(PI, Y, CATS3) | {'completion': float(v.mean()), 'repeats': per}
    S, v, _ = grove_203(c); PI, per = gs.cv(S, Y, grp); PIs['GROVE'] = PI; valid['GROVE'] = v; sel = selection()
    L.append(row_metrics('**GROVE** (%s, Electrical %s of %s)' % (sel['main_model'], sel['electrical_source']['option'], sel['electrical_source']['model']), PI, Y, CATS3, v.mean(), sel['runtime_seconds_per_image']))
    res['GROVE'] = gs.summary(PI, Y, CATS3) | {'completion': float(v.mean()), 'repeats': per}
    L += ['', '## Gain from fact questions and the formula, same model (h formula minus m main questions)', '', '| Model | Micro-F1 m | Micro-F1 h | Difference (95% interval, paired bootstrap by scene group) |', '|---|---:|---:|---|']
    for m in DECISION:
        a, b = 'GROVE questions and formula (h) %s' % m, 'Main questions only (m) %s' % m
        if a in PIs and b in PIs:
            d_ = gs.boot_diff(PIs[a], PIs[b], grp); L.append('| %s | %s | %s | %+.4f [%+.4f, %+.4f] |' % (m, fmt(res[b]['micro_f1']), fmt(res[a]['micro_f1']), *d_)); res['gain ' + m] = d_
    rk = sp_rank(c); L += ['', '## GROVE against single-pass models', '']
    for m in rk:
        d_ = gs.boot_diff(PIs['GROVE'], PIs['sp ' + m], grp); res['GROVE minus single-pass ' + m] = d_; L.append('- GROVE minus %s: %+.4f [%+.4f, %+.4f]' % (m, *d_))
    if rk:
        both = valid['GROVE'] & valid['sp ' + rk[0]]
        if both.sum() >= 2:
            d_ = gs.boot_diff(PIs['GROVE'][both], PIs['sp ' + rk[0]][both], grp[both]); L.append('- Valid-only sensitivity (%d images where both are valid), GROVE minus %s: %+.4f [%+.4f, %+.4f]' % (both.sum(), rk[0], *d_))
    L += ['', '## Selection (experiment 14)', '', '- Selected: **%s** for Fall and PPE, Electrical from **%s of %s** (held-out micro-F1 %.4f, %d model(s), %.1f s per image).' % (sel['main_model'], sel['electrical_source']['option'], sel['electrical_source']['model'], sel['held_out_micro_f1'], sel['n_models'], sel['runtime_seconds_per_image']),
          '- Runner-up main model (second-best decision model): %s.' % sel['runner_up_main_model'], '- Excluded (failed): %s' % (sel['excluded_failed'] or 'none'), '', '| Main model | Electrical source | Held-out micro-F1 | Models | Seconds per image |', '|---|---|---:|---:|---:|']
    for r in sel['all_pairs'][:20]: L.append('| %s | %s(%s) | %.4f | %d | %.1f |' % (r['main'], r['electrical_option'], r['electrical_model'], r['f1'], r['n_models'], r['runtime']))
    L += ['', 'Fold selection counts (pair chosen by the rule inside each of the 50 training folds): %s' % json.dumps(sel['fold_selection_counts'])]
    write_json(MODE.path('results', 'e15_screening.json'), res); save_report('screening.md', L); mark_done('e15')

# ---------------------------------------------------------------- Stage D
def stage_D(c):
    if not is_done('e16_21'): e16_21(c)
    s = selection(); runs = [('h', s['main_model'], 'e12')]
    if s['electrical_source']['option'] != 'formula':
        st = s['electrical_source']['option']; runs.append((st, s['electrical_source']['model'], {'S0': 'e13', 'm': 'e11'}[st]))
    for rep in ('e23_rep1', 'e23_rep2'):
        for st, m, _ in runs: run_dec(rep, m, st, c.items)
    if not is_done('e23'): e23(c, runs)
    if not is_done('e24_30'): e24_30(c)
def cv_row(lab, S, v, Y, grp, cats, L, store, secs=None, fitfn=gs.fit):
    PI, per = gs.cv(S, Y, grp, fitfn=fitfn); store[lab] = PI; L.append(row_metrics(lab, PI, Y, cats, v.mean(), secs)); return PI
def e16_21(c):
    names, Y, grp = c.names, c.Y3, c.groups; s = selection(); M = s['main_model']; qh, vh, _ = load_q('e12', M, 'h', names); qm, vm, _ = load_q('e11', M, 'm', names)
    E, ve, _ = elec_source(s['electrical_source']['option'], s['electrical_source']['model'], names); v = vh & ve; P = {}
    L = ['# Removing one part at a time, 203 images (experiments 16 to 21)', '', 'Offline, from saved outputs of %s. Held-out: 10 repeats of 5 grouped folds, seed %d, thresholds fit on training folds only (except experiment 21).' % (M, SEED), ''] + table_head(CATS3)
    G = grove_S(qh, E, CATS3); cv_row('GROVE (as selected)', G, v, Y, grp, CATS3, L, P)
    cv_row('16 Main questions only (m set of %s)' % M, mq_S(qm, CATS3), vm, Y, grp, CATS3, L, P)
    S17 = np.stack([f_fall(qh, protection=False), E, f_ppe(qh)], 1); cv_row('17 No protection term', S17, v, Y, grp, CATS3, L, P)
    S18 = np.stack([f_fall(qh), E, f_ppe(qh, worker=False)], 1); cv_row('18 No worker-visible term', S18, v, Y, grp, CATS3, L, P)
    S19 = grove_S(qh, f_elec(qh), CATS3); cv_row('19 Electrical from the main model (h formula)', S19, vh, Y, grp, CATS3, L, P)
    cv_row('20 One threshold for all categories', G, v, Y, grp, CATS3, L, P, fitfn=gs.fit_single)
    P['21 Fixed 0.5'] = gs.fixed(gs.ge(G, 0.5), Y); L.append(row_metrics('21 Fixed 0.5, nothing tuned', P['21 Fixed 0.5'], Y, CATS3, v.mean()))
    L += ['', '| Change | Micro-F1 change against GROVE (95% interval, paired bootstrap by scene group) |', '|---|---|']; res = {}
    for k in P:
        if k.startswith('GROVE'): continue
        d_ = gs.boot_diff(P[k], P['GROVE (as selected)'], grp); res[k] = d_; L.append('| %s | %+.4f [%+.4f, %+.4f] |' % (k, *d_))
    L += ['', 'Experiment 22 (learned safe-image filter) is not run, as the design states.']
    write_json(MODE.path('results', 'e16_21.json'), {k: gs.summary(v_, Y, CATS3) for k, v_ in P.items()} | {'differences': res}); save_report('removal_tests.md', L); mark_done('e16_21')
def e23(c, runs):
    names, Y = c.names, c.Y3; s = selection(); S0_, v0, qh0 = grove_203(c); th = gs.fit(S0_, Y)
    L = ['# Experiment 23. Rerun of the selected GROVE models twice, 203 images', '', 'Thresholds fit on all 203 images (first-freeze method) applied to the original run and to each rerun.', '', '| Run | Largest probability difference | Largest category-score difference | Decisions changed (of %d) | Valid in both |' % (len(names) * 3), '|---|---:|---:|---:|---:|']
    out = {}
    for rep in ('e23_rep1', 'e23_rep2'):
        qh, vh, _ = load_q(rep, s['main_model'], 'h', names); e = s['electrical_source']
        if e['option'] == 'formula': E, ve = f_elec(qh), vh
        else: qq, ve, _ = load_q(rep, e['model'], e['option'], names); E = qq['Electrocution_Hazard']
        S = grove_S(qh, E, CATS3); both = v0 & vh & ve
        dp = max(float(np.nanmax(np.abs(qh[k][both] - qh0[k][both]))) if both.any() else float('nan') for k in qh)
        ds = float(np.nanmax(np.abs(S[both] - S0_[both]))) if both.any() else float('nan'); ch = int((gs.ge(S, th)[both] != gs.ge(S0_, th)[both]).sum())
        out[rep] = {'max_prob_diff': dp, 'max_score_diff': ds, 'decisions_changed': ch, 'valid_both': int(both.sum())}
        L.append('| %s | %s | %s | %d | %d |' % (rep, fmt(dp, 6), fmt(ds, 6), ch, both.sum()))
    write_json(MODE.path('results', 'e23.json'), out); save_report('repeatability_e23.md', L); mark_done('e23')
def e24_30(c):
    names, Y, grp, nums = c.names, c.Y3, c.groups, c.nums; d = c.d; s = selection(); M = s['main_model']; rk = sp_rank(c); best_sp = rk[0] if rk else None
    L = ['# Robustness on the 203 images (experiments 24 to 30)', '', 'Generated %s. GROVE = %s (Electrical %s of %s). Main-question model = m set of %s. Best single-pass in experiment 9 = %s.' % (now(), M, s['electrical_source']['option'], s['electrical_source']['model'], M, best_sp), '']
    res = {}; G, vG, qh = grove_203(c); qm, vm, _ = load_q('e11', M, 'm', names); MQ = mq_S(qm, CATS3)
    SP = load_sp('e09', best_sp, names) if best_sp else None
    L += ['## Experiment 24. 3, 4 and 7 categories (decision models only)', '']
    C4 = CATS3 + ['Housekeeping_Storage']; Y4 = d['Y'](C4)[c.idx]; Y7 = d['Y'](gd.ALL7)[c.idx]
    L += ['| Decision model | 3 categories (h formula) | 4 categories (h formula + Housekeeping) | 7 categories (S0, raw) |', '|---|---:|---:|---:|']
    for m in DECISION:
        q, v, _ = load_q('e12', m, 'h', names); q0, v0, _ = load_q('e13', m, 'S0', names)
        if not v.any(): continue
        f3 = gs.f1(gs.cv(grove_S(q, f_elec(q), CATS3), Y, grp)[0].sum((0, 1)))
        S4 = np.concatenate([grove_S(q, f_elec(q), CATS3), f_house(q)[:, None]], 1); f4 = gs.f1(gs.cv(S4, Y4, grp)[0].sum((0, 1)))
        f7 = gs.f1(gs.cv(np.stack([q0[k] for k in gd.ALL7], 1), Y7, grp)[0].sum((0, 1))) if v0.any() else float('nan')
        res['e24 ' + m] = {'3': f3, '4': f4, '7': f7}; L.append('| %s | %s | %s | %s |' % (m, fmt(f3), fmt(f4), fmt(f7)))
    L += ['', 'Positive pairs: 3 categories %d, 4 categories %d, 7 categories %d.' % (Y.sum(), Y4.sum(), Y7.sum()), '']
    def block(title, mask, groups=None, cats=CATS3, key=''):
        L.extend(['## ' + title, ''] + table_head(cats)); g_ = (grp if groups is None else groups)[mask]; ci = [CATS3.index(x) for x in cats]; Yc = Y[mask][:, ci]
        if mask.sum() < 4 or len(np.unique(g_)) < 2: L.append('| (too few images: %d) |' % mask.sum()); L.append(''); return
        for lab, S, v in (('GROVE', G[:, ci], vG), ('Main-question model', MQ[:, ci], vm)):
            PI, _ = gs.cv(S[mask], Yc, g_); L.append(row_metrics(lab, PI, Yc, cats, v[mask].mean())); res['%s %s' % (key, lab)] = gs.summary(PI, Yc, cats)
        if SP:
            PI = gs.fixed(SP[0][mask][:, ci], Yc); L.append(row_metrics('Single-pass %s' % best_sp, PI, Yc, cats, SP[1][mask].mean())); res['%s single-pass' % key] = gs.summary(PI, Yc, cats)
        L.append('')
    allm = np.ones(len(names), bool)
    block('Experiment 25. Fall and protective equipment only', allm, cats=CATS2, key='e25')
    block('Experiment 26. Excluding the %d AI-tagged images' % int(d['ai'][c.idx].sum()), ~d['ai'][c.idx], key='e26')
    block('Experiment 27. Duplicate file 79 removed', nums != 79, key='e27')
    L += ['## Experiment 28. Each file block held out (thresholds fit on the other blocks)', '', '| System | Pooled micro-F1 | ' + ' | '.join('Block %d-%d' % b for b in gd.BLOCKS) + ' |', '|---|---:|' + '---:|' * len(gd.BLOCKS)]
    for lab, S in (('GROVE', G), ('Main-question model', MQ)):
        PI = gs.blocks_cv(S, Y, nums, gd.BLOCKS); per = []
        for lo, hi in gd.BLOCKS:
            te = (nums >= lo) & (nums <= hi); per.append(fmt(gs.f1(PI[te].sum((0, 1)))) if te.any() else '-')
        res['e28 ' + lab] = gs.f1(PI.sum((0, 1))); L.append('| %s | %s | %s |' % (lab, fmt(res['e28 ' + lab]), ' | '.join(per)))
    L.append('')
    lab_only_removed = d['labeled'][c.idx] & ~Y.any(1)
    block('Experiment 29a. Negatives = all %d images without a scored label (98 unlabeled + 13 labeled only with removed categories in the full set)' % int((~Y.any(1)).sum()), allm, key='e29a')
    block('Experiment 29b. Negatives = only the images with no label at all (the %d labeled only with removed categories are left out)' % int(lab_only_removed.sum()), ~lab_only_removed, key='e29b')
    block('Experiment 30a. Grouped folds (same-scene groups)', allm, key='e30a')
    block('Experiment 30b. Plain random folds (no groups)', allm, groups=np.arange(len(names)), key='e30b')
    write_json(MODE.path('results', 'e24_30.json'), res); save_report('robustness.md', L); mark_done('e24_30')

# ---------------------------------------------------------------- grounding (shared by Stages E, G, I, K)
def fixed_phrase(qh, i, cat):
    keys = list(FIXED_PHRASES[cat]); vals = [qh[k][i] for k in keys]
    if any(np.isnan(vals)): return None, None
    k = keys[int(np.argmax(vals))]; return FIXED_PHRASES[cat][k], k
def flagged_items(names, S, th, cats, limit_images=None):
    F = gs.ge(S, th); out = []; imgs = []
    for i, n in enumerate(names):
        if F[i].any():
            if limit_images is not None and len(imgs) >= limit_images: break
            imgs.append(n); out += [(i, n, c) for j, c in enumerate(cats) if F[i, j]]
    return out
class GCache:
    def __init__(self):
        self.pg = MODE.path('results', 'gcache_gdino.jsonl'); self.pd = MODE.path('results', 'gcache_detr.jsonl')
        self.g = {d['k']: d['v'] for d in read_jsonl(self.pg)}; self.d = {d['k']: d['v'] for d in read_jsonl(self.pd)}
    def gdino(self, gr, pil, sha, phrase):
        k = sha + '|' + phrase
        if k not in self.g:
            t = time.time(); v = {'dets': gr.gdino(pil, phrase), 'seconds': round(time.time() - t, 3)}; self.g[k] = v; append_jsonl(self.pg, {'k': k, 'v': v}); heartbeat()
        return self.g[k]
    def detr(self, gr, pil, sha):
        if sha not in self.d:
            t = time.time(); v = {'dets': gr.detr_dets(pil), 'seconds': round(time.time() - t, 3)}; self.d[sha] = v; append_jsonl(self.pd, {'k': sha, 'v': v}); heartbeat()
        return self.d[sha]
def written_phrases(exp, items_flag, src):
    """qwen3.5:9b writes a phrase or NONE per flagged image and category."""
    its = [gcl.item(n, src, c) for _, n, c in items_flag]
    if its: gcl.run_job(exp, 'phrase', PHRASE_MODEL, 'phrase', its)
    R = gcl.load_results(exp, PHRASE_MODEL, 'phrase'); out = {}
    for _, n, c in items_flag:
        r = R.get('%s|%s' % (n, c)); out[(n, c)] = (r['output']['phrase'] if r and r['status'] == 'valid' else None, r['status'] if r else 'missing')
    return out
def run_grounding(exp, names, src, S, th, cats, qh, methods, limit_images=None, crop=False):
    """methods: list of (label, phrase_kind, search) with phrase_kind fixed|written and search both|gdino|fallback.
    Returns {label: {'top': {(n,c): [box]}, 'up5': {...}, 'items': [...]}}"""
    flag = flagged_items(names, S, th, cats, limit_images); phr = {'fixed': {}, 'written': {}}
    for i, n, c in flag: phr['fixed'][(n, c)] = (fixed_phrase(qh, i, c)[0], 'valid')
    if any(k == 'written' for _, k, _ in methods): phr['written'] = written_phrases(exp + '_phrases', flag, src)
    gcl.unload_all(); import grove_ground as gg; gr = gg.Grounder(); cache = GCache(); out = {}
    try:
        for lab, kind, search in methods:
            top, up5, items = {}, {}, []
            for i, n, c in flag:
                phrase, pst = phr[kind].get((n, c), (None, 'missing')); t0 = time.time()
                rec = {'image': n, 'category': c, 'score': float(S[i, cats.index(c)]), 'phrase': phrase, 'phrase_status': pst, 'boxes': [], 'source': None}
                if phrase and phrase != 'NONE':
                    pil, sha = gg.pil_from_item(gcl.item(n, src)); gd_ = cache.gdino(gr, pil, sha, phrase)['dets'] if search in ('both', 'gdino') else []
                    if gd_: rec['boxes'] = [x['box'] for x in gd_]; rec['source'] = 'GroundingDINO'; rec['logits'] = [x['logit'] for x in gd_]
                    elif search in ('both', 'fallback'):
                        fb = gr.fallback(cache.detr(gr, pil, sha)['dets'], phrase)
                        if fb:
                            rec['boxes'] = [fb['box']]; rec['source'] = 'DETR+OpenCLIP'; rec['fallback'] = fb
                            if crop: rec['crop_similarity'] = gr.crop_sim(pil, fb['box'], phrase)
                rec['no_visible_evidence'] = phrase == 'NONE'; rec['seconds'] = round(time.time() - t0, 3)
                if rec['boxes']: top[(n, c)] = rec['boxes'][:1]; up5[(n, c)] = rec['boxes'][:5]
                items.append(rec)
            out[lab] = {'top': top, 'up5': up5, 'items': items}
    finally:
        gr.close()
    return out, flag
def box_rates(items):
    n = max(len(items), 1)
    return {'flagged': len(items), 'no_box_rate': sum(not x['boxes'] for x in items) / n, 'no_visible_evidence_rate': sum(bool(x.get('no_visible_evidence')) for x in items) / n,
            'share_GroundingDINO': sum(x['source'] == 'GroundingDINO' for x in items) / n, 'share_fallback': sum(x['source'] == 'DETR+OpenCLIP' for x in items) / n,
            'phrase_failures': sum(x['phrase_status'] not in ('valid',) for x in items)}
def box_row(lab, ev, rates=None):
    a, b = ev['iou_0.5'], ev['iou_0.3']
    return '| %s | %d | %d | %d | %s | %s | %s | %s | %d/%d | %s | %s | %s |' % (lab, a['pred_boxes'], a['true_boxes'], a['matched'], fmt(a['precision']), fmt(a['recall']), fmt(a['f1']), fmt(b['f1']),
        a['unmatched_pred'], a['unmatched_true'], fmt(ev['coverage_iog_0.5'], 3), fmt(ev['coverage_iog_0.7'], 3), (' no box %.3f, no visible evidence %.3f, GroundingDINO %.3f, fallback %.3f' % (rates['no_box_rate'], rates['no_visible_evidence_rate'], rates['share_GroundingDINO'], rates['share_fallback'])) if rates else '')
BOX_HEAD = ['| System | Predicted boxes | True boxes | Matched at 0.5 | Box precision | Box recall | Box F1 at 0.5 | Box F1 at 0.3 | Unmatched predicted/true | Coverage IoG 0.5 | Coverage IoG 0.7 | Rates |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
def save_matches(exp, matches):
    p = MODE.path('results', '%s_matches.jsonl' % exp)
    with open(p + '.tmp', 'w', encoding='utf-8') as f:
        for cut, ms in matches.items():
            for m in ms: f.write(json.dumps(m) + '\n')
    os.replace(p + '.tmp', p)
def true_203(names, cats):
    d = gd.g203(); return {(n, c): d['boxes'][(n, c)] for n in names for c in cats if d['boxes'].get((n, c))}
def true_cs(ids, cats=CATS2):
    out = {}
    for i in ids:
        b = gd.cs_boxes(i)
        for c in cats:
            if b[c]: out[(i, c)] = b[c]
    return out

# ---------------------------------------------------------------- Stage E
def stage_E(c):
    if is_done('e31_38'): return
    names, Y = c.names, c.Y3; G, vG, qh = grove_203(c); th = gs.fit(G, Y); T = true_203(names, CATS3)
    write_json(MODE.path('results', 'e_thresholds_all203.json'), {'GROVE': dict(zip(CATS3, th.tolist()))})
    R, flag = run_grounding('e31_32', names, '203', G, th, CATS3, qh, [('31 fixed phrases', 'fixed', 'both'), ('32 written phrases', 'written', 'both')], c.ground_limit)
    ev = {}; L = ['# Grounding on the 203 images (experiments 31 to 38)', '', 'Thresholds fit on all 203 images for the selected GROVE models (%s). Flagged image-category pairs: %d. True boxes: all boxes in the scored categories (%d), including categories the system did not flag. One-to-one matching per image and category (primary cutoff 0.5, also 0.3). Comparisons use the top box per category.' % (dict(zip(CATS3, th.tolist())), len(flag), sum(len(v) for v in T.values())), ''] + BOX_HEAD
    for lab in R:
        e, ms = gs.box_eval(R[lab]['top'], T); ev[lab] = {'top': e, 'rates': box_rates(R[lab]['items'])}; L.append(box_row(lab + ', top box', e, ev[lab]['rates'])); save_matches('e%s' % lab[:2], ms)
    f_fixed = ev['31 fixed phrases']['top']['iou_0.5']['f1']; f_wr = ev['32 written phrases']['top']['iou_0.5']['f1']
    method = 'written' if f_wr > f_fixed + 0.005 else 'fixed'
    write_json(MODE.path('results', 'e33_phrase_method.json'), {'method': method, 'top_box_f1_fixed': f_fixed, 'top_box_f1_written': f_wr, 'rule': 'higher top-box F1 at IoU 0.5; within 0.005 fixed phrases win'})
    L += ['', '**Experiment 33.** Top-box F1 at 0.5: fixed %.4f, written %.4f -> phrase method **%s**.' % (f_fixed, f_wr, method), '']
    R2, _ = run_grounding('e34_36', names, '203', G, th, CATS3, qh, [('34 GroundingDINO only', method, 'gdino'), ('35 DETR + OpenCLIP only', method, 'fallback'), ('36 both, as designed', method, 'both')], c.ground_limit, crop=True)
    L += BOX_HEAD
    for lab in R2:
        e, ms = gs.box_eval(R2[lab]['top'], T); ev[lab] = {'top': e, 'rates': box_rates(R2[lab]['items'])}; L.append(box_row(lab + ', top box', e, ev[lab]['rates'])); save_matches('e%s' % lab[:2], ms)
    e5, _ = gs.box_eval(R2['36 both, as designed']['up5'], T); ev['36 up to 5 boxes'] = {'top': e5}; L.append(box_row('36 both, up to 5 boxes per category (reported separately, never compared with single-pass)', e5))
    L += ['', '**Experiment 37.** Single-pass boxes, same scoring (one box per category when present is true and the box is 4 integers inside the image).', ''] + BOX_HEAD
    for m in GENERATORS:
        P, v, B, _, _, _ = load_sp('e09', m, names)
        if not v.any(): continue
        e, ms = gs.box_eval(B, T); ev['37 single-pass ' + m] = {'top': e}; L.append(box_row('Single-pass ' + m, e)); save_matches('e37_%s' % gcl.safe(m), ms)
    cs = [x['crop_similarity'] for x in R2['36 both, as designed']['items'] if x.get('crop_similarity') is not None]
    L += ['', '**Experiment 38.** OpenCLIP image-crop to phrase similarity for fallback boxes (reported only): n %d, mean %s, min %s, max %s.' % (len(cs), fmt(float(np.mean(cs)) if cs else None, 3), fmt(min(cs) if cs else None, 3), fmt(max(cs) if cs else None, 3))]
    write_json(MODE.path('results', 'e31_38.json'), {'evaluation': ev, 'phrase_method': method, 'items': {k: v['items'] for k, v in {**R, **R2}.items()}})
    save_report('grounding.md', L); mark_done('e31_38')

# ---------------------------------------------------------------- Stage F: first freeze (experiment 39)
def code_hashes():
    d = os.path.join(G, 'code'); return {f: sha256_file(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(('.py', '.ps1'))}
def prompt_files():
    write_json(MODE.path('freeze', 'set_m.json'), SETS['m']); write_text(MODE.path('freeze', 'single_pass_prompt.txt'), SP_PROMPT + '\n\n(qwen models: "\\n/nothink" appended)\n\nSCHEMA:\n' + json.dumps(SP_SCHEMA, indent=1))
    write_text(MODE.path('freeze', 'phrase_prompt.txt'), PHRASE_PROMPT + '\n\nC = ' + json.dumps(CAT_DISPLAY) + '\n(qwen3.5:9b: "\\n/nothink" appended, think false)')
    fs = {'packet prompts.json': os.path.join(PK, 'prompts', 'prompts.json'), 'set_m.json': MODE.path('freeze', 'set_m.json'),
          'single_pass_prompt.txt': MODE.path('freeze', 'single_pass_prompt.txt'), 'phrase_prompt.txt': MODE.path('freeze', 'phrase_prompt.txt')}
    return {k: sha256_file(v) for k, v in fs.items()}
def list_hashes():
    return {f: sha256_file(MODE.path('lists', f)) for f in ('calibration.json', 'final.json') if os.path.exists(MODE.path('lists', f))}
def model_table():
    tags = {x['name']: x for x in gcl.http_json('/api/tags', timeout=60).get('models', [])}
    return {m: {'digest': tags.get(m, {}).get('digest'), 'size': tags.get(m, {}).get('size')} for m in DECISION + GENERATORS}
def stage_F(c):
    p = MODE.path('freeze', 'freeze_1.json')
    if os.path.exists(p): return
    s = selection(); Y = c.Y3; names = c.names; G, vG, qh = grove_203(c); M = s['main_model']; M2 = s['runner_up_main_model']
    qm, _, _ = load_q('e11', M, 'm', names); E, _, _ = elec_source(s['electrical_source']['option'], s['electrical_source']['model'], names)
    thr = {'GROVE': gs.fit(G, Y), 'main_question': gs.fit(mq_S(qm, CATS3), Y),
           'variant_no_protection': gs.fit(np.stack([f_fall(qh, protection=False), E, f_ppe(qh)], 1), Y),
           'variant_no_worker': gs.fit(np.stack([f_fall(qh), E, f_ppe(qh, worker=False)], 1), Y)}
    thr['variant_no_fact_questions'] = thr['main_question']
    if M2: q2, _, _ = load_q('e12', M2, 'h', names); thr['second_GROVE_questions'] = gs.fit(grove_S(q2, f_elec(q2), CATS3), Y)
    obj = {'freeze': 1, 'at': now(), 'mode': MODE.name, 'selection': {k: s[k] for k in ('main_model', 'electrical_source', 'held_out_micro_f1', 'runner_up_main_model', 'rule')},
           'thresholds_fit_on_all_203': {k: dict(zip(CATS3, [float(x) for x in v])) for k, v in thr.items()}, 'formula': FORMULA_TEXT,
           'weights': {'fall_protection': 0.35, 'electrical_testing': 0.40, 'fall_mix': 0.5, 'ppe_mix': 0.5}, 'phrase_method': read_json(MODE.path('results', 'e33_phrase_method.json')),
           'models': model_table(), 'ollama': {'version': gcl.serving_version(), 'exe': OLLAMA_EXE, 'exe_sha256': sha256_file(OLLAMA_EXE)},
           'prompt_hashes': prompt_files(), 'code_hashes': code_hashes(), 'list_hashes': list_hashes(), 'single_pass_options': SP_OPTIONS, 'phrase_options': PHRASE_OPTIONS}
    write_json(p, obj); write_text(p[:-5] + '.sha256', sha256_file(p) + '\n'); log('first freeze written')
def freeze(n): return read_json(MODE.path('freeze', 'freeze_%d.json' % n))
def frozen_th(sysname, cats=CATS2):
    t = freeze(1)['thresholds_fit_on_all_203'][sysname]; return np.array([t[c] for c in cats])

# ---------------------------------------------------------------- Stage G: calibration (experiments 40 to 48)
def cal_systems(c, ids, exps=('e40', 'e41', 'e42')):
    s = selection(); M, M2 = s['main_model'], s['runner_up_main_model']
    qh, vh, sh = load_q(exps[0], M, 'h', ids); qm, vm, sm = load_q(exps[1], M, 'm', ids)
    out = {'GROVE': (np.stack([f_fall(qh), f_ppe(qh)], 1), vh, sh), 'main_question': (mq_S(qm, CATS2), vm, sm),
           'variant_no_fact_questions': (mq_S(qm, CATS2), vm, sm), 'variant_no_protection': (np.stack([f_fall(qh, protection=False), f_ppe(qh)], 1), vh, sh),
           'variant_no_worker': (np.stack([f_fall(qh), f_ppe(qh, worker=False)], 1), vh, sh)}
    if M2 and exps[2]:
        q2, v2, s2 = load_q(exps[2], M2, 'h', ids)
        if v2.any(): out['second_GROVE_questions'] = (np.stack([f_fall(q2), f_ppe(q2)], 1), v2, s2)
    return out, qh
def stage_G(c):
    s = selection(); M, M2 = s['main_model'], s['runner_up_main_model']; gd.prepare_cs(c.cal)
    gcl.run_frozen_job('e40', 'decision', M, 'h', c.cal_items, 'GROVE'); gcl.run_frozen_job('e41', 'decision', M, 'm', c.cal_items, 'main_question')
    if M2: run_dec('e42', M2, 'h', c.cal_items)
    for m in sp_rank(c)[:2]: run_sp('e43', m, c.cal_items)
    if not is_done('e44'): e44(c)
    if not is_done('e45'): e45(c)
    if not is_done('e46'): e46(c)
    if not is_done('e47'): e47(c)
    if not is_done('e48'): e48(c)
def e44(c):
    Y = gd.Ycs(c.cal); systems, _ = cal_systems(c, c.cal); out = {}; res = {}
    for k, (S, v, _) in systems.items():
        fz = frozen_th(k) if k in freeze(1)['thresholds_fit_on_all_203'] else None; rf = gs.fit(S, Y)
        out[k] = {'refit': dict(zip(CATS2, rf.tolist())), 'first_freeze': dict(zip(CATS2, fz.tolist())) if fz is not None else None}
        res[k] = {'refit': gs.summary(gs.fixed(gs.ge(S, rf), Y), Y, CATS2), 'first_freeze': gs.summary(gs.fixed(gs.ge(S, fz), Y), Y, CATS2) if fz is not None else None, 'completion': float(v.mean())}
    write_json(MODE.path('freeze', 'final_thresholds.json'), {'fit_on': 'calibration 500 (refit once, Fall and PPE)', 'method': 'grid 0.02-0.98 step 0.02, best single threshold then 2 rounds per category, micro-F1', 'thresholds': out, 'at': now()})
    write_json(MODE.path('results', 'e44.json'), res); mark_done('e44')
def final_th(k): t = read_json(MODE.path('freeze', 'final_thresholds.json'))['thresholds'][k]['refit']; return np.array([t[c] for c in CATS2])
def e45(c):
    systems, qh = cal_systems(c, c.cal); S = systems['GROVE'][0]; th = final_th('GROVE'); method = read_json(MODE.path('results', 'e33_phrase_method.json'))['method']
    R, flag = run_grounding('e45', c.cal, 'cs', S, th, CATS2, qh, [('45 GROVE grounding', method, 'both')], c.ground_limit, crop=True)
    T = true_cs(c.cal); e, ms = gs.box_eval(R['45 GROVE grounding']['top'], T); save_matches('e45', ms); e5, _ = gs.box_eval(R['45 GROVE grounding']['up5'], T)
    ev = {'GROVE top box': e, 'GROVE up to 5 boxes': e5, 'rates': box_rates(R['45 GROVE grounding']['items'])}
    for m in sp_rank(c)[:2]:
        P, v, B, _, _, _ = load_sp('e43', m, c.cal, cats=CATS2)
        if v.any(): ev['single-pass ' + m], ms2 = gs.box_eval(B, T); save_matches('e45_%s' % gcl.safe(m), ms2)
    write_json(MODE.path('results', 'e45.json'), {'evaluation': ev, 'items': R['45 GROVE grounding']['items'], 'phrase_method': method}); mark_done('e45')
def e46(c):
    Y = gd.Ycs(c.cal); cand = []
    for m in sp_rank(c)[:2]:
        P, v, _, s, st, _ = load_sp('e43', m, c.cal, cats=CATS2)
        if failed('e43', m, 'sp') or not v.any(): continue
        cand.append({'model': m, 'f1': float(gs.f1(gs.fixed(P, Y).sum((0, 1)))), 'completion': float(v.mean()), 'statuses': st, 'seconds': s})
    best = sorted(cand, key=lambda x: (-x['f1'], -x['completion']))[0] if cand else None
    write_json(MODE.path('freeze', 'best_baseline.json'), {'best': best, 'candidates': cand, 'rule': 'higher micro-F1 (Fall, PPE) on the calibration 500', 'at': now()}); mark_done('e46')
def best_baseline(): b = read_json(MODE.path('freeze', 'best_baseline.json')); return (b or {}).get('best')
def night_mask(ids): return np.array([('night' in str(gd.meta()[i].get('illumination') or '').lower()) for i in ids])
def e47(c):
    Y = gd.Ycs(c.cal); systems, qh = cal_systems(c, c.cal); grp = gd.cs_groups(c.cal); nm = night_mask(c.cal); res = {}
    var = {'GROVE': systems['GROVE'][0], 'without f_ppe_novest': np.stack([f_fall(qh), f_ppe(qh, vest=False)], 1), 'without f_fall_opening': np.stack([f_fall(qh, opening=False), f_ppe(qh)], 1)}
    for k, S in var.items():
        PI, _ = gs.cv(S, Y, grp, reps=1, k=5); res[k] = gs.summary(PI, Y, CATS2)
    if nm.sum() >= 4 and len(np.unique(grp[nm])) >= 2:
        PI, _ = gs.cv(var['GROVE'][nm], Y[nm], grp[nm], reps=1, k=5); res['night images only (GROVE)'] = gs.summary(PI, Y[nm], CATS2)
    res['night_image_count'] = int(nm.sum()); res['illumination_values'] = dict(collections.Counter(str(gd.meta()[i].get('illumination')) for i in c.cal))
    write_json(MODE.path('results', 'e47.json'), res); mark_done('e47')
def cs_eval(ids, systems, sp_models, sp_exp, th_kind, Y, r, grp, exp_label):
    """Metrics for new-image sets (Fall, PPE). systems: name -> (S, valid, secs). th_kind: 'refit' or 'first_freeze'."""
    out = {}; PIs = {}; valid = {}; viol = Y.any(1)
    for k, (S, v, s) in systems.items():
        t = read_json(MODE.path('freeze', 'final_thresholds.json'))['thresholds'].get(k, {}).get(th_kind)
        if not t: continue
        PI = gs.fixed(gs.ge(S, np.array([t[c] for c in CATS2])), Y); PIs[k] = PI; valid[k] = v
        out[k] = gs.summary(PI, Y, CATS2) | {'completion': float(v.mean()), 'seconds': s, 'prevalence_standardized': gs.prevalence_std(PI, viol, r)}
    for m in sp_models:
        P, v, _, s, st, _ = load_sp(sp_exp, m, ids, cats=CATS2)
        if not len(v): continue
        PI = gs.fixed(P, Y); PIs['single-pass ' + m] = PI; valid['single-pass ' + m] = v
        out['single-pass ' + m] = gs.summary(PI, Y, CATS2) | {'completion': float(v.mean()), 'seconds': s, 'statuses': st, 'prevalence_standardized': gs.prevalence_std(PI, viol, r)}
    return out, PIs, valid
def subgroup_lines(ids, PI, Y, label):
    """Subgroups of Section 7.3 for one system: clearly visible, size bands, camera_distance, illumination, rule-4-only negatives."""
    M = gd.meta(); share = np.array([gd.largest_scored_share(i) for i in ids]); viol = Y.any(1); vis = read_json(MODE.path('lists', 'calibration.json')).get('visibility_cutoff_largest_box_share', 0)
    L = ['', '#### Subgroups, %s' % label, '', '| Subgroup | Images | Micro-F1 | Recall | False alarms per 100 negatives |', '|---|---:|---:|---:|---:|']
    def row(name, m):
        if m.sum() == 0: L.append('| %s | 0 | - | - | - |' % name); return
        s = gs.summary(PI[m], Y[m], CATS2); L.append('| %s | %d | %s | %s | %s |' % (name, m.sum(), fmt(s['micro_f1']), fmt(s['recall']), fmt(s['false_alarms_per_100_negative'], 1)))
    row('Clearly visible (negatives + violations with largest box share >= %.4f)' % vis, (~viol) | (share >= vis))
    for lo, hi, nm in ((0, 0.01, 'below 1% of image'), (0.01, 0.10, '1% to 10%'), (0.10, 1.01, '10% or more')): row('Hazard size %s (violation images)' % nm, viol & (share >= lo) & (share < hi))
    for key in ('camera_distance', 'illumination'):
        for val, n in sorted(collections.Counter(str(M[i].get(key)) for i in ids).items()): row('%s = %s' % (key, val), np.array([str(M[i].get(key)) == val for i in ids]))
    r4 = np.array([gd.cs_labels(i)['rule4'] for i in ids]) & ~viol; row('Rule-4-only negatives (false alarms)', r4)
    return L
def e48(c):
    ids = c.cal; Y = gd.Ycs(ids); grp = gd.cs_groups(ids); r = read_json(MODE.path('lists', 'calibration.json'))['reference_rate_r']; systems, _ = cal_systems(c, ids); sp = sp_rank(c)[:2]; bb = best_baseline()
    L = ['# Calibration report, %d new images (experiments 40 to 48)' % len(ids), '', 'Generated %s. Fall and protective equipment only. These images tuned thresholds and choose the baseline, so they are not an independent test. Prevalence-standardized precision uses r = %.4f (tuning_sample natural violation rate) and is secondary.' % (now(), r), '']
    res = {}
    for th_kind, title in (('first_freeze', 'Frozen thresholds from the 203 images (first freeze)'), ('refit', 'Thresholds refit once on these images (used on the final set)')):
        out, PIs, valid = cs_eval(ids, systems, sp, 'e43', th_kind, Y, r, grp, 'cal'); res[th_kind] = out
        L += ['## ' + title, ''] + table_head(CATS2)
        for k, PI in PIs.items(): L.append(row_metrics(k, PI, Y, CATS2, out[k]['completion'], out[k].get('seconds'), ' prevalence-standardized P %s F1 %s' % (fmt(out[k]['prevalence_standardized']['precision']), fmt(out[k]['prevalence_standardized']['f1']))))
        if bb and 'GROVE' in PIs and ('single-pass ' + bb['model']) in PIs:
            a, b = PIs['GROVE'], PIs['single-pass ' + bb['model']]; d1 = gs.boot_diff(a, b, grp); d2 = gs.boot_fa_diff(a, b, Y, grp); res[th_kind]['GROVE minus best single-pass'] = {'f1': d1, 'fa': d2}
            L += ['', '- GROVE minus best single-pass (%s), micro-F1: %+.4f [%+.4f, %+.4f]; false alarms per 100 negatives: %+.2f [%+.2f, %+.2f] (paired bootstrap, 4,000 draws, near-copy groups).' % (bb['model'], *d1, *d2)]
            both = valid['GROVE'] & valid['single-pass ' + bb['model']]
            if both.sum() >= 2: dv = gs.boot_diff(a[both], b[both], grp[both]); L.append('- Valid-only sensitivity (%d images): %+.4f [%+.4f, %+.4f]' % (both.sum(), *dv))
        if 'GROVE' in PIs and 'main_question' in PIs: d3 = gs.boot_diff(PIs['GROVE'], PIs['main_question'], grp); L.append('- GROVE minus main-question model: %+.4f [%+.4f, %+.4f]' % d3); res[th_kind]['GROVE minus main-question'] = d3
        if th_kind == 'refit' and 'GROVE' in PIs: L += subgroup_lines(ids, PIs['GROVE'], Y, 'GROVE, refit thresholds')
        L.append('')
    e45r = read_json(MODE.path('results', 'e45.json'), {}); e47r = read_json(MODE.path('results', 'e47.json'), {})
    if e45r:
        L += ['## Grounding on flagged categories (experiment 45, top box)', ''] + BOX_HEAD
        for k, v in e45r['evaluation'].items():
            if k != 'rates': L.append(box_row(k, v, e45r['evaluation']['rates'] if k == 'GROVE top box' else None))
    if e47r:
        L += ['', '## Component sensitivity (experiment 47, reported only)', '', 'Thresholds fit with 5 grouped folds inside these images, held-out folds scored. This shows how much the score rests on these components, not the full effect of the definition difference. Night images: %d (descriptive).' % e47r.get('night_image_count', 0), '', '| Variant | Micro-F1 | Recall | False alarms per 100 negatives |', '|---|---:|---:|---:|']
        for k, v in e47r.items():
            if isinstance(v, dict) and 'micro_f1' in v: L.append('| %s | %s | %s | %s |' % (k, fmt(v['micro_f1']), fmt(v['recall']), fmt(v['false_alarms_per_100_negative'], 1)))
        L.append('- illumination values: %s' % e47r.get('illumination_values'))
    st = {k: statuses(e, m, s_, ids) for k, (e, m, s_) in {'GROVE h': ('e40', selection()['main_model'], 'h'), 'main m': ('e41', selection()['main_model'], 'm')}.items()}
    for m in sp: st['single-pass ' + m] = statuses('e43', m, 'sp', ids)
    L += ['', '## Response status (failure types)', ''] + ['- %s: %s' % (k, v) for k, v in st.items()]
    write_json(MODE.path('results', 'e48.json'), {'results': res, 'statuses': st}); save_report('calibration.md', L); mark_done('e48')

# ---------------------------------------------------------------- Stage H: second freeze (experiment 49)
def incomplete(name): return os.path.exists(MODE.path('results', 'incomplete_%s.json' % name))
def stage_H(c):
    p = MODE.path('freeze', 'freeze_2.json')
    if os.path.exists(p): return
    f1_ = freeze(1); e48r = read_json(MODE.path('results', 'e48.json'))['results']['refit']; bb = best_baseline()
    g = e48r.get('GROVE', {}).get('micro_f1'); b = e48r.get('single-pass ' + bb['model'], {}).get('micro_f1') if bb else None
    auto = bool(g is not None and b is not None and g > b)
    obj = dict(f1_, freeze=2, at=now(), freeze_1_sha256=sha256_file(MODE.path('freeze', 'freeze_1.json')), final_thresholds=read_json(MODE.path('freeze', 'final_thresholds.json')),
               best_baseline=read_json(MODE.path('freeze', 'best_baseline.json')), calibration_micro_f1={'GROVE_refit': g, 'best_single_pass': b},
               auto_score_final=auto, auto_rule='true only if GROVE F1 > best single-pass F1 on the calibration images, using refit thresholds (Section 7.7)',
               incomplete={'GROVE': incomplete('GROVE'), 'baseline': incomplete('baseline')}, code_hashes=code_hashes(), list_hashes=list_hashes())
    write_json(p, obj); write_text(p[:-5] + '.sha256', sha256_file(p) + '\n'); log('second freeze written; auto_score_final=%s' % auto)

# ---------------------------------------------------------------- Stage I: final predictions (experiments 50 to 53). No final labels are read here.
def stage_I(c):
    s = selection(); M = s['main_model']; bb = best_baseline(); gd.prepare_cs(c.fin)
    gcl.run_frozen_job('e50', 'decision', M, 'h', c.fin_items, 'GROVE'); gcl.run_frozen_job('e51', 'decision', M, 'm', c.fin_items, 'main_question')
    if bb: gcl.run_frozen_job('e52', 'sp', bb['model'], 'sp', c.fin_items, 'baseline')
    if not is_done('e53'):
        qh, vh, _ = load_q('e50', M, 'h', c.fin); S = np.stack([f_fall(qh), f_ppe(qh)], 1); th = final_th('GROVE'); method = freeze(2)['phrase_method']['method']
        R, flag = run_grounding('e53', c.fin, 'cs', S, th, CATS2, qh, [('53 GROVE grounding', method, 'both')], c.ground_limit)
        write_json(MODE.path('results', 'e53_grounding_predictions.json'), {'items': R['53 GROVE grounding']['items'], 'phrase_method': method, 'thresholds': dict(zip(CATS2, th.tolist()))}); mark_done('e53')

# ---------------------------------------------------------------- Stage K: reports (experiments 56 to 63)
def final_scored(): return os.path.exists(MODE.path('logs', 'final_scored.lock'))
def final_held(): return os.path.exists(MODE.path('logs', 'final_held.json')) and not final_scored()
def stage_K(c):
    for name, fn in (('e56', e56), ('e57_59', e57_59), ('e60', e60), ('e61', e61), ('e62', e62)):
        if is_done(name): continue
        try: fn(c); mark_done(name)
        except Exception as e:
            import traceback; log('ERROR in %s: %s' % (name, traceback.format_exc())); write_json(MODE.path('results', '%s.failed.json' % name), {'error': traceback.format_exc(), 'at': now()})
    e63(c)
def run_seconds():
    out = []
    for p in sorted(glob.glob(MODE.path('runs', '*', '*.jsonl'))):
        cp = p[:-6] + '.config.json'
        if not os.path.exists(cp): continue
        h = read_json(cp)['config_hash']; term, _, _ = gcl.read_job(p, h); v = [d['seconds'] for d in term.values() if d['status'] == 'valid']
        exp = os.path.basename(os.path.dirname(p)); out.append({'experiment': exp, 'file': os.path.basename(p), 'n': len(term), 'valid': len(v), 'mean_seconds': float(np.mean(v)) if v else None, 'total_hours': sum(d['seconds'] for d in term.values()) / 3600})
    return out
def e56(c):
    s = selection(); M = s['main_model']; e = s['electrical_source']; ids = c.cal[:c.e56_n]; items = [gcl.item(i, 'cs') for i in ids]; res = {'batch': run_seconds(), 'gpu_peaks_mib': read_json(MODE.path('results', 'gpu_peaks.json'), {})}
    stages = [('main model h', 'decision', M, 'h')] + ([('electrical source', 'decision', e['model'], e['option'])] if e['option'] != 'formula' else [])
    per_img = collections.defaultdict(float); st = {}
    for lab, kind, m, setn in stages:
        gcl.unload_all(); gcl.run_job('e56_' + gcl.safe(m) + '_' + setn, kind, m, setn, items)
        R = gcl.load_results('e56_' + gcl.safe(m) + '_' + setn, m, setn); secs = [R[i]['seconds'] for i in ids if i in R]
        warm = secs[1:] if len(secs) > 1 else secs; st[lab] = {'model': m, 'first_call_seconds': secs[0] if secs else None, 'warm_median_seconds': float(np.median(warm)) if warm else None,
                                                             'load_seconds_estimate': (secs[0] - float(np.median(warm))) if len(secs) > 1 else None}
        for i, v in zip(ids[1:], warm if len(secs) > 1 else []): per_img[i] += v
    qh, vh, _ = load_q('e56_' + gcl.safe(M) + '_h', M, 'h', ids); S = np.stack([f_fall(qh), f_ppe(qh)], 1); th = final_th('GROVE') if os.path.exists(MODE.path('freeze', 'final_thresholds.json')) else frozen_th('GROVE')
    flag = flagged_items(ids, S, th, CATS2); method = read_json(MODE.path('results', 'e33_phrase_method.json'))['method']
    if method == 'written' and flag:
        gcl.unload_all(); ph = written_phrases('e56_phrases', flag, 'cs'); R = gcl.load_results('e56_phrases', PHRASE_MODEL, 'phrase')
        for _, n, cc in flag:
            r = R.get('%s|%s' % (n, cc))
            if r: per_img[n] += r['seconds']
        st['phrase step'] = {'model': PHRASE_MODEL, 'items': len(flag)}
    else: ph = {(n, cc): (fixed_phrase(qh, i, cc)[0], 'valid') for i, n, cc in flag}
    gcl.unload_all(); import grove_ground as gg; t0 = time.time(); gr = gg.Grounder(); st['grounding models'] = {'load_seconds': time.time() - t0}
    try:
        for i, n, cc in flag:
            p = ph.get((n, cc), (None,))[0]
            if not p or p == 'NONE': continue
            pil, _ = gg.pil_from_item(gcl.item(n, 'cs')); t = time.time(); b = gr.gdino(pil, p)
            if not b: gr.fallback(gr.detr_dets(pil), p)
            per_img[n] += time.time() - t
        import torch; res['grounding_peak_mib'] = int(torch.cuda.max_memory_allocated() // 2 ** 20) if torch.cuda.is_available() else None
    finally: gr.close()
    v = [per_img[i] for i in ids[1:]]; res['single_image'] = {'images': len(ids), 'stages': st, 'seconds_per_image_models_loaded_mean': float(np.mean(v)) if v else None,
                                                             'seconds_per_image_max': float(np.max(v)) if v else None, 'flagged_items': len(flag), 'note': 'stage-wise with each model already loaded; load times measured separately'}
    write_json(MODE.path('results', 'e56_speed.json'), res)
    L = ['# Experiment 56. Speed and memory (Table 7)', '', '## Batch runs (seconds per image, valid responses)', '', '| Experiment | File | Images | Valid | Mean seconds per image | Total hours |', '|---|---|---:|---:|---:|---:|']
    L += ['| %s | %s | %d | %d | %s | %.2f |' % (r['experiment'], r['file'], r['n'], r['valid'], fmt(r['mean_seconds'], 2), r['total_hours']) for r in res['batch']]
    L += ['', '## Peak graphics memory (MiB, sampled every minute by nvidia-smi)', ''] + ['- %s: %s' % (k, v_) for k, v_ in sorted(res['gpu_peaks_mib'].items())]
    L += ['', '## Single-image speed of the whole GROVE pipeline (%d calibration images, one at a time)' % len(ids), '', '- Seconds per image with models loaded: mean %s, max %s.' % (fmt(res['single_image']['seconds_per_image_models_loaded_mean'], 2), fmt(res['single_image']['seconds_per_image_max'], 2))]
    L += ['- %s: %s' % (k, v_) for k, v_ in st.items()] + ['', 'Batch speed is not single-image speed: batch runs keep one model loaded for the whole set.']
    save_report('speed.md', L)
def sets_for_reports(c):
    """(label, ids, Y, groups, r, PIs dict, valid dict). The final set only after experiment 54 wrote its lock."""
    out = []; s = selection(); bb = best_baseline()
    if os.path.exists(MODE.path('freeze', 'final_thresholds.json')):
        Y = gd.Ycs(c.cal); systems, _ = cal_systems(c, c.cal); o, PIs, val = cs_eval(c.cal, {k: systems[k] for k in ('GROVE', 'main_question') if k in systems}, [bb['model']] if bb else [], 'e43', 'refit', Y, read_json(MODE.path('lists', 'calibration.json'))['reference_rate_r'], None, '')
        out.append(('Calibration (%d images, not independent)' % len(c.cal), c.cal, Y, gd.cs_groups(c.cal), read_json(MODE.path('lists', 'calibration.json'))['reference_rate_r'], PIs, val))
    if final_scored():
        Y = gd.Ycs(c.fin); qh, vh, _ = load_q('e50', s['main_model'], 'h', c.fin); qm, vm, _ = load_q('e51', s['main_model'], 'm', c.fin)
        PIs = {'GROVE': gs.fixed(gs.ge(np.stack([f_fall(qh), f_ppe(qh)], 1), final_th('GROVE')), Y), 'main_question': gs.fixed(gs.ge(mq_S(qm, CATS2), final_th('main_question')), Y)}; val = {'GROVE': vh, 'main_question': vm}
        if bb: P, v, _, _, _, _ = load_sp('e52', bb['model'], c.fin, cats=CATS2); PIs['single-pass ' + bb['model']] = gs.fixed(P, Y); val['single-pass ' + bb['model']] = v
        out.append(('Final test (%d images)' % len(c.fin), c.fin, Y, gd.cs_groups(c.fin), read_json(MODE.path('lists', 'final.json'))['reference_rate_r'], PIs, val))
    return out
def e57_59(c):
    L = ['# Experiments 57 to 59. Per-category results, subgroups, false alarms and prevalence-standardized precision', '', 'Intervals: paired bootstrap, 4,000 draws, seed %d, resampled by related-scene group.' % SEED]
    if final_held(): L += ['', '**The final set is held (experiment 54 did not run automatically). No final-set metric appears here.**']
    res = {}
    for lab, ids, Y, grp, r, PIs, val in sets_for_reports(c):
        L += ['', '## ' + lab, '', '| System | Category | F1 (95% interval) | Precision | Recall |', '|---|---|---|---:|---:|']
        for k, PI in PIs.items():
            for j, cc in enumerate(CATS2):
                ci = gs.boot_ci(PI, grp, cat=j); s_ = gs.summary(PI, Y, CATS2)['per_category'][cc]; L.append('| %s | %s | %.4f [%.4f, %.4f] | %s | %s |' % (k, SHORT[cc], *ci, fmt(s_['precision']), fmt(s_['recall'])))
                res['%s|%s|%s' % (lab, k, cc)] = ci
        L += ['', '| System | False alarms per 100 negative images | Prevalence-standardized precision (95% interval) | Prevalence-standardized F1 (95% interval) | Completion |', '|---|---:|---|---|---:|']
        viol = Y.any(1)
        for k, PI in PIs.items():
            ps = gs.prevalence_std(PI, viol, r); pci, fci = gs.boot_prevalence(PI, viol, r, grp)
            L.append('| %s | %s | %s [%s, %s] | %s [%s, %s] | %s |' % (k, fmt(gs.summary(PI, Y, CATS2)['false_alarms_per_100_negative'], 1), fmt(ps['precision']), fmt(pci[0]), fmt(pci[1]), fmt(ps['f1']), fmt(fci[0]), fmt(fci[1]), fmt(val[k].mean(), 3)))
        L.append('- r = %.4f (natural violation rate of the main pool), p = %.4f in this sample. Top-up images count in their group, so this is performance standardized to that rate under the assumption that the pools are comparable within the violation and no-violation groups.' % (r, viol.mean()))
        for k, PI in PIs.items(): L += subgroup_lines(ids, PI, Y, '%s, %s' % (lab, k))
    write_json(MODE.path('results', 'e57_59.json'), res); save_report('per_category_subgroups.md', L)
def classify_error(text):
    t = (text or '').lower()
    for k, words in (('hidden or occluded equipment', ('hidden', 'occlud', 'not visible', 'cannot see', 'obscur', 'back to', 'from behind')), ('equipment of another worker', ('another worker', 'other worker', 'others')),
                     ('inferred height or depth', ('height', 'high', 'meter', ' m ', 'deep', 'depth', 'edge', 'roof')), ('energized wiring', ('wire', 'electric', 'energ', 'cable')), ('helmet or vest', ('hat', 'helmet', 'vest', 'clothing'))):
        if any(w in t for w in words): return k
    return 'other or no text'
def e60(c):
    ids = c.cal; Y = gd.Ycs(ids); systems, qh = cal_systems(c, ids); S = systems['GROVE'][0]; P = gs.ge(S, final_th('GROVE')); e45r = read_json(MODE.path('results', 'e45.json'), {}); ph = {(x['image'], x['category']): x.get('phrase') for x in e45r.get('items', [])}
    errs = []
    for i, n in enumerate(ids):
        for j, cc in enumerate(CATS2):
            if P[i, j] != Y[i, j]:
                rules = gd.meta()[n]['rules']; reason = ' '.join((rules[k] or {}).get('reason') or '' for k in (('1',) if cc == 'PPE_Violation' else ('2', '3')))
                kind = 'false alarm' if P[i, j] else 'miss'; text = ph.get((n, cc)) if kind == 'false alarm' else reason
                errs.append({'image_id': n, 'category': cc, 'type': kind, 'score': float(S[i, j]), 'phrase': ph.get((n, cc)), 'dataset_reason': reason, 'error_class': classify_error(text if kind == 'miss' else (text or '') + ' ' + reason)})
    pick = sorted(random.Random(SEED).sample(errs, min(100, len(errs))), key=lambda x: (x['type'], x['error_class'], x['image_id']))
    d = MODE.path('reports', 'errors'); os.makedirs(d, exist_ok=True)
    for x in pick:
        src = os.path.join(G, 'tools', 'cs10k_q95', '%s.q95.jpg' % x['image_id']); x['file'] = '%s_%s_%s.jpg' % (x['type'].replace(' ', '_'), SHORT[x['category']], x['image_id']); shutil.copyfile(src, os.path.join(d, x['file']))
    import csv
    with open(os.path.join(d, 'errors.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(pick[0].keys()) if pick else ['image_id']); w.writeheader(); [w.writerow(x) for x in pick]
    cnt = collections.Counter((x['type'], x['error_class']) for x in pick)
    save_report('errors.md', ['# Experiment 60. Sample of false alarms and misses (calibration, GROVE with refit thresholds)', '', 'Total errors %d (false alarms %d, misses %d); sample %d drawn with seed %d; images in `reports\\errors`, table `errors.csv`. Classes come from keywords in the GROVE phrase and the dataset reason, where the text allows it.' % (len(errs), sum(e['type'] == 'false alarm' for e in errs), sum(e['type'] == 'miss' for e in errs), len(pick), SEED), '', '| Type | Class | Count |', '|---|---|---:|'] + ['| %s | %s | %d |' % (a, b, n) for (a, b), n in sorted(cnt.items())])
def e61(c):
    import csv; d = c.d; Y203 = d['Y'](CATS3); rng = random.Random(SEED); M = gd.meta(); vis = read_json(MODE.path('lists', 'calibration.json'))['visibility_cutoff_largest_box_share']
    iaa = {str(r['img']) for r in csv.DictReader(open(os.path.join(gd.D203, 'iaa_matched_pairs.csv'), encoding='utf-8')) if str(r.get('cat_match')).lower() == 'false'}
    def area203(n): W, H = d['dims'].get(n, (1, 1)); return max([((b[2] - b[0]) * (b[3] - b[1])) / (W * H) for cc in CATS3 for b in d['boxes'].get((n, cc), [])] or [1])
    qv = collections.Counter(str(M[i]['quality_of_info']) for i in c.cal); low = 'poor info' if 'poor info' in qv else (sorted(qv)[0] if qv else None)
    P = {'violation': ['203:' + n for n, y in zip(d['names'], Y203.any(1)) if y] + ['cs:' + i for i in c.cal if gd.cs_labels(i)['violation']],
         'no violation': ['203:' + n for n, y in zip(d['names'], Y203.any(1)) if not y] + ['cs:' + i for i in c.cal if not gd.cs_labels(i)['violation']],
         'small or partly hidden': ['203:' + n for n, y in zip(d['names'], Y203.any(1)) if y and area203(n) < 0.01] + ['cs:' + i for i in c.cal if gd.cs_labels(i)['violation'] and gd.largest_scored_share(i) < max(vis, 0.01)],
         'uncertain label': ['203:' + n for n in d['names'] if str(gd.fnum(n)) in iaa] + ['cs:' + i for i in c.cal if str(M[i]['quality_of_info']) == low]}
    want = (('small or partly hidden', 10), ('uncertain label', 10), ('violation', 20), ('no violation', 20)); chosen = []; used = set()
    for k, n in want:
        pool = sorted(x for x in P[k] if x not in used); pk = rng.sample(pool, min(n, len(pool))); chosen += [(k, x) for x in pk]; used |= set(pk)
    rng.shuffle(chosen); out = MODE.path('reports', 'expert_review'); os.makedirs(os.path.join(out, 'images'), exist_ok=True); key = []
    for q, (k, x) in enumerate(chosen, 1):
        code = 'R%02d' % q; src = os.path.join(gd.D203, 'images', x[4:]) if x.startswith('203:') else os.path.join(G, 'tools', 'cs10k_q95', '%s.q95.jpg' % x[3:])
        shutil.copyfile(src, os.path.join(out, 'images', code + os.path.splitext(src)[1].lower())); key.append({'code': code, 'source': x, 'stratum': k})
    with open(os.path.join(out, 'review_form.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['code', 'category', 'present (yes/no)', 'confidence (1-5)', 'reason'])
        for x in key:
            for cc in ('Fall', 'Electrical', 'PPE'): w.writerow([x['code'], cc, '', '', ''])
    write_text(os.path.join(out, 'INSTRUCTIONS.md'), '# Expert review instructions\n\nPlease judge each of the %d images in `images` before you see any model output. Do not look at any GROVE report, prediction or label first.\n\nFor each image and each category, fill one row of `review_form.csv`:\n\n- **Fall**: a worker exposed to falling into an unguarded trench or opening, or from an elevated edge, roof, ladder or scaffold without guardrails or a tied-off harness.\n- **Electrical**: an unprotected electrical hazard, such as damaged or exposed live wiring, makeshift power hookups, or work close to overhead power lines.\n- **PPE**: a visible construction worker missing a required hard hat, high-visibility vest, eye protection or task-specific protective gear (fall harnesses count under Fall).\n\nWrite yes only when the violation is visible in the image. Give a confidence from 1 (guess) to 5 (certain) and one short reason. If equipment may be hidden (body part not visible, too small), say so in the reason.\n\nThe images were drawn with a fixed seed from the development images and the calibration images. The file names are codes and carry no information about labels.\n' % len(key))
    write_json(MODE.path('results', 'e61_key_not_for_reviewer.json'), {'key': key, 'note': 'stratum and source of each code; keep away from the reviewer'})
def e62(c):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from PIL import Image, ImageDraw
    sets = sets_for_reports(c); figs = []
    fig, ax = plt.subplots(figsize=(8, 4)); y = 0; labels = []
    for lab, ids, Y, grp, r, PIs, val in sets:
        for k, PI in PIs.items():
            p, lo, hi = gs.boot_ci(PI, grp); ax.errorbar(p, y, xerr=[[p - lo], [hi - p]], fmt='o', capsize=3); labels.append('%s | %s' % (lab.split(' (')[0], k)); y += 1
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=7); ax.set_xlabel('Micro-F1 (Fall, PPE), 95% interval'); ax.set_title('F1 per system' + (' (final set held)' if final_held() else ''))
    fig.tight_layout(); p2 = MODE.path('reports', 'figure2_f1_intervals.png'); fig.savefig(p2, dpi=150); plt.close(fig); figs.append(p2)
    fig, ax = plt.subplots(figsize=(6, 4))
    for lab, ids, Y, grp, r, PIs, val in sets:
        share = np.array([gd.largest_scored_share(i) for i in ids]); viol = Y.any(1); bands = [(0, 0.01), (0.01, 0.1), (0.1, 1.01)]
        for k, PI in PIs.items():
            rc = [gs.summary(PI[viol & (share >= a) & (share < b)], Y[viol & (share >= a) & (share < b)], CATS2)['recall'] if (viol & (share >= a) & (share < b)).any() else np.nan for a, b in bands]
            ax.plot(['<1%', '1-10%', '>=10%'], rc, marker='o', label='%s | %s' % (lab.split(' (')[0], k))
    ax.set_xlabel('Largest scored box, share of image'); ax.set_ylabel('Recall'); ax.legend(fontsize=6); fig.tight_layout(); p4 = MODE.path('reports', 'figure4_recall_by_size.png'); fig.savefig(p4, dpi=150); plt.close(fig); figs.append(p4)
    e45r = read_json(MODE.path('results', 'e45.json'), {}); items = e45r.get('items', []); T = true_cs(c.cal); Y = gd.Ycs(c.cal); idx = {i: k for k, i in enumerate(c.cal)}
    good = [x for x in items if x['boxes'] and T.get((x['image'], x['category'])) and gs.iou_matrix(x['boxes'][:1], T[(x['image'], x['category'])]).max() >= 0.5]
    fa = [x for x in items if not Y[idx[x['image']], CATS2.index(x['category'])]]; miss = [(i, cc) for (i, cc) in T if not any(x['image'] == i and x['category'] == cc for x in items)]
    rng = random.Random(SEED); ex = [('match', x['image'], x['category'], x['boxes'][:1]) for x in rng.sample(good, min(6, len(good)))] + [('false alarm', x['image'], x['category'], x['boxes'][:1]) for x in rng.sample(fa, min(3, len(fa)))] + [('miss', i, cc, []) for i, cc in rng.sample(miss, min(3, len(miss)))]
    if ex:
        tiles = []
        for kind, i, cc, pb in ex[:12]:
            im = Image.open(os.path.join(G, 'tools', 'cs10k_q95', '%s.q95.jpg' % i)).convert('RGB'); dr = ImageDraw.Draw(im)
            for b in T.get((i, cc), []): dr.rectangle(b, outline=(0, 200, 0), width=4)
            for b in pb: dr.rectangle(b, outline=(230, 0, 0), width=4)
            im.thumbnail((400, 300)); t = Image.new('RGB', (400, 330), 'white'); t.paste(im, (0, 0)); ImageDraw.Draw(t).text((5, 305), '%s | %s | %s (green: label, red: GROVE)' % (kind, SHORT[cc], i), fill='black'); tiles.append(t)
        sheet = Image.new('RGB', (1200, 330 * ((len(tiles) + 2) // 3)), 'white')
        for k, t in enumerate(tiles): sheet.paste(t, ((k % 3) * 400, (k // 3) * 330))
        p3 = MODE.path('reports', 'figure3_examples_calibration.png'); sheet.save(p3); figs.append(p3)
    write_json(MODE.path('results', 'e62_figures.json'), {'figures': figs, 'note': 'examples from the calibration images'})
def _get(d, *ks):
    for k in ks:
        if not isinstance(d, dict): return None
        d = d.get(k)
    return d
def e63(c):
    held = final_held(); scored = final_scored(); f2 = read_json(MODE.path('freeze', 'freeze_2.json'), {}) or {}; sel = read_json(MODE.path('freeze', 'selection.json'), {}) or {}
    inc = [k for k in ('GROVE', 'baseline', 'main_question') if incomplete(k)]; L = ['# GROVE: final results', '']
    if inc: L += ['**INCOMPLETE COMPARISON: %s. A frozen model failed for 12 hours; see logs.**' % ', '.join(inc), '']
    if held: L += ['**THE FINAL SET IS HELD.** GROVE F1 was not higher than the best single-pass F1 on the calibration images (refit thresholds), or a compared system was incomplete, so experiment 54 did not score the final 1,000 images. No final-set metric appears in this file. The owner decides what to do next (score_final.py runs only with `--i-have-approval`).', '']
    elif scored:
        R = read_json(MODE.path('results', 'e54_final.json')); cr = R['criteria']; p = cr.get('primary', {})
        L += ['**Primary criterion %s.** GROVE micro-F1 minus best single-pass micro-F1 on the final %d images (Fall and PPE): %+.4f, 95%% interval [%+.4f, %+.4f].' % ('MET' if p.get('met') else 'NOT MET', R['n_images'], *p.get('difference', [float('nan')] * 3)), '']
    else: L += ['The run stopped before final scoring. See logs\\run.log.', '']
    L += ['Generated %s. Mode: %s. Ollama %s (frozen). Models and digests: `freeze\\freeze_1.json`.' % (now(), MODE.name, OLLAMA_VERSION), '']
    L += ['## Table 1. Datasets', '', '| Set | Images | Positive image-category pairs | Notes |', '|---|---:|---:|---|', '| 203 development images | %d | %d (Fall %d, Electrical %d, PPE %d) | 3 scored categories |' % (len(c.names), c.Y3.sum(), *c.Y3.sum(0))]
    for nm_, ids in (('Calibration', c.cal), ('Final test', c.fin)):
        lj = read_json(MODE.path('lists', '%s.json' % ('calibration' if nm_ == 'Calibration' else 'final')), {}); L.append('| %s | %d | %s | with %s, without %s, top-up %s |' % (nm_, len(ids), '-', lj.get('n_with', '-'), lj.get('n_without', '-'), lj.get('top_up_from_tuning_rest', '-')))
    L += ['', '## Table 2. Model screening', '', 'See `reports\\screening.md`.', '', '## Table 3. Best single-pass, main questions and GROVE', '']
    e15 = read_json(MODE.path('results', 'e15_screening.json'), {}); bb = best_baseline() or {}
    L += ['| Set | System | Micro-F1 | Precision | Recall | False alarms per 100 negatives | Completion |', '|---|---|---:|---:|---:|---:|---:|']
    for k in ('GROVE', 'Main questions only (m) %s' % sel.get('main_model'), 'single-pass %s' % bb.get('model')):
        v = e15.get(k)
        if v: L.append('| 203 (held-out folds, 3 categories) | %s | %s | %s | %s | %s | %s |' % (k, fmt(v['micro_f1']), fmt(v['precision']), fmt(v['recall']), fmt(v['false_alarms_per_100_negative'], 1), fmt(v.get('completion'), 3)))
    cal = _get(read_json(MODE.path('results', 'e48.json'), {}), 'results', 'refit') or {}
    for k in ('GROVE', 'main_question', 'single-pass %s' % bb.get('model')):
        v = cal.get(k)
        if v: L.append('| Calibration (refit, not independent) | %s | %s | %s | %s | %s | %s |' % (k, fmt(v['micro_f1']), fmt(v['precision']), fmt(v['recall']), fmt(v['false_alarms_per_100_negative'], 1), fmt(v.get('completion'), 3)))
    if scored:
        R = read_json(MODE.path('results', 'e54_final.json'))
        for k in ('GROVE', 'main_question', 'best single-pass'):
            v = R.get(k)
            if v: L.append('| **Final test (%d images)** | %s | %s [%s, %s] | %s | %s | %s | %s |' % (len(c.fin), k, fmt(v['micro_f1']), fmt(v['f1_ci'][1]), fmt(v['f1_ci'][2]), fmt(v['precision']), fmt(v['recall']), fmt(v['false_alarms_per_100_negative'], 1), fmt(v['completion'], 3)))
        cr = R['criteria']; L += ['', '- Secondary, false alarms per 100 negatives, GROVE minus baseline: %s (met: %s).' % (cr.get('secondary_false_alarms', {}).get('difference_GROVE_minus_baseline'), cr.get('secondary_false_alarms', {}).get('met')),
                                  '- Secondary, GROVE minus main-question model: %s (met: %s).' % (cr['secondary_main_question']['difference'], cr['secondary_main_question']['met']),
                                  '- Secondary, top-box F1 at 0.5: GROVE %s, best single-pass %s (met: %s).' % (fmt(_get(cr, 'secondary_top_box', 'GROVE', 'iou_0.5', 'f1')), fmt(_get(cr, 'secondary_top_box', 'best single-pass', 'iou_0.5', 'f1')), _get(cr, 'secondary_top_box', 'met')),
                                  '- Valid-only sensitivity: %s. First-freeze thresholds sensitivity: %s.' % (cr.get('valid_only_sensitivity'), cr.get('first_freeze_thresholds_sensitivity'))]
    L += ['', '## Table 4. Per-category results', '', 'See `reports\\per_category_subgroups.md`.', '', '## Table 5. Removing one part at a time', '', 'On the 203 images: `reports\\removal_tests.md`.']
    if scored:
        R55 = read_json(MODE.path('results', 'e55_removal_final.json')); L += ['On the final images (thresholds from freeze_2, unchanged):', ''] + ['- %s: micro-F1 change against GROVE %+.4f [%+.4f, %+.4f]' % (k, *v['difference_from_GROVE']) for k, v in R55.items()]
    L += ['', '## Table 6. Grounding, top box against top box', '', 'On the 203: `reports\\grounding.md`. Calibration: `reports\\calibration.md`.', '', '## Table 7. Speed and memory', '', 'See `reports\\speed.md`.', '']
    L += ['## Completion and failures', ''] + ['- %s' % x for x in completion_lines()]
    L += ['', '## Deviations', '', open(os.path.join(G, 'logs', 'deviations.md'), encoding='utf-8').read() if os.path.exists(os.path.join(G, 'logs', 'deviations.md')) else '-']
    fails = sorted(glob.glob(MODE.path('results', '*.failed.json'))); L += ['', '## Steps that failed', ''] + (['- %s' % os.path.basename(f) for f in fails] or ['- none'])
    st0 = read_json(MODE.path('results', 'run_started.json'), {}); L += ['', 'Total runtime: started %s, finished %s.' % (st0.get('at', '-'), now())]
    save_report('FINAL_RESULTS.md', L)
    zp = os.path.join(G, 'GROVE_results_package.zip') if MODE.name == 'main' else MODE.path('results', 'GROVE_results_package_pilot.zip'); make_zip(zp)
    write_text(MODE.path('logs', 'ALL_DONE.txt'), 'All experiments finished %s. FINAL_RESULTS.md written. Package: %s\n' % (now(), zp)); log('ALL DONE')
def completion_lines():
    out = []
    for p in sorted(glob.glob(MODE.path('runs', '*', '*.jsonl'))):
        cp = p[:-6] + '.config.json'
        if not os.path.exists(cp): continue
        term, _, _ = gcl.read_job(p, read_json(cp)['config_hash']); c = collections.Counter(d['status'] for d in term.values())
        out.append('%s/%s: %d terminal, %s' % (os.path.basename(os.path.dirname(p)), os.path.basename(p), len(term), dict(c)))
    out += ['%s: %s' % (os.path.basename(p), read_json(p)) for p in sorted(glob.glob(MODE.path('runs', '*', '*.model_failed.json')))]
    return out
def make_zip(zp):
    import zipfile
    tmp = zp + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for d in ('runs', 'results', 'reports', 'freeze', 'lists', 'logs'):
            base = getattr(MODE, d)
            for root, dirs, files in os.walk(base):
                if MODE.name == 'main' and d == 'runs' and os.path.normcase(root).startswith(os.path.normcase(os.path.join(G, 'runs', 'pilot'))): continue
                for f in files:
                    if f.endswith(('.tmp', '.lock')) and f != 'final_scored.lock': continue
                    p = os.path.join(root, f); z.write(p, os.path.join(d, os.path.relpath(p, base)))
    os.replace(tmp, zp)
