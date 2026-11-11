"""Check every number of the GROVE site. Exits with code 1 if anything differs.

  python tools/check_numbers.py            (any Python 3.9+; standard library only)

1. Recomputes from the per-image files (src/data/final_scores.json, calibration_scores.json) the headline numbers and
   compares them with src/data/numbers.json and with the values the owner fixed for the page:
   GROVE final micro-F1 at the refit thresholds 0.7021 and false alarms per 100 violation-free images 22.8;
   gemma4:31b 0.6423 and 71.6. Also the main questions, first-freeze (post hoc), qwen3.5:27b fixed answers (post hoc),
   the signed-confidence baselines (post hoc) and the calibration 500.
2. If the run folder is present (C:\\GROVE_PC, or the GROVE_PC environment variable), re-reads every entry of
   numbers.json from its source file and key path, and checks thresholds.json and errors.json against their sources.
   Without the run folder this part is reported as skipped (the per-image check still runs).
3. Checks that every gallery image file named in gallery.json exists.
The same per-image check runs in JavaScript before every build (tools/check_data.mjs), so the build fails as well.
"""
import json, os, re, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); SITE = os.path.dirname(HERE); sys.path.insert(0, HERE)
from site_sources import md_table_cell, NUMRE, jget
D = os.path.join(SITE, 'src', 'data'); GROVE = os.environ.get('GROVE_PC', r'C:\GROVE_PC')
def load(n): return json.load(open(os.path.join(D, n), encoding='utf-8'))
NUM = load('numbers.json')['numbers']; TH = load('thresholds.json'); bad = []; ok = 0
def check(name, got, want, tol=1e-9):
    global ok
    if isinstance(want, (int, float)) and isinstance(got, (int, float)) and abs(got - want) <= tol: ok += 1; return
    if got == want: ok += 1; return
    bad.append('%s: got %r, expected %r' % (name, got, want))

# ---------------------------------------------------------------- 1. per-image recomputation
def metrics(rows, pred):
    """pred(row) -> (fall, ppe) decisions. Same definitions as grove_score.summary."""
    tp = fp = fn = 0; fa = 0; neg = 0
    for r in rows:
        y = (r['y_fall'], r['y_ppe']); p = pred(r); isneg = not any(y); neg += isneg
        for a, b in zip(p, y):
            tp += a and b; fp += a and not b; fn += (not a) and b; fa += isneg and a and not b
    return {'micro_f1': 2 * tp / max(2 * tp + fp + fn, 1e-9), 'false_alarms': 100 * fa / max(neg, 1), 'precision': tp / max(tp + fp, 1e-9), 'recall': tp / max(tp + fn, 1e-9)}
def ge(x, t): return x is not None and x >= t
RF, FFZ, MQ, SG = TH['refit']['GROVE'], TH['first_freeze']['GROVE'], TH['refit']['main_question'], TH['signed_confidence']
for setk, file in (('final', 'final_scores.json'), ('cal', 'calibration_scores.json')):
    rows = load(file)['rows']
    check('%s rows' % setk, len(rows), NUM['%s.n_images' % setk]['value'])
    systems = {'grove': lambda r: (ge(r['grove_fall'], RF['fall']), ge(r['grove_ppe'], RF['ppe'])),
               'main': lambda r: (ge(r['main_fall'], MQ['fall']), ge(r['main_ppe'], MQ['ppe'])),
               'gemma': lambda r: (bool(r['gemma_fall']), bool(r['gemma_ppe'])),
               'signed.gemma': lambda r: (ge(r['gemma_signed_fall'], SG['gemma']['fall']), ge(r['gemma_signed_ppe'], SG['gemma']['ppe'])),
               'signed.qwen': lambda r: (ge(r['qwen_signed_fall'], SG['qwen']['fall']), ge(r['qwen_signed_ppe'], SG['qwen']['ppe']))}
    if setk == 'final':
        systems['qwen'] = lambda r: (bool(r['qwen_fall']), bool(r['qwen_ppe']))
        systems['first_freeze_grove'] = lambda r: (ge(r['grove_fall'], FFZ['fall']), ge(r['grove_ppe'], FFZ['ppe']))
    for k, f in systems.items():
        m = metrics(rows, f)
        for q in ('micro_f1', 'false_alarms', 'precision', 'recall'):
            key = '%s.%s.%s' % (setk, k, q)
            if key in NUM: check('recomputed ' + key, m[q], NUM[key]['value'])
    if setk == 'final':
        g = metrics(rows, systems['grove']); b = metrics(rows, systems['gemma'])
        check('owner value: GROVE final micro-F1 (4 decimals)', round(g['micro_f1'], 4), 0.7021); check('owner value: GROVE final false alarms (1 decimal)', round(g['false_alarms'], 1), 22.8)
        check('owner value: gemma4:31b final micro-F1 (4 decimals)', round(b['micro_f1'], 4), 0.6423); check('owner value: gemma4:31b final false alarms (1 decimal)', round(b['false_alarms'], 1), 71.6)
check('owner value: refit thresholds', (RF['fall'], RF['ppe']), (0.86, 0.8)); check('owner value: first-freeze thresholds', (FFZ['fall'], FFZ['electrical'], FFZ['ppe']), (0.12, 0.32, 0.5))
print('recomputed from src/data/final_scores.json at the refit thresholds:')
print('  GROVE       micro-F1 %.4f (expected 0.7021)  false alarms per 100 violation-free images %.1f (expected 22.8)' % (g['micro_f1'], g['false_alarms']))
print('  gemma4:31b  micro-F1 %.4f (expected 0.6423)  false alarms per 100 violation-free images %.1f (expected 71.6)' % (b['micro_f1'], b['false_alarms']))
print('per-image recomputation: %d checks' % ok)

# ---------------------------------------------------------------- 2. sources
n_src = 0
if os.path.isdir(GROVE):
    cache = {}
    def src_json(rel):
        if rel not in cache: cache[rel] = json.load(open(os.path.join(GROVE, *rel.split('/')), encoding='utf-8'))
        return cache[rel]
    skipped = []
    for key, e in NUM.items():
        kp = e['key_path']; p = os.path.join(GROVE, *e['source'].split('/'))
        if not os.path.exists(p): skipped.append('%s (%s)' % (key, e['source'])); continue
        if kp and kp[0] == 'md_table':
            cell = md_table_cell(p, kp[1], kp[2], kp[3], kp[4]); xs = [float(x) for x in NUMRE.findall(cell)]
            check(key, xs[0], e['value']);
            if 'interval' in e: check(key + ' interval', xs[1:3], e['interval'])
        elif kp and kp[0] == 'regex':
            m = re.search(kp[1], open(p, encoding='utf-8').read()); check(key, m.group(1) if m else None, e['value'])
        else:
            v = jget(src_json(e['source']), kp)
            if e.get('count_of'): v = len(v)
            if 'interval' in e and 'interval_key_path' not in e: check(key, [v[0], v[1], v[2]], [e['value']] + e['interval'])
            else:
                check(key, v, e['value'])
                if 'interval_key_path' in e: c = jget(src_json(e['source']), e['interval_key_path']); check(key + ' interval', [c[1], c[2]], e['interval'])
        n_src += 1
    if skipped: print('source files not present here, entries skipped: ' + ', '.join(skipped))
    F1, FT, F2 = src_json('freeze/freeze_1.json'), src_json('freeze/final_thresholds.json'), src_json('freeze/freeze_2.json')
    MAP = {'fall': 'Fall_Hazard', 'ppe': 'PPE_Violation', 'electrical': 'Electrocution_Hazard'}
    for s in ('GROVE', 'main_question'):
        for c, v in TH['first_freeze'][s].items(): check('thresholds first_freeze %s %s' % (s, c), v, F1['thresholds_fit_on_all_203'][s][MAP[c]])
        for c, v in TH['refit'][s].items(): check('thresholds refit %s %s' % (s, c), v, FT['thresholds'][s]['refit'][MAP[c]])
    check('thresholds electrical', TH['electrical']['GROVE'], F2['thresholds_fit_on_all_203']['GROVE']['Electrocution_Hazard'])
    CSJ = src_json('results_posthoc/confidence_signed.json')
    for m, mk in (('gemma', 'gemma4:31b'), ('qwen', 'qwen3.5:27b')):
        for c, v in TH['signed_confidence'][m].items(): check('thresholds signed %s %s' % (m, c), v, CSJ['thresholds_signed'][mk][MAP[c]])
    EJ = src_json('results_posthoc/errors_final.json'); ER = load('errors.json')
    for s, rows in ER['systems'].items():
        for r in rows: check('errors %s %s|%s' % (s, r['type'], r['class']), r['all'], EJ['systems'][s]['all']['%s|%s' % (r['type'], r['class'])])
    print('source comparison: %d entries of numbers.json re-read from %s' % (n_src, GROVE))
else:
    print('source comparison skipped: run folder %s not found on this computer (per-image checks above still ran)' % GROVE)

# ---------------------------------------------------------------- 3. gallery files
G = load('gallery.json')
for im in G['images']:
    for f in im['files'].values():
        if not os.path.isfile(os.path.join(SITE, 'public', *f.split('/'))): bad.append('missing image file %s' % f)
print('gallery: %d images, %d files checked' % (len(G['images']), sum(len(i['files']) for i in G['images'])))
if bad:
    print('FAILED: %d differences' % len(bad)); [print('  ' + b) for b in bad]; sys.exit(1)
print('ALL CHECKS PASSED: %d comparisons, 0 differences' % ok)
