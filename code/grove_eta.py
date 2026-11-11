"""Finish estimate for the main run (restart of 2026-11-05). Standard library only; read-only.
Remaining passes per job times the pilot speed of that model and question set, plus the pause before every decision-model
and phrase call (0 since 2026-11-06, D22), plus about 30 s per model load. Once experiment 14 has chosen the models, experiments 23, 40 to 42 and 50 to 51
use the chosen models; experiments 43 and 52 use the top two single-pass models of experiment 9 (and the chosen baseline for 52)."""
import datetime, json, os
GENERATORS = ['qwen3.5:9b', 'qwen3.5:27b', 'gemma4:31b', 'mistral-small3.2:24b', 'ministral-3:14b', 'qwen3-vl:32b']
DECISION = ['clef:27b', 'clef-flash:9b', 'pplx-decider:27b', 'd3:9b', 'd3:27b']
PAUSE = {'decision': 0.0, 'phrase': 0.0, 'sp': 0.0}  # 7 s pause removed 2026-11-06 (D22)
_cache = {}
def _rj(p, d=None):
    try:
        with open(p, encoding='utf-8') as f: return json.load(f)
    except Exception: return d
def safe(m): return m.replace(':', '_').replace('/', '_')
def done_count(G, exp, model, setname):
    p = os.path.join(G, 'runs', exp, '%s__%s.jsonl' % (safe(model), setname))
    try: st = os.stat(p)
    except OSError: return 0
    c = _cache.get(p)
    if c and c[0] == (st.st_size, st.st_mtime_ns): return c[1]
    h = (_rj(p[:-6] + '.config.json', {}) or {}).get('config_hash'); keys = set()
    with open(p, 'rb') as f:
        for l in f:
            if not l.endswith(b'\n'): continue
            try: r = json.loads(l)
            except Exception: continue
            if r.get('terminal') and (not h or r.get('config_hash') == h): keys.add(r.get('key'))
    _cache[p] = ((st.st_size, st.st_mtime_ns), len(keys)); return len(keys)
def top2_single_pass(G):
    e15 = _rj(os.path.join(G, 'results', 'e15_screening.json'))
    if not isinstance(e15, dict): return None
    c = [(v.get('micro_f1') or 0, v.get('completion') or 0, k[len('single-pass '):]) for k, v in e15.items() if k.startswith('single-pass ') and isinstance(v, dict)]
    return [m for _, _, m in sorted(c, key=lambda x: (-x[0], -x[1]))][:2] or None
def estimate(G, live=None, now=None):
    pe = _rj(os.path.join(G, 'results', 'e08_pilot_estimate.json'), {}) or {}
    sp = pe.get('speeds') or {}; ph = pe.get('phrase_seconds') or 1.0; gd = pe.get('gdino_seconds') or 1.0; fr = pe.get('flag_rate') or 1.0
    pilot_sel = pe.get('pilot_selection') or {}
    sel = _rj(os.path.join(G, 'freeze', 'selection.json'))
    chosen = isinstance(sel, dict) and sel.get('main_model')
    S = sel if chosen else pilot_sel
    M, M2, E = S.get('main_model'), S.get('runner_up_main_model'), (S.get('electrical_source') or {})
    top2 = top2_single_pass(G) or pe.get('pilot_top2') or GENERATORS[:2]
    bb = ((_rj(os.path.join(G, 'freeze', 'best_baseline.json'), {}) or {}).get('best') or {}).get('model') or top2[0]
    def speed(e, m, s):
        if live and live[0] == e and live[1] == m and live[2]: return live[2]  # live speed of the running job
        cs = e in ('e40', 'e41', 'e42', 'e43', 'e50', 'e51', 'e52')
        v = (sp.get('%s|%s|cs' % (m, s)) if cs else None) or sp.get('%s|%s' % (m, s))
        return v if v else 15.0
    jobs = [('e09', m, 'sp', 203, 'sp') for m in GENERATORS] + [('e10', m, 'sp', 20, 'sp') for m in GENERATORS[:3]]
    jobs += [(e, m, s, 203, 'decision') for e, s in (('e11', 'm'), ('e12', 'h'), ('e13', 'S0')) for m in DECISION]
    for rep in ('e23_rep1', 'e23_rep2'):
        if M: jobs.append((rep, M, 'h', 203, 'decision'))
        if E.get('option') and E['option'] != 'formula': jobs.append((rep, E['model'], E['option'], 203, 'decision'))
    jobs += [('e40', M, 'h', 500, 'decision'), ('e41', M, 'm', 500, 'decision')] + ([('e42', M2, 'h', 500, 'decision')] if M2 else [])
    jobs += [('e43', m, 'sp', 500, 'sp') for m in top2] + [('e50', M, 'h', 1000, 'decision'), ('e51', M, 'm', 1000, 'decision'), ('e52', bb, 'sp', 1000, 'sp')]
    rem = 0.0; rows = []; loads = 0
    for e, m, s, n, kind in jobs:
        if not m: continue
        d = done_count(G, e, m, s); left = max(0, n - d)
        if left: loads += 1
        sec = left * (speed(e, m, s) + PAUSE[kind]); rem += sec; rows.append((e, m, s, left, round(sec / 3600, 2)))
    for marker, n in (('e31_38', int(203 * fr)), ('e45', int(500 * fr * 0.7)), ('e53', int(1000 * fr * 0.7))):
        if not os.path.exists(os.path.join(G, 'results', '%s.done.json' % marker)):
            sec = n * (gd + ph + PAUSE['phrase']); rem += sec; rows.append(('grounding ' + marker, None, None, n, round(sec / 3600, 2))); loads += 2
    rem += loads * 30
    t = now or datetime.datetime.now()
    return dict(remaining_h=rem / 3600, finish=(t + datetime.timedelta(seconds=rem)).isoformat(timespec='minutes'), rows=rows, chosen_models=bool(chosen),
                basis='pilot speeds per model and question set%s%s; %s' % (
                    (' plus the %d s pause per decision-model and phrase call' % PAUSE['decision']) if PAUSE['decision'] else ', no pause', '' if not live else ', live speed for the running job',
                    'models chosen by experiment 14' if chosen else 'pilot-chosen models until experiment 14 runs'))
