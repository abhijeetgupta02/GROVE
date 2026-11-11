"""Export the data of the GROVE project site from the run's saved files. Read only; no model call.

Usage (on the run computer, from the project folder):
    C:\\GROVE_PC\\venv\\Scripts\\python.exe -B tools\\export_site_data.py
The run folder is C:\\GROVE_PC, or the folder named in the GROVE_PC environment variable. It is read through the run's
own loaders (code\\posthoc_partb.py, code\\grove_stages.py, code\\grove_data.py), as code\\posthoc_partb.py and
code\\posthoc_signed.py do. This script writes only inside this project: src/data/*.json and public/gallery/*.
Every number on the page comes from src/data; tools/check_numbers.py compares each entry with its source.
"""
import collections, io, json, math, os, random, re, sys
sys.dont_write_bytecode = True
GROVE = os.environ.get('GROVE_PC', r'C:\GROVE_PC')
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(GROVE, 'code'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import posthoc_partb as pb
from posthoc_partb import off, gs, gd, st, gcl, read_json, CATS2, SEED, base, ph_load
from grove_common import f_fall, f_ppe, f_elec, SETS, FORMULA_TEXT
from site_sources import md_table_cell, NUMRE, jget

DATA = os.path.join(SITE, 'src', 'data'); GAL = os.path.join(SITE, 'public', 'gallery')
os.makedirs(DATA, exist_ok=True); os.makedirs(GAL, exist_ok=True)
def P(*a): return os.path.join(GROVE, *a)
CAT = {'Fall_Hazard': 'fall', 'PPE_Violation': 'ppe', 'Electrocution_Hazard': 'electrical'}
_J = {}
def J(rel):
    if rel not in _J: _J[rel] = read_json(P(*rel.split('/')))
    return _J[rel]

def r4(x):
    """Round to 4 decimals without crossing any multiple of 0.01: a score just below a grid point stays below it,
    so every threshold the page can set (steps of 0.01) gives the same decision as the unrounded score."""
    if x is None: return None
    x = float(x)
    if math.isnan(x): return None
    y = round(x, 4); g = round(y * 100) / 100
    if abs(y - g) < 1e-12 and x < g: y = round(g - 0.0001, 4)
    return y

# ------------------------------------------------------------------ numbers.json helpers
NUM = {}
def add(key, src, path, unit, post_hoc=False, triple=False, note=None):
    v = jget(J(src), path); e = {'unit': unit, 'source': src, 'key_path': path, 'post_hoc': post_hoc}
    if triple: e['value'], e['interval'] = v[0], [v[1], v[2]]
    else: e['value'] = v
    if note: e['note'] = note
    NUM[key] = e
def add_ci(key, src, path, ci_path, unit, post_hoc=False):
    add(key, src, path, unit, post_hoc); c = jget(J(src), ci_path)
    NUM[key]['interval'] = [c[1], c[2]]; NUM[key]['interval_key_path'] = ci_path
MD = 'reports/PAPER_TABLES_v2.md'
def add_md(key, heading, row_key, col, unit, post_hoc=False, note=None, nth=0):
    cell = md_table_cell(P('reports', 'PAPER_TABLES_v2.md'), heading, row_key, col, nth)
    xs = [float(x) for x in NUMRE.findall(cell)]
    e = {'value': xs[0], 'unit': unit, 'source': MD, 'key_path': ['md_table', heading, row_key, col, nth], 'cell': cell, 'post_hoc': post_hoc}
    if len(xs) >= 3 and '[' in cell: e['interval'] = [xs[1], xs[2]]
    if note: e['note'] = note
    NUM[key] = e
def add_text(key, src, pattern, unit, note=None):
    t = open(P(*src.split('/')), encoding='utf-8').read(); m = re.search(pattern, t)
    NUM[key] = {'value': m.group(1), 'unit': unit, 'source': src, 'key_path': ['regex', pattern], 'post_hoc': False}
    if note: NUM[key]['note'] = note

# ------------------------------------------------------------------ numbers shown on the page
E54, E48, E15, E16, E55 = 'results/e54_final.json', 'results/e48.json', 'results/e15_screening.json', 'results/e16_21.json', 'results/e55_removal_final.json'
SB, FF, CS, CB, EF = 'results_posthoc/second_baseline.json', 'results_posthoc/first_freeze_scores.json', 'results_posthoc/confidence_signed.json', 'results_posthoc/confidence_baseline.json', 'results_posthoc/errors_final.json'
def summary_block(prefix, src, base_path, post_hoc=False, ci_path=None, cats=CATS2, std=True):
    add(prefix + '.micro_f1', src, base_path + ['micro_f1'], 'micro-F1', post_hoc)
    if ci_path: c = jget(J(src), ci_path); NUM[prefix + '.micro_f1']['interval'] = [c[1], c[2]]; NUM[prefix + '.micro_f1']['interval_key_path'] = ci_path
    add(prefix + '.precision', src, base_path + ['precision'], 'precision', post_hoc)
    add(prefix + '.recall', src, base_path + ['recall'], 'recall', post_hoc)
    add(prefix + '.false_alarms', src, base_path + ['false_alarms_per_100_negative'], 'false alarms per 100 violation-free images', post_hoc)
    add(prefix + '.completion', src, base_path + ['completion'], 'share of images with a valid response', post_hoc)
    for c in cats:
        for m in ('f1', 'precision', 'recall'): add('%s.%s.%s' % (prefix, CAT[c], m), src, base_path + ['per_category', c, m], m, post_hoc)
    if std and 'prevalence_standardized' in jget(J(src), base_path):
        add(prefix + '.std_precision', src, base_path + ['prevalence_standardized', 'precision'], 'prevalence-standardized precision', post_hoc)
        add(prefix + '.std_f1', src, base_path + ['prevalence_standardized', 'f1'], 'prevalence-standardized F1', post_hoc)
# final 1,000
add('final.n_images', E54, ['n_images'], 'images'); add('final.n_violation', E54, ['n_violation'], 'images with a violation')
add('final.n_negative', E54, ['GROVE', 'n_negative_images'], 'violation-free images'); add('final.reference_rate', E54, ['reference_rate_r'], 'natural violation rate')
summary_block('final.grove', E54, ['GROVE'], ci_path=['GROVE', 'f1_ci'])
summary_block('final.main', E54, ['main_question'], ci_path=['main_question', 'f1_ci'])
summary_block('final.gemma', E54, ['best single-pass'], ci_path=['best single-pass', 'f1_ci'])
summary_block('final.qwen', SB, ['qwen3.5:27b'], post_hoc=True, ci_path=['qwen3.5:27b_f1_ci'])
add('final.diff.grove_minus_gemma', E54, ['criteria', 'primary', 'difference'], 'micro-F1 difference', triple=True)
add('final.diff.grove_minus_gemma_false_alarms', E54, ['criteria', 'secondary_false_alarms', 'difference_GROVE_minus_baseline'], 'false alarms per 100 violation-free images, difference', triple=True)
add('final.diff.grove_minus_main', E54, ['criteria', 'secondary_main_question', 'difference'], 'micro-F1 difference', triple=True)
for c in CATS2: add('final.diff.grove_minus_gemma.%s' % CAT[c], E54, ['criteria', 'per_category', c], 'F1 difference', triple=True)
add('final.diff.grove_minus_qwen', SB, ['GROVE_minus_qwen'], 'micro-F1 difference', post_hoc=True, triple=True)
add('final.diff.grove_minus_qwen_false_alarms', SB, ['GROVE_minus_qwen_false_alarms'], 'false alarms per 100 violation-free images, difference', post_hoc=True, triple=True)
for m, k in (('first_freeze_grove', 'GROVE'), ('first_freeze_main', 'main_question')):
    add_ci('final.%s.micro_f1' % m, FF, ['final', 'summary', k, 'micro_f1'], ['final', 'summary', k, 'f1_ci'], 'micro-F1', post_hoc=True)
    add('final.%s.false_alarms' % m, FF, ['final', 'summary', k, 'false_alarms_per_100_negative'], 'false alarms per 100 violation-free images', post_hoc=True)
    add('final.%s.precision' % m, FF, ['final', 'summary', k, 'precision'], 'precision', post_hoc=True)
    add('final.%s.recall' % m, FF, ['final', 'summary', k, 'recall'], 'recall', post_hoc=True)
# boxes on the final set
for cut in ('0.5', '0.3'):
    for m, k in (('grove', 'GROVE'), ('gemma', 'best single-pass')):
        for q in ('f1', 'precision', 'recall'): add('final.box.%s.%s.%s' % (m, cut, q), E54, ['criteria', 'secondary_top_box', k, 'iou_' + cut, q], 'top-box ' + q)
    add('final.box.grove_up_to_5.%s.f1' % cut, E54, ['criteria', 'GROVE_up_to_5_boxes', 'iou_' + cut, 'f1'], 'box F1, up to 5 boxes per category')
    add('final.box.qwen_as_written.%s.f1' % cut, SB, ['boxes', cut, 'as_written'], 'top-box F1', post_hoc=True)
    add('final.box.qwen_grid.%s.f1' % cut, SB, ['boxes', cut, 'grid'], 'top-box F1, 0-1000 grid reading', post_hoc=True)
    add('final.box.grove_minus_qwen_grid.%s' % cut, SB, ['boxes', cut, 'GROVE_minus_upper_bound'], 'top-box F1 difference', post_hoc=True, triple=True)
add_md('final.box.gemma_grid.0.5', '#### Final 1,000 (Fall, PPE)', ['single-pass gemma4:31b'], 'at 0.5, rescaled', 'top-box F1, 0-1000 grid reading (sensitivity; not trusted)')
add('final.box.qwen_counts.boxes', SB, ['box_counts', 'boxes'], 'boxes', post_hoc=True); add('final.box.qwen_counts.grid_only', SB, ['box_counts', 'grid_only'], 'boxes', post_hoc=True)
# removal tests on the final set
for v in ('variant_no_fact_questions', 'variant_no_protection', 'variant_no_worker'):
    add('final.removal.%s.micro_f1' % v, E55, [v, 'summary', 'micro_f1'], 'micro-F1'); add('final.removal.%s.diff' % v, E55, [v, 'difference_from_GROVE'], 'micro-F1 difference', triple=True)
# signed-confidence baselines (post hoc) and the original confidence/100 rows (post hoc)
for k, setk in (('final', 'final'), ('cal', 'calibration')):
    for m, mk in (('gemma', 'gemma4:31b'), ('qwen', 'qwen3.5:27b')):
        add_ci('%s.signed.%s.micro_f1' % (k, m), CS, ['sets', setk, 'models', mk, 'signed_fitted', 'micro_f1'], ['sets', setk, 'models', mk, 'signed_ci'], 'micro-F1', post_hoc=True)
        for q in ('precision', 'recall', 'false_alarms_per_100_negative'):
            add('%s.signed.%s.%s' % (k, m, 'false_alarms' if q.startswith('false') else q), CS, ['sets', setk, 'models', mk, 'signed_fitted', q], q.replace('_', ' '), post_hoc=True)
        add('%s.signed.%s.diff' % (k, m), CS, ['sets', setk, 'models', mk, 'GROVE_minus_signed'], 'micro-F1 difference, GROVE minus', post_hoc=True, triple=True)
        add('%s.confidence100.%s.micro_f1' % (k, m), CB, ['sets', setk, 'confidence', mk, 'fitted', 'micro_f1'], 'micro-F1', post_hoc=True)
        for c in CATS2:
            add('%s.ap.%s_signed.%s' % (k, m, CAT[c]), CS, ['sets', setk, 'average_precision', c, '%s signed' % mk, 'AP'], 'average precision', post_hoc=True)
    for c in CATS2:
        for lab, nm in (('grove', 'GROVE'), ('main', 'main questions')): add('%s.ap.%s.%s' % (k, lab, CAT[c]), CS, ['sets', setk, 'average_precision', c, nm, 'AP'], 'average precision', post_hoc=True)

# calibration 500 (thresholds fit here: not an independent test)
add('cal.n_images', E48, ['results', 'refit', 'GROVE', 'n_images'], 'images'); add('cal.n_negative', E48, ['results', 'refit', 'GROVE', 'n_negative_images'], 'violation-free images')
for k, nm in (('grove', 'GROVE'), ('main', 'main_question'), ('gemma', 'single-pass gemma4:31b'), ('qwen', 'single-pass qwen3.5:27b')):
    summary_block('cal.%s' % k, E48, ['results', 'refit', nm])
for k, nm in (('first_freeze_grove', 'GROVE'), ('first_freeze_main', 'main_question')):
    for q in ('micro_f1', 'precision', 'recall', 'false_alarms_per_100_negative'):
        add('cal.%s.%s' % (k, 'false_alarms' if q.startswith('false') else q), E48, ['results', 'first_freeze', nm, q], q.replace('_', ' '))
add('cal.diff.grove_minus_gemma', E48, ['results', 'refit', 'GROVE minus best single-pass', 'f1'], 'micro-F1 difference (in-sample thresholds)', triple=True)
add('cal.diff.grove_minus_gemma_false_alarms', E48, ['results', 'refit', 'GROVE minus best single-pass', 'fa'], 'false alarms per 100 violation-free images, difference', triple=True)
# per-category F1 with intervals (Table 4) at full precision from results\e57_59.json; PAPER_TABLES_v2.md rounds them to
# 4 decimals, and rounding those again to 3 can move the last digit (0.3945 shows as 0.395, but the full value 0.39449... is 0.394)
E5759 = 'results/e57_59.json'
for setk, head in (('cal', 'Calibration (500 images, not independent)'), ('final', 'Final test (1000 images)')):
    for k, nm in (('grove', 'GROVE'), ('main', 'main_question'), ('gemma', 'single-pass gemma4:31b')):
        for c, cn in (('fall', 'Fall_Hazard'), ('ppe', 'PPE_Violation')):
            add('%s.table4.%s.%s.f1' % (setk, k, c), E5759, ['%s|%s|%s' % (head, nm, cn)], 'F1', triple=True)
            for q in ('precision', 'recall'): NUM['%s.table4.%s.%s.%s' % (setk, k, c, q)] = dict(NUM['%s.%s.%s.%s' % (setk, k, c, q)])
# 203 development images (held-out thresholds for GROVE and the main questions; single-pass fixed answers)
add('dev.n_images', E15, ['GROVE', 'n_images'], 'images'); add('dev.n_negative', E15, ['GROVE', 'n_negative_images'], 'violation-free images')
for k, nm in (('grove', 'GROVE'), ('main', 'Main questions only (m) d3:27b'), ('gemma', 'single-pass gemma4:31b'), ('qwen', 'single-pass qwen3.5:27b')):
    summary_block('dev.%s' % k, E15, [nm], cats=['Fall_Hazard', 'Electrocution_Hazard', 'PPE_Violation'], std=False)
SHORTM = {'gemma4:31b': 'gemma', 'qwen3.5:27b': 'qwen'}
for m in ('gemma4:31b', 'qwen3.5:27b'): add('dev.diff.grove_minus_%s' % SHORTM[m], E15, ['GROVE minus single-pass %s' % m], 'micro-F1 difference', triple=True)
for k in ('16 Main questions only (m set of d3:27b)', '17 No protection term', '18 No worker-visible term', '20 One threshold for all categories', '21 Fixed 0.5'):
    kk = k.split(' ')[0]; add('dev.removal.%s.micro_f1' % kk, E16, [k, 'micro_f1'], 'micro-F1'); add('dev.removal.%s.diff' % kk, E16, ['differences', k], 'micro-F1 difference', triple=True)
add('dev.removal.grove.micro_f1', E16, ['GROVE (as selected)', 'micro_f1'], 'micro-F1')
# grounding on the 203 and the calibration 500 (PAPER_TABLES_v2.md, section 8)
add_md('dev.box.grove.0.5', '### 203 images (copied from `reports\\grounding.md`, numbers in `results\\e31_38.json`)', ['36 both, as designed, top box'], 'Box F1 at 0.5', 'top-box F1')
for m in ('qwen3.5:27b', 'gemma4:31b'):
    for col, nm in (('Top-box F1 at 0.5, as written', 'as_written'), ('at 0.5, rescaled', 'grid')):
        add_md('dev.box.%s.%s.0.5' % (SHORTM[m], nm), '#### 203 development images (Fall, Electrical, PPE)', ['single-pass ' + m], col, 'top-box F1' + (', 0-1000 grid reading (sensitivity)' if nm == 'grid' else ''))
        add_md('cal.box.%s.%s.0.5' % (SHORTM[m], nm), '#### Calibration 500 (Fall, PPE)', ['single-pass ' + m], col, 'top-box F1' + (', 0-1000 grid reading (sensitivity; not trusted)' if nm == 'grid' else ''))
add_md('cal.box.grove.0.5', '### Calibration 500 (copied from `reports\\calibration.md`, numbers in `results\\e45.json`)', ['GROVE top box'], 'Box F1 at 0.5', 'top-box F1')
# speed and setup
add_md('speed.decision_seconds', '## Batch runs (seconds per image, valid responses)', ['e50', 'd3_27b__h.jsonl'], 'Mean seconds per image', 'seconds per image (decision step, d3:27b, final set)')
add_md('speed.single_pass_seconds', '## Batch runs (seconds per image, valid responses)', ['e52', 'gemma4_31b__sp.jsonl'], 'Mean seconds per image', 'seconds per image (single-pass gemma4:31b, final set)')
add('setup.ollama_version', 'freeze/freeze_2.json', ['ollama', 'version'], 'version')
add('setup.question_count_h', 'runs/e50/d3_27b__h.config.json', ['config', 'questions'], 'questions'); NUM['setup.question_count_h']['value'] = len(NUM['setup.question_count_h']['value']); NUM['setup.question_count_h']['count_of'] = True
for m in J('freeze/freeze_2.json')['models']: add('setup.digest.%s' % m, 'freeze/freeze_2.json', ['models', m, 'digest'], 'sha256 digest')
add_text('setup.gpu', 'logs/pc_setup_report.md', r'\((?:[^,()]*), (RTX A6000 \d+ GB)\)', 'graphics card')
add_text('setup.freeze_2_sha256', 'freeze/freeze_2.sha256', r'^([0-9a-f]{64})', 'SHA-256 of freeze_2.json')
add_text('dataset.height_rule_m', 'packet/data/constructionsite10k/upstream_README.md', r'\| 2 \| Use of safety harness when working \u2265(\d+)m high', 'metres (ConstructionSite10k rules 2 and 3)')
add_text('dataset.total_images', 'packet/data/constructionsite10k/upstream_README.md', r'\*\*Total images:\*\* ([\d,]+)', 'images in ConstructionSite10k')
add('lists.final.visibility_cutoff', 'lists/final.json', ['visibility_cutoff_largest_box_share'], 'largest-box share')
# errors (post hoc, experiment 60 repeated on the final set)
for s, k in (('GROVE', 'grove'), ('gemma4:31b', 'gemma')):
    for t in ('miss', 'false alarm'): add('errors.%s.%s' % (k, t.replace(' ', '_')), EF, ['systems', s, 'totals', t], 'errors', post_hoc=True)
add('errors.overlap', EF, ['overlap'], 'image-category errors made by both', post_hoc=True)
# method parameters quoted in the text
add_text('method.cv_repeats', 'freeze/freeze_2.json', r'held-out micro-F1 \((\d+) repeats of \d+ grouped folds', 'repeats')
add_text('method.cv_folds', 'freeze/freeze_2.json', r'held-out micro-F1 \(\d+ repeats of (\d+) grouped folds', 'grouped folds')
add('method.bootstrap_draws', 'results_posthoc/box_upper_bound.json', ['draws'], 'bootstrap draws')
add('method.seed', 'results_posthoc/box_upper_bound.json', ['seed'], 'random seed')
add('method.threshold_fit', 'freeze/final_thresholds.json', ['method'], 'threshold fitting method')

# ------------------------------------------------------------------ thresholds.json
F1J, FTJ, F2J = J('freeze/freeze_1.json'), J('freeze/final_thresholds.json'), J('freeze/freeze_2.json')
TH_REFIT = {c: FTJ['thresholds']['GROVE']['refit'][c] for c in CATS2}; TH_FIRST = {c: F1J['thresholds_fit_on_all_203']['GROVE'][c] for c in CATS2}
TH_MQ = {c: FTJ['thresholds']['main_question']['refit'][c] for c in CATS2}
TH_SIGN = {m: J(CS)['thresholds_signed'][m] for m in ('gemma4:31b', 'qwen3.5:27b')}
def tdict(d): return {CAT[c]: v for c, v in d.items()}
THRESH = {
    'first_freeze': {'GROVE': tdict(F1J['thresholds_fit_on_all_203']['GROVE']), 'main_question': tdict(F1J['thresholds_fit_on_all_203']['main_question']),
                     'source': 'freeze/freeze_1.json', 'key_path': ['thresholds_fit_on_all_203'], 'fit_on': 'all 203 development images'},
    'refit': {'GROVE': tdict(TH_REFIT), 'main_question': tdict(TH_MQ), 'source': 'freeze/final_thresholds.json', 'key_path': ['thresholds', '<system>', 'refit'],
              'fit_on': 'calibration 500, refit once (Fall and protective equipment); used unchanged on the final 1,000'},
    'electrical': {'GROVE': F2J['thresholds_fit_on_all_203']['GROVE']['Electrocution_Hazard'], 'source': 'freeze/freeze_2.json', 'key_path': ['thresholds_fit_on_all_203', 'GROVE', 'Electrocution_Hazard'],
                   'note': 'Electrical is labeled only on the development images; its threshold was not refit.'},
    'signed_confidence': {SHORTM[m]: tdict(v) for m, v in TH_SIGN.items()} | {'source': CS, 'key_path': ['thresholds_signed'], 'post_hoc': True,
                          'fit_on': 'calibration 500 (grid and method of experiment 44); score redefined after the first scoring'},
    'method': FTJ['method'],
}
assert TH_REFIT == {'Fall_Hazard': 0.86, 'PPE_Violation': 0.8} and TH_FIRST == {'Fall_Hazard': 0.12, 'PPE_Violation': 0.5} and THRESH['electrical']['GROVE'] == 0.32

# ------------------------------------------------------------------ per-image scores (final 1,000 and calibration 500)
f2, M, Bm, TH, B = base(); assert M == 'd3:27b' and Bm == 'gemma4:31b'
META = gd.meta()
def size_band(i, viol):
    if not viol: return 'no violation'
    s = gd.largest_scored_share(i)
    return 'below 1%' if s < 0.01 else ('1% to 10%' if s < 0.10 else '10% or more')
def signed(exp, model, ids):
    S, Pr, v, stt, h = pb.conf_scores(exp, model, ids); return np.where(Pr, S, 1.0 - S), v
def qwen_fixed_final(ids):
    term, h = ph_load('p06_final', 'qwen3.5:27b', 'sp'); out = np.zeros((len(ids), 2), bool); v = np.zeros(len(ids), bool)
    for i, n in enumerate(ids):
        x = term.get(n)
        if x and x['status'] == 'valid':
            v[i] = True
            for j, c in enumerate(CATS2): out[i, j] = bool(x['output']['parsed'][c]['present'])
    return out, v
ROWS = {}
for setk, exp in (('final', 'p07_final'), ('calibration', 'p07_cal')):
    S_ = B[setk]; ids, Y = S_['ids'], S_['Y']; gsg, gv = signed(exp, 'gemma4:31b', ids); qsg, qv = signed(exp, 'qwen3.5:27b', ids)
    assert S_['vG'].all() and S_['vM'].all() and S_['vsp'].all() and gv.all() and qv.all()
    if setk == 'final': qf, qfv = qwen_fixed_final(ids); assert qfv.all()
    rows = []
    for i, n in enumerate(ids):
        m = META[n]; viol = bool(Y[i].any())
        r = {'id': n, 'y_fall': int(Y[i, 0]), 'y_ppe': int(Y[i, 1]), 'grove_fall': r4(S_['SG'][i, 0]), 'grove_ppe': r4(S_['SG'][i, 1]),
             'main_fall': r4(S_['SM'][i, 0]), 'main_ppe': r4(S_['SM'][i, 1]), 'gemma_fall': int(S_['Psp'][i, 0]), 'gemma_ppe': int(S_['Psp'][i, 1]),
             'gemma_signed_fall': r4(gsg[i, 0]), 'gemma_signed_ppe': r4(gsg[i, 1]), 'qwen_signed_fall': r4(qsg[i, 0]), 'qwen_signed_ppe': r4(qsg[i, 1])}
        if setk == 'final': r['qwen_fall'], r['qwen_ppe'] = int(qf[i, 0]), int(qf[i, 1])
        r |= {'illumination': m.get('illumination'), 'camera_distance': m.get('camera_distance'), 'size_band': size_band(n, viol)}
        rows.append(r)
    # rounding must not change any decision at the thresholds used on the page
    for key, th in (('grove', TH_REFIT), ('grove', TH_FIRST), ('main', TH_MQ)):
        for j, c in enumerate(CATS2):
            raw = (S_['SG'] if key == 'grove' else S_['SM'])[:, j] >= th[c]; rnd = np.array([x['%s_%s' % (key, CAT[c])] >= th[c] for x in rows])
            assert (raw == rnd).all(), (setk, key, c)
    ROWS[setk] = rows
FIELDS = {'id': 'ConstructionSite10k image id', 'y_fall': 'label, Fall (1 = violation)', 'y_ppe': 'label, protective equipment (1 = violation)',
          'grove_fall': 'GROVE score, Fall (d3:27b, question set h, frozen formula)', 'grove_ppe': 'GROVE score, protective equipment',
          'main_fall': 'main-question score, Fall (d3:27b, set m)', 'main_ppe': 'main-question score, protective equipment',
          'gemma_fall': 'gemma4:31b single-pass fixed answer, Fall (1 = present)', 'gemma_ppe': 'gemma4:31b single-pass fixed answer, protective equipment',
          'gemma_signed_fall': 'gemma4:31b signed-confidence score, Fall (post hoc)', 'gemma_signed_ppe': 'gemma4:31b signed-confidence score, protective equipment (post hoc)',
          'qwen_signed_fall': 'qwen3.5:27b signed-confidence score, Fall (post hoc)', 'qwen_signed_ppe': 'qwen3.5:27b signed-confidence score, protective equipment (post hoc)',
          'qwen_fall': 'qwen3.5:27b single-pass fixed answer, Fall (post hoc run, final set only)', 'qwen_ppe': 'qwen3.5:27b single-pass fixed answer, protective equipment (final set only)',
          'illumination': 'dataset attribute', 'camera_distance': 'dataset attribute', 'size_band': 'largest labeled violation box as a share of the image (violation images)'}
SRC_SCORES = {'final': {'GROVE': 'runs/e50/d3_27b__h.jsonl', 'main_question': 'runs/e51/d3_27b__m.jsonl', 'gemma4:31b': 'runs/e52/gemma4_31b__sp.jsonl',
                        'signed': 'runs_posthoc/p07_final/*__spc.jsonl', 'qwen3.5:27b fixed': 'runs_posthoc/p06_final/qwen3.5_27b__sp.jsonl', 'labels and attributes': 'tools/cs10k_meta.json (from the ConstructionSite10k parquet files)', 'list': 'lists/final.json'},
              'calibration': {'GROVE': 'runs/e40/d3_27b__h.jsonl', 'main_question': 'runs/e41/d3_27b__m.jsonl', 'gemma4:31b': 'runs/e43/gemma4_31b__sp.jsonl',
                              'signed': 'runs_posthoc/p07_cal/*__spc.jsonl', 'labels and attributes': 'tools/cs10k_meta.json (from the ConstructionSite10k parquet files)', 'list': 'lists/calibration.json'}}

# ------------------------------------------------------------------ gallery: fixed selection rule on the final 1,000
import box_rescale as br
F = B['final']; ids, Y = F['ids'], F['Y']; IDX = {n: i for i, n in enumerate(ids)}
PG = gs.ge(F['SG'], np.array([TH_REFIT[c] for c in CATS2])); PM = gs.ge(F['SM'], np.array([TH_MQ[c] for c in CATS2]))
GRP = gd.cs_groups(ids); E53 = {(x['image'], x['category']): x for x in J('results/e53_grounding_predictions.json')['items']}
_, _, _, _, _, RAWSP = st.load_sp('e52', Bm, ids, cats=CATS2)
PROBS = {n: r['output']['probs'] for n, r in gcl.load_results('e50', M, 'h').items() if r['status'] == 'valid'}
QTEXT = dict(SETS['h']['questions'])
def lab_boxes(n): return gd.cs_boxes(n)
def top_iou(n, c):
    it = E53.get((n, c)); T = lab_boxes(n)[c]
    if not it or not it['boxes'] or not T: return 0.0
    return float(gs.iou_matrix(it['boxes'][:1], T).max())
def reason(n, c):
    rules = META[n]['rules']; return ' '.join((rules[k] or {}).get('reason') or '' for k in (('1',) if c == 'PPE_Violation' else ('2', '3')))
def err_class(n, c, kind):
    ph = (E53.get((n, c)) or {}).get('phrase'); r = reason(n, c)
    return st.classify_error(r if kind == 'miss' else (ph or '') + ' ' + r)
def illum(n): return str(META[n].get('illumination'))
def dist(n): return str(META[n].get('camera_distance'))
def gemma_wrong(i): return bool((F['Psp'][i] != Y[i]).any())
succ = []
for i, n in enumerate(ids):
    if not (PG[i] == Y[i]).all(): continue
    if all(top_iou(n, c) >= 0.5 for j, c in enumerate(CATS2) if PG[i, j]): succ.append(n)
succ = sorted(succ); rng = random.Random(SEED); order = list(succ); rng.shuffle(order)
chosen, used_groups, qlog = [], set(), []
def free(n): return n not in chosen and GRP[IDX[n]] not in used_groups
def take(n, why): chosen.append(n); used_groups.add(GRP[IDX[n]]); qlog.append({'id': n, 'reason': why})
QUOTAS = [('GROVE reports Fall', 4, lambda n: PG[IDX[n], 0]), ('GROVE reports protective equipment', 4, lambda n: PG[IDX[n], 1]),
          ('night', 2, lambda n: illum(n) == 'night'), ('long distance', 1, lambda n: dist(n) == 'long distance'),
          ('short distance', 1, lambda n: dist(n) == 'short distance'), ('mid distance', 1, lambda n: dist(n) == 'mid distance')]
quota_out = {}
for name, k, pred in QUOTAS:
    have = sum(1 for n in chosen if pred(n))
    while have < k:
        pool = [n for n in order if free(n) and pred(n)]
        if not pool: break
        pick = next((n for n in pool if gemma_wrong(IDX[n])), pool[0]); take(pick, 'quota: %s' % name); have += 1
    quota_out[name] = {'wanted': k, 'met': have}
while sum(gemma_wrong(IDX[n]) for n in chosen) < 8 and len(chosen) < 15:
    pool = [n for n in order if free(n) and gemma_wrong(IDX[n])]
    if not pool: break
    take(pool[0], 'gemma4:31b wrong (at least 8)')
for n in order:
    if len(chosen) >= 15: break
    if free(n): take(n, 'fill in draw order')
assert len(chosen) == 15, len(chosen)
FAIL_TYPES = [
    ('false alarm on a vest in daylight', 'GROVE flags protective equipment with the phrase about a vest, the label has no protective-equipment violation, normal lighting',
     lambda i, n: PG[i, 1] and not Y[i, 1] and 'vest' in ((E53.get((n, 'PPE_Violation')) or {}).get('phrase') or '') and illum(n) == 'normal lighting'),
    ('miss', 'labeled protective-equipment violation (hard hat or vest in the dataset reason) that GROVE does not flag, normal lighting',
     lambda i, n: Y[i, 1] and not PG[i, 1] and err_class(n, 'PPE_Violation', 'miss') == 'helmet or vest' and illum(n) == 'normal lighting'),
    ('right category, wrong worker boxed', 'GROVE flags a labeled protective-equipment violation correctly, but its top box does not overlap any labeled box (IoU 0)',
     lambda i, n: PG[i, 1] and Y[i, 1] and E53.get((n, 'PPE_Violation')) and (E53[(n, 'PPE_Violation')]['boxes'] or []) and top_iou(n, 'PPE_Violation') == 0.0),
    ('night-time miss', 'labeled violation that GROVE does not flag, illumination night',
     lambda i, n: illum(n) == 'night' and bool(((Y[i] == 1) & (PG[i] == 0)).any())),
    ('miss on height or depth', 'labeled Fall violation that GROVE does not flag, dataset reason about height or depth',
     lambda i, n: Y[i, 0] and not PG[i, 0] and err_class(n, 'Fall_Hazard', 'miss') == 'inferred height or depth')]
fails, fail_info = [], []
for name, rule, pred in FAIL_TYPES:
    cands = sorted(n for n in ids if pred(IDX[n], n)); pool = [n for n in cands if free(n)]
    if not pool: fail_info.append({'type': name, 'rule': rule, 'candidates': len(cands), 'picked': None}); continue
    n = rng.choice(pool); chosen.append(n); used_groups.add(GRP[IDX[n]]); fails.append((n, name)); fail_info.append({'type': name, 'rule': rule, 'candidates': len(cands), 'picked': n})
SUCC = chosen[:15]
TEASER = next(n for n in SUCC if PG[IDX[n]].any() and gemma_wrong(IDX[n]))
RULE = ('Selected examples, chosen by a fixed rule from the final 1,000 images, using only the saved scores, labels and attributes (no picture was looked at). '
        'Successes (15): images where both GROVE decisions (refit thresholds) match the labels and, for each category GROVE reports, its top box overlaps a labeled box with IoU 0.5 or more; '
        'the sorted image ids were shuffled with random.Random(%d); quotas were then filled in that order (at least 4 with Fall reported, 4 with protective equipment reported, 2 at night, '
        '1 each at long, short and mid camera distance; within a quota an image where gemma4:31b is wrong comes first), then images where gemma4:31b is wrong until there are at least 8, '
        'then the next images in order; no two images from one near-copy group. Failures (5): one per type, drawn with the same generator from the sorted ids of that type: %s.' % (SEED, '; '.join('%s (%s)' % (a, b) for a, b, _ in FAIL_TYPES)))

# ------------------------------------------------------------------ images: decoded as the run did (parquet bytes -> RGB), no metadata, no boxes burnt in
from PIL import Image
import pyarrow.parquet as pq
def decode(n):
    m = META[n]; t = pq.ParquetFile(os.path.join(gd.DCS, 'train', m['file'])).read_row_group(m['row_group'], columns=['image_id', 'image', 'image_caption']).to_pylist()
    r = next(x for x in t if str(x['image_id']) == n); im = r['image']; b = im['bytes'] if isinstance(im, dict) else im; CAPTION[n] = r.get('image_caption')
    im = Image.open(io.BytesIO(b)).convert('RGB'); return Image.frombytes('RGB', im.size, im.tobytes())   # fresh image: no EXIF, ICC or other metadata
CAPTION = {}
def save_all(n):
    im = decode(n); W0, H0 = im.size; assert (W0, H0) == (META[n]['W'], META[n]['H'])
    s = min(1.0, 1600.0 / max(W0, H0)); big = im if s == 1.0 else im.resize((round(W0 * s), round(H0 * s)), Image.LANCZOS)
    th = im.copy(); th.thumbnail((480, 480), Image.LANCZOS); out = {}
    for tag, img in (('', big), ('_thumb', th)):
        for ext, kw in (('webp', dict(format='WEBP', quality=82, method=6)), ('jpg', dict(format='JPEG', quality=82, optimize=True, progressive=True))):
            p = os.path.join(GAL, 'final_%s%s.%s' % (n, tag, ext)); img.save(p, **kw)
            with Image.open(p) as chk: assert not {'exif', 'icc_profile', 'xmp'} & set(chk.info), chk.info.keys()
            out[(tag[1:] or 'full') + '_' + ext] = 'gallery/final_%s%s.%s' % (n, tag, ext)
    return out, big.size, th.size, (W0, H0)
def nb(b, W, H): return [round(b[0] / W, 4), round(b[1] / H, 4), round(b[2] / W, 4), round(b[3] / H, 4)]
WHY = {x['id']: x['reason'] for x in qlog}
GALLERY = []
for n, role, ftype in [(n, 'success', None) for n in SUCC] + [(n, 'failure', t) for n, t in fails]:
    i = IDX[n]; files, (w, h), (tw, tht), (W0, H0) = save_all(n); LB = lab_boxes(n); raw = RAWSP.get(n) or {}; pr = PROBS[n]
    g = {'scores': {CAT[c]: r4(F['SG'][i, j]) for j, c in enumerate(CATS2)}, 'decisions': {CAT[c]: bool(PG[i, j]) for j, c in enumerate(CATS2)},
         'first_freeze_decisions': {CAT[c]: bool(F['SG'][i, j] >= TH_FIRST[c]) for j, c in enumerate(CATS2)},
         'boxes': {}, 'phrase': {}, 'box_source': {}, 'top_iou': {}, 'probs': {k: round(float(pr[k]), 4) for k in QTEXT}}
    for c in CATS2:
        it = E53.get((n, c))
        if it:
            g['boxes'][CAT[c]] = [nb(b, W0, H0) for b in (it['boxes'] or [])[:5]]; g['phrase'][CAT[c]] = it.get('phrase'); g['box_source'][CAT[c]] = it.get('source')
            g['top_iou'][CAT[c]] = round(top_iou(n, c), 4)
    gm = {'decisions': {CAT[c]: bool(F['Psp'][i, j]) for j, c in enumerate(CATS2)}, 'evidence': {}, 'box_as_written': {}, 'box_drawn': {}, 'fits_pixel_rule': {}, 'fits_grid_reading': {}}
    for c in CATS2:
        pc = (raw.get('parsed') or {}).get(c) or {}; gm['evidence'][CAT[c]] = pc.get('evidence')
        if pc.get('present') is True:
            b = pc.get('bbox'); gm['box_as_written'][CAT[c]] = b; px, gr = br.pixel_box(b, W0, H0), br.grid_box(b)
            gm['fits_pixel_rule'][CAT[c]] = bool(px); gm['fits_grid_reading'][CAT[c]] = bool(gr)
            if isinstance(b, list) and len(b) == 4 and all(isinstance(v, (int, float)) for v in b): gm['box_drawn'][CAT[c]] = nb(b, W0, H0)
    e = {'id': n, 'role': role, 'failure_type': ftype, 'draw_reason': WHY.get(n) or ('failure type: %s' % ftype), 'teaser': n == TEASER,
         'files': files, 'width': w, 'height': h, 'thumb_width': tw, 'thumb_height': tht, 'original_width': W0, 'original_height': H0,
         'illumination': illum(n), 'camera_distance': dist(n), 'size_band': size_band(n, bool(Y[i].any())),
         'caption': CAPTION.get(n), 'label_reason': {CAT[c]: (reason(n, c).strip() or None) for c in CATS2},
         'labels': {CAT[c]: bool(Y[i, j]) for j, c in enumerate(CATS2)}, 'label_boxes': {CAT[c]: [nb(b, W0, H0) for b in LB[c]] for c in CATS2},
         'grove': g, 'main_question': {'scores': {CAT[c]: r4(F['SM'][i, j]) for j, c in enumerate(CATS2)}, 'decisions': {CAT[c]: bool(PM[i, j]) for j, c in enumerate(CATS2)}},
         'gemma': gm, 'outcome': {'grove_correct': bool((PG[i] == Y[i]).all()), 'gemma_wrong': gemma_wrong(i), 'disagree': bool((PG[i] != F['Psp'][i]).any())}}
    if role == 'failure':
        e['error'] = [{'category': CAT[c], 'kind': 'false alarm' if PG[i, j] else 'miss', 'class': err_class(n, c, 'false alarm' if PG[i, j] else 'miss')} for j, c in enumerate(CATS2) if PG[i, j] != Y[i, j]]
    GALLERY.append(e)
GAL_OUT = {'set': 'final', 'n_images_in_set': len(ids), 'seed': SEED, 'selection_rule': RULE, 'candidates_successes': len(succ), 'success_draw_log': qlog, 'quotas': quota_out,
           'failure_types': fail_info, 'teaser': TEASER, 'thresholds_refit': tdict(TH_REFIT), 'thresholds_first_freeze': tdict(TH_FIRST),
           'questions': QTEXT, 'state': SETS['h']['state'], 'formula': {'fall': FORMULA_TEXT['Fall'], 'ppe': FORMULA_TEXT['PPE']}, 'weights': F2J['weights'],
           'weights_source': 'freeze/freeze_2.json (weights)', 'caption_source': 'ConstructionSite10k image_caption (used as alt text)',
           'dataset_citation': re.search(r'```bibtex\n(.*?)```', open(P('packet', 'data', 'constructionsite10k', 'upstream_README.md'), encoding='utf-8').read(), re.S).group(1).strip(),
           'dataset_citation_source': 'packet/data/constructionsite10k/upstream_README.md',
           'box_note': 'Boxes are stored as fractions of the image width and height. gemma4:31b boxes are drawn as written, read as pixel coordinates (the frozen rule); many of its boxes fit a 0-1000 grid reading instead (sensitivity analysis on the page).',
           'sources': {'scores': 'runs/e50 (GROVE), runs/e51 (main questions), runs/e52 (gemma4:31b)', 'boxes': 'results/e53_grounding_predictions.json (GROVE), runs/e52 parsed bbox (gemma4:31b)',
                       'labels': 'ConstructionSite10k annotations via tools/cs10k_meta.json', 'images': 'ConstructionSite10k parquet files, decoded as the run did (RGB), resized to at most 1600 px'},
           'images': GALLERY}

# ------------------------------------------------------------------ errors.json from reports\errors_final.md (post hoc)
ERR_MD = P('reports', 'errors_final.md'); txt = open(ERR_MD, encoding='utf-8').read().split('\n'); ERR = {'post_hoc': True, 'source': 'reports/errors_final.md', 'systems': {}}
cur = None
for l in txt:
    if l.startswith('## GROVE'): cur = 'GROVE'
    elif l.startswith('## Single-pass gemma4:31b'): cur = 'gemma4:31b'
    elif l.startswith('## Overlap'): cur = None
    m = re.match(r'\| (false alarm|miss) \| ([^|]+) \| (\d+) \| (\d+) \|', l)
    if cur and m: ERR['systems'].setdefault(cur, []).append({'type': m.group(1), 'class': m.group(2).strip(), 'all': int(m.group(3)), 'sample': int(m.group(4))})
    m2 = re.match(r'All errors: (\d+) \(false alarms (\d+), misses (\d+)\)', l)
    if cur and m2: ERR.setdefault('totals', {})[cur] = {'all': int(m2.group(1)), 'false_alarms': int(m2.group(2)), 'misses': int(m2.group(3))}
EJ = J(EF)
for s, rows in ERR['systems'].items():
    for r in rows: assert EJ['systems'][s]['all']['%s|%s' % (r['type'], r['class'])] == r['all']
ERR['note'] = 'Classes come from keywords in the system text and the dataset reason; "other or no text" means no keyword matched. Same method as experiment 60, repeated on the final 1,000 after final scoring.'

# ------------------------------------------------------------------ write
def wj(name, obj):
    p = os.path.join(DATA, name)
    with open(p, 'w', encoding='utf-8', newline='\n') as f: json.dump(obj, f, ensure_ascii=False, indent=1 if name not in ('final_scores.json', 'calibration_scores.json') else None, separators=None if name not in ('final_scores.json', 'calibration_scores.json') else (',', ':'))
    print('written', os.path.relpath(p, SITE), os.path.getsize(p))
GEN = {'generated_by': 'tools/export_site_data.py', 'run_folder': 'C:/GROVE_PC (read only)', 'rounding': 'scores rounded to 4 decimals without crossing a multiple of 0.01'}
wj('numbers.json', {'_about': GEN | {'note': 'every number on the page, with its source file (relative to the run folder) and key path; post_hoc marks analyses made after final scoring'}, 'numbers': NUM})
wj('final_scores.json', {'_about': GEN | {'set': 'final 1,000', 'fields': FIELDS, 'sources': SRC_SCORES['final']}, 'rows': ROWS['final']})
wj('calibration_scores.json', {'_about': GEN | {'set': 'calibration 500 (thresholds were fit on these images)', 'fields': {k: v for k, v in FIELDS.items() if not k.startswith('qwen_f') and not k == 'qwen_ppe'}, 'sources': SRC_SCORES['calibration']}, 'rows': ROWS['calibration']})
wj('thresholds.json', THRESH)
wj('gallery.json', GAL_OUT)
wj('errors.json', ERR)
print('successes', SUCC); print('failures', fails); print('teaser', TEASER); print('quotas', quota_out); print('candidates', len(succ), [(x['type'], x['candidates']) for x in fail_info])
print('numbers', len(NUM))
