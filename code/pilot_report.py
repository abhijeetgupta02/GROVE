"""Experiment 8 report: pilot speeds, statuses and the finish estimate for the full run -> reports\\speed_pilot.md (observations appended by hand)."""
import collections, glob, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grove_common import *
P = set_mode('pilot'); import grove_calls as gcl
rows = []; spd = {}
for p in sorted(glob.glob(P.path('runs', '*', '*.jsonl'))):
    cp = p[:-6] + '.config.json'
    if not os.path.exists(cp): continue
    h = read_json(cp)['config_hash']; term, _, _ = gcl.read_job(p, h); exp = os.path.basename(os.path.dirname(p)); f = os.path.basename(p)[:-6]
    s = [d['seconds'] for d in term.values() if d['status'] == 'valid']; st = collections.Counter(d['status'] for d in term.values())
    first = min(term.values(), key=lambda d: d['timestamp'])['seconds'] if term else None
    warm = float(np.median(s[1:] if len(s) > 1 else s)) if s else None
    rows.append((exp, f, len(term), dict(st), float(np.mean(s)) if s else None, warm, first)); spd[(exp, f)] = warm
def w(model, setn, exps):
    v = [spd[(e, '%s__%s' % (gcl.safe(model), setn))] for e in exps if spd.get((e, '%s__%s' % (gcl.safe(model), setn)))]
    return float(np.mean(v)) if v else None
sel = read_json(P.path('freeze', 'selection.json'), {}); M = sel.get('main_model'); M2 = sel.get('runner_up_main_model'); E = (sel.get('electrical_source') or {})
plan = []
for m in GENERATORS: plan.append(('e09 single-pass %s' % m, 203, w(m, 'sp', ['e09'])))
for m in ['qwen3.5:9b', 'qwen3.5:27b', 'gemma4:31b']: plan.append(('e10 repeat %s' % m, 20, w(m, 'sp', ['e10', 'e09'])))
for e_, s_ in (('e11', 'm'), ('e12', 'h'), ('e13', 'S0')):
    for m in DECISION: plan.append(('%s %s %s' % (e_, s_, m), 203, w(m, s_, [e_])))
if M:
    plan.append(('e23 reruns main h x2', 406, w(M, 'h', ['e12'])))
    if E.get('option') and E['option'] != 'formula': plan.append(('e23 reruns electrical x2', 406, w(E['model'], E['option'], {'S0': ['e13'], 'm': ['e11']}[E['option']])))
    plan += [('e40 calibration main h', 500, w(M, 'h', ['e40', 'e12'])), ('e41 calibration main m', 500, w(M, 'm', ['e41', 'e11'])), ('e50 final main h', 1000, w(M, 'h', ['e50', 'e12'])), ('e51 final main m', 1000, w(M, 'm', ['e51', 'e11']))]
if M2: plan.append(('e42 calibration second h', 500, w(M2, 'h', ['e42', 'e12'])))
bb = (read_json(P.path('freeze', 'best_baseline.json'), {}) or {}).get('best') or {}
for m in [x for x in GENERATORS if spd.get(('e43', '%s__sp' % gcl.safe(x)))] or GENERATORS[:2]: plan.append(('e43 calibration single-pass %s' % m, 500, w(m, 'sp', ['e43', 'e09'])))
if bb: plan.append(('e52 final single-pass %s' % bb['model'], 1000, w(bb['model'], 'sp', ['e52', 'e09'])))
ph = [d for p in glob.glob(P.path('runs', '*phrases*', '*.jsonl')) for d in read_jsonl(p)]; phs = float(np.median([d['seconds'] for d in ph])) if ph else 1.0
g = [json.loads(l)['v']['seconds'] for l in open(P.path('results', 'gcache_gdino.jsonl'))] if os.path.exists(P.path('results', 'gcache_gdino.jsonl')) else []
gsec = float(np.median(g)) if g else 1.0
flag_rate = None
e31 = read_json(P.path('results', 'e31_38.json'), {})
if e31: n = len(e31['items'].get('31 fixed phrases', [])); flag_rate = n / 5.0
fr = flag_rate or 1.0
plan += [('phrases + grounding, 203 (fixed and written)', int(203 * fr), 2 * gsec + phs), ('phrases + grounding, calibration', int(500 * fr * 0.7), gsec + phs), ('phrases + grounding, final', int(1000 * fr * 0.7), gsec + phs)]
PZ = lambda label: PAUSE_SECONDS['decision'] if label.split()[0] in ('e11', 'e12', 'e13', 'e23', 'e40', 'e41', 'e42', 'e50', 'e51') else (PAUSE_SECONDS['phrase'] if label.startswith('phrases') else 0.0)
tot = sum(n * ((s or 15.0) + PZ(a_)) for a_, n, s in plan) + 45 * 30  # the pause is part of the estimate, never of any speed figure
speeds = {}
for (e_, f_), v_ in spd.items():
    if v_ is None: continue
    rd = read_json(P.path('runs', e_, f_ + '.config.json'), {}) or {}; cf = rd.get('config') or {}
    if not cf.get('model'): continue
    k_ = '%s|%s%s' % (cf['model'], cf.get('set'), '|cs' if e_ in ('e40', 'e41', 'e42', 'e43', 'e50', 'e51', 'e52') else '')
    if e_ in ('e09', 'e11', 'e12', 'e13', 'e40', 'e41', 'e42', 'e43', 'e50', 'e51', 'e52'): speeds.setdefault(k_, v_)
pilot_top2 = [x for x in GENERATORS if spd.get(('e43', '%s__sp' % gcl.safe(x)))] or GENERATORS[:2]
L = ['# Experiment 8. Pilot: speed, observed problems and finish estimate', '', 'Pilot run %s in `runs\\pilot` (10 images per model and set from the 203; 10 tuning_rest images in neither list in place of the calibration and final lists; grounding on 5 images; every scoring and report step).' % now(), '',
     '## Pilot jobs', '', '| Experiment | Job | Lines | Statuses | Mean seconds (valid) | Median warm seconds | First call seconds (includes load) |', '|---|---|---:|---|---:|---:|---:|']
L += ['| %s | %s | %d | %s | %s | %s | %s |' % (a, b, n, st, '-' if m is None else '%.1f' % m, '-' if wm is None else '%.1f' % wm, '-' if fc is None else '%.1f' % fc) for a, b, n, st, m, wm, fc in rows]
L += ['', '## Finish estimate for the full run', '', ('Median warm seconds from the pilot times planned passes, plus the %.0f s pause before every decision-model and phrase call (the pause is not part of any speed figure), plus about 30 s per model load (45 loads).' % PAUSE_SECONDS['decision'] if PAUSE_SECONDS['decision'] else 'Median warm seconds from the pilot times planned passes (no pause before any call: the 7 s pause was removed on 2026-11-06, D22; the pilot speeds never included it), plus about 30 s per model load (45 loads).') + ' Grounding: %.2f s per GroundingDINO call, %.2f s per phrase call, about %.1f flagged categories per flagged image in the pilot.' % (gsec, phs, fr), '',
      '| Step | Passes | Seconds each (call time) | Pause before each call |', '|---|---:|---:|---:|'] + ['| %s | %d | %s | %s |' % (a, n, '-' if s is None else '%.1f' % s, ('%.0f s' % PZ(a)) if PZ(a) else '-') for a, n, s in plan]
L += ['', '**Estimated compute: %.1f hours (%.1f days).** Unknown speeds counted at 15 s. Retries, the second freeze and reports add a little.' % (tot / 3600, tot / 86400)]
L += ['', '## Tests', '', '- Resume test: %s' % read_json(P.path('results', 'pilot_resume_test.json')), '- score_final lock test: %s' % {k: v for k, v in (read_json(P.path('results', 'pilot_score_final_test.json'), {}) or {}).items() if k in ('identical_outputs', 'lock_exists', 'refused_after_lock', 'pass')},
      '- Acceptance test: %s' % (read_json(os.path.join(G, 'results', 'acceptance_test.json'), {}) or {}).get('all_pass'), '', '## Observations from viewing the pilot outputs', '', '(added below)']
write_text(os.path.join(G, 'reports', 'speed_pilot.md'), '\n'.join(L) + '\n'); write_json(os.path.join(G, 'results', 'e08_pilot_estimate.json'), {'hours': tot / 3600, 'plan': plan, 'speeds': speeds, 'phrase_seconds': phs, 'gdino_seconds': gsec, 'flag_rate': fr,
           'pilot_selection': {k: sel.get(k) for k in ('main_model', 'runner_up_main_model', 'electrical_source')}, 'pilot_top2': pilot_top2, 'pause_seconds': PAUSE_SECONDS}); print('\n'.join(L))
