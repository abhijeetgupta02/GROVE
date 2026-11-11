"""Acceptance test for the scoring code (Section 14 Part 7). Mac reference files are used only here, never in a report."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grove_common import *
import grove_data as gd, grove_score as gs
R = []
def check(name, ok, detail): R.append({'test': name, 'pass': bool(ok), 'detail': detail}); print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail, flush=True)
d = gd.g203(); names = d['names']; Y = d['Y'](CATS3)
pos = Y.sum(0); kept = {c: sum(len(d['boxes'].get((n, c), [])) for n in names) for c in CATS3}; other = int((~Y.any(1)).sum())
check('1 labels', list(pos) == [61, 24, 40] and pos.sum() == 125 and [kept[c] for c in CATS3] == [63, 24, 45] and other == 111,
      'positive pairs %s total %d; kept boxes %s total %d of %d; other images %d' % (dict(zip(CATS3, pos.tolist())), pos.sum(), kept, sum(kept.values()), sum(d['raw_box_counts'].values()), other))
def rows(f):
    out = {}
    for l in open(os.path.join(PK, 'reference_mac', f), encoding='utf-8'):
        x = json.loads(l); out[gd.ht.normalize_image_name(x['image_name'])] = x['probs']
    return out
h = rows('clef_27b__h.jsonl'); s0 = rows('clef-flash_9b__S0.jsonl'); assert set(h) == set(names) == set(s0)
q = {k: np.array([h[n][k] for n in names]) for k in h[names[0]]}
S = np.stack([f_fall(q), np.array([s0[n]['Electrocution_Hazard'] for n in names]), f_ppe(q)], 1)
v = gs.f1(gs.fixed(gs.ge(S, 0.5), Y).sum((0, 1))); check('2 fixed 0.5', round(v, 4) == 0.6783, 'micro-F1 %.6f (target 0.6783)' % v)
v = gs.f1(gs.blocks_cv(S, Y, d['nums'], gd.BLOCKS).sum((0, 1))); check('3 file blocks', abs(v - 0.7726) <= 0.005, 'micro-F1 %.4f (target 0.7726 within 0.005)' % v)
PI, per = gs.cv(S, Y, d['groups']); v = gs.f1(PI.sum((0, 1))); check('4 grouped folds', 0.78 <= v <= 0.80, 'micro-F1 %.4f (target 0.78 to 0.80), repeats %.3f to %.3f' % (v, min(per), max(per)))
m1 = gs.match_iou([[0.6, 0.45], [0.45, 0]], 0.5); m2 = gs.match_iou([[0.9, 0.6], [0.6, 0]], 0.5)
check('5 box matching', [(i, j) for i, j, _ in m1] == [(0, 0)] and sorted((i, j) for i, j, _ in m2) == [(0, 1), (1, 0)], 'matrix 1 -> %s; matrix 2 -> %s' % ([(i, j) for i, j, _ in m1], [(i, j) for i, j, _ in m2]))
rng = np.random.RandomState(1); Yt = rng.rand(300, 2) < 0.3; Pt = rng.rand(300, 2) < 0.4; PIt = gs.per_image(Pt, Yt); viol = Yt.any(1)
ps = gs.prevalence_std(PIt, viol, viol.mean())['precision']; up = gs.prec(PIt.sum((0, 1)))
check('6 prevalence-standardized precision', abs(ps - up) < 1e-12, 'r = p: %.10f vs unweighted %.10f' % (ps, up))
ok = all(x['pass'] for x in R); out = MODE.path('results', 'acceptance_test.json'); write_json(out, {'all_pass': ok, 'tests': R, 'at': now()})
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
