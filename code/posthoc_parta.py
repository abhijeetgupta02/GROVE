"""POST HOC Part A of 2026-11-10 (logs\\deviations.md D24): saved results only, no model calls. New files only; refuses to overwrite.
  tables  Step 1: reports\\PAPER_TABLES.md, every number copied from an existing result or report file (named beside it). Computes nothing new.
  errors  Step 2: experiment 60 repeated on the final 1,000 for GROVE (refit thresholds) and single-pass gemma4:31b:
          reports\\errors_final.md, reports\\errors_final\\ (100 sampled errors per system, images copied unchanged, one CSV per system).
  upper   Step 3: box upper bound for each single-pass model and set (higher of as written and 0-1000 grid reading), GROVE minus that,
          paired bootstrap (4,000 draws, seed 20260422, the run's groups): reports\\box_upper_bound.md, results_posthoc\\box_upper_bound.json.
Usage: posthoc_parta.py tables|errors|upper
"""
import collections, csv, json, os, random, re, shutil, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import offline_20261110 as off          # sets the main mode; reuses its readers (no model calls)
from grove_common import MODE, G, read_json, now, CATS2, CATS3, SHORT, SEED, GENERATORS, f_fall, f_ppe
import grove_data as gd, grove_score as gs, grove_stages as st, grove_calls as gcl
RP = os.path.join(G, 'results_posthoc'); os.makedirs(RP, exist_ok=True)
new_file = off.new_file
def f4(x): return '-' if x is None else '%.4f' % x

# ------------------------------------------------------------------ step 3
def run_upper():
    res = {'POST_HOC': 'post hoc upper bound for single-pass boxes; the frozen pixel rule stays primary', 'written': now(), 'draws': off.DRAWS, 'seed': SEED, 'sets': {}}
    L = ['# POST HOC: box upper bound for the single-pass baselines', '',
         '**Post hoc analysis** (D24), written %s by `code\\posthoc_parta.py upper` from saved outputs; no model call. For each single-pass model and set, the reading of its saved raw boxes that gives the higher top-box F1 (as written under the frozen pixel rule, or read as 0-1000 grid coordinates) is taken, whatever the trust rule of `reports\\box_rescale.md` says. Choosing the better reading with the labels favours the baseline, so GROVE minus this is a conservative (lower-bound) comparison for GROVE. The primary result (frozen pixel rule) is unchanged.' % now(), '',
         '- Top box against top box, one-to-one within image and category, intersection over union 0.5 (primary) and 0.3, as in experiments 37, 45 and 54. The reading is chosen separately at each cutoff, once on the full set (not again inside each bootstrap draw).',
         '- Intervals: paired bootstrap, %d draws, seed %d, by same-scene group on the 203 and by near-copy group on the calibration and final images, the run\'s resampling code.' % (off.DRAWS, SEED),
         '- qwen3.5:27b was not run on the final set by the run; its post hoc final-set run (Part B, step 6) is scored in `reports\\posthoc_second_baseline.md`, with the same upper bound.', '',
         '| Set | Single-pass model | Cutoff | GROVE top-box F1 | As written | 0-1000 grid | Reading taken | GROVE minus upper bound (95% interval) |', '|---|---|---:|---:|---:|---:|---|---|']
    for key in ('203', 'cal', 'final'):
        S = off.set_info(key); names, cats, T, grp = S['names'], S['cats'], S['T'], S['groups']; gt = off.grove_top(key); rows = {}
        for m in GENERATORS:
            if not os.path.exists(gcl.job_path(S['exp'], m, 'sp')): continue
            wr, rs, n = off.sp_boxes(S['exp'], m, names, cats, S['src']); rows[m] = {}
            for cut in (0.5, 0.3):
                Cg = off.per_image_counts(gt, T, names, cats, cut); Cw = off.per_image_counts(wr, T, names, cats, cut); Cr = off.per_image_counts(rs, T, names, cats, cut)
                fw, fr, fg = float(off.box_f1(Cw.sum(0))), float(off.box_f1(Cr.sum(0))), float(off.box_f1(Cg.sum(0)))
                take, Cb = ('0-1000 grid', Cr) if fr > fw else ('as written', Cw)
                d = off.boot_box_diff(Cg, Cb, grp)
                rows[m][str(cut)] = {'GROVE': fg, 'as_written': fw, 'grid': fr, 'taken': take, 'difference': d}
                L.append('| %s | %s | %.1f | %.4f | %.4f | %.4f | %s | %+.4f [%+.4f, %+.4f] |' % (S['label'].split(' (')[0], m, cut, fg, fw, fr, take, *d))
        res['sets'][key] = rows
    L += ['', 'Same numbers in `results_posthoc\\box_upper_bound.json`.', '']
    new_file(os.path.join(G, 'reports', 'box_upper_bound.md'), '\n'.join(L) + '\n'); new_file(os.path.join(RP, 'box_upper_bound.json'), off.jdump(res))

# ------------------------------------------------------------------ step 2
def run_errors():
    ids = gd.list_ids('final'); Y = gd.Ycs(ids); f2 = read_json(MODE.path('freeze', 'freeze_2.json')); M = f2['selection']['main_model']; Bm = f2['best_baseline']['best']['model']
    qh, vh, _ = st.load_q('e50', M, 'h', ids); SG = np.stack([f_fall(qh), f_ppe(qh)], 1); PG = gs.ge(SG, st.final_th('GROVE'))
    Psp, vsp, _, _, _, raw = st.load_sp('e52', Bm, ids, cats=CATS2)
    ph = {(x['image'], x['category']): x.get('phrase') for x in read_json(MODE.path('results', 'e53_grounding_predictions.json'))['items']}
    meta = gd.meta(); out = {}
    def reason(n, cc):
        rules = meta[n]['rules']; return ' '.join((rules[k] or {}).get('reason') or '' for k in (('1',) if cc == 'PPE_Violation' else ('2', '3')))
    for sysname, P, txt, score in (('GROVE', PG, lambda n, cc: ph.get((n, cc)), lambda i, j: float(SG[i, j])),
                                   (Bm, Psp, lambda n, cc: (((raw.get(n) or {}).get('parsed') or {}).get(cc) or {}).get('evidence'), lambda i, j: None)):
        errs = []
        for i, n in enumerate(ids):
            for j, cc in enumerate(CATS2):
                if P[i, j] != Y[i, j]:
                    kind = 'false alarm' if P[i, j] else 'miss'; r = reason(n, cc); t = txt(n, cc)
                    errs.append({'image_id': n, 'category': cc, 'type': kind, 'score': score(i, j), 'system_text': t, 'dataset_reason': r,
                                 'error_class': st.classify_error(r if kind == 'miss' else (t or '') + ' ' + r)})
        out[sysname] = errs
    d = os.path.join(G, 'reports', 'errors_final')
    if os.path.exists(d): raise SystemExit('REFUSED: %s exists' % d)
    os.makedirs(d); res = {'POST_HOC': 'experiment 60 repeated on the final 1,000 after final scoring', 'written': now(), 'systems': {}}
    L = ['# POST HOC: false alarms and misses on the final 1,000 (experiment 60 repeated)', '',
         '**Post hoc analysis** (D24), written %s by `code\\posthoc_parta.py errors`, after final scoring, from saved outputs; no model call; nothing refit. Same method as experiment 60 (calibration): every image-category error (Fall, PPE) is classed from keywords in the system\'s text and the dataset reason (`grove_stages.classify_error`), and 100 errors per system are sampled with `random.Random(%d)`. GROVE uses its refit thresholds from `freeze_2.json` and its grounding phrase (experiment 53); single-pass %s uses its fixed answers and its own evidence text in place of a phrase. Images are copied unchanged into `reports\\errors_final` (file names start with the system), one CSV per system.' % (now(), SEED, Bm), '']
    for sysname, errs in out.items():
        cnt = collections.Counter((e['type'], e['error_class']) for e in errs); tot = collections.Counter(e['type'] for e in errs)
        pick = sorted(random.Random(SEED).sample(errs, min(100, len(errs))), key=lambda x: (x['type'], x['error_class'], x['image_id']))
        tag = 'GROVE' if sysname == 'GROVE' else 'singlepass_' + gcl.safe(sysname)
        for x in pick:
            x['file'] = '%s_%s_%s_%s.jpg' % (tag, x['type'].replace(' ', '_'), SHORT[x['category']], x['image_id'])
            shutil.copyfile(os.path.join(G, 'tools', 'cs10k_q95', '%s.q95.jpg' % x['image_id']), os.path.join(d, x['file']))
        with open(os.path.join(d, 'errors_%s.csv' % tag), 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(pick[0].keys())); w.writeheader(); [w.writerow(x) for x in pick]
        pc = collections.Counter((e['type'], e['error_class']) for e in pick); classes = sorted({k[1] for k in cnt})
        L += ['## %s' % ('GROVE (%s, refit thresholds)' % M if sysname == 'GROVE' else 'Single-pass %s (best single-pass, experiment 52)' % sysname), '',
              'All errors: %d (false alarms %d, misses %d). By category: %s.' % (len(errs), tot['false alarm'], tot['miss'], ', '.join('%s %d false alarms / %d misses' % (SHORT[c], sum(1 for e in errs if e['category'] == c and e['type'] == 'false alarm'), sum(1 for e in errs if e['category'] == c and e['type'] == 'miss')) for c in CATS2)), '',
              '| Type | Class | All errors | In the sample of %d |' % len(pick), '|---|---|---:|---:|']
        for t_ in ('false alarm', 'miss'):
            for c_ in classes:
                if cnt[(t_, c_)] or pc[(t_, c_)]: L.append('| %s | %s | %d | %d |' % (t_, c_, cnt[(t_, c_)], pc[(t_, c_)]))
        L += ['', 'Sample table: `reports\\errors_final\\errors_%s.csv`.' % tag, '']
        res['systems'][sysname] = {'all': {'%s|%s' % k: v for k, v in cnt.items()}, 'totals': dict(tot), 'sample': {'%s|%s' % k: v for k, v in pc.items()}, 'n_sample': len(pick)}
    both = set((e['image_id'], e['category']) for e in out['GROVE']) & set((e['image_id'], e['category']) for e in out[Bm])
    L += ['## Overlap', '', 'Image-category errors made by both systems: %d (GROVE %d, %s %d).' % (len(both), len(out['GROVE']), Bm, len(out[Bm])), '',
          'Classes come from keywords and are only as good as the text allows: "other or no text" means no keyword matched (for single-pass false alarms the evidence text is used; for misses only the dataset reason exists).', '']
    res['overlap'] = len(both)
    new_file(os.path.join(G, 'reports', 'errors_final.md'), '\n'.join(L) + '\n'); new_file(os.path.join(RP, 'errors_final.json'), off.jdump(res))

# ------------------------------------------------------------------ step 1
def md_section(path, heading_prefix, stop_level=None):
    """Lines from the heading that starts with heading_prefix up to the next heading of the same or higher level."""
    lines = open(path, encoding='utf-8').read().splitlines(); out = []; lvl = None
    for l in lines:
        m = re.match(r'^(#+) ', l)
        if lvl is None:
            if m and l[len(m.group(1)) + 1:].startswith(heading_prefix): lvl = len(m.group(1)); out.append(l)
        else:
            if m and len(m.group(1)) <= lvl: break
            out.append(l)
    if not out: raise SystemExit('section %r not found in %s' % (heading_prefix, path))
    return out
def shift(lines, add=2):
    return [('#' * add + l) if re.match(r'^#+ ', l) else l for l in lines]
def run_tables():
    R = lambda *p: os.path.join(G, *p); rep = lambda n: R('reports', n); res = lambda n: R('results', n)
    e15 = read_json(res('e15_screening.json')); e48 = read_json(res('e48.json'))['results']; e54 = read_json(res('e54_final.json')); e55 = read_json(res('e55_removal_final.json'))
    e24 = read_json(res('e24_30.json')); e07 = read_json(res('e07_lists.json')); sel = read_json(R('freeze', 'selection.json')); bb = read_json(R('freeze', 'best_baseline.json'))
    def row(setlab, thr, name, s, src, ci=None):
        pc = s.get('per_category') or {}
        return '| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (setlab, thr, name, f4(s.get('micro_f1')) + ((' [%.4f, %.4f]' % (ci[1], ci[2])) if ci else ''), f4(s.get('precision')), f4(s.get('recall')),
               ' / '.join(f4((pc.get(c) or {}).get('f1')) for c in pc), '%.1f' % s['false_alarms_per_100_negative'] if s.get('false_alarms_per_100_negative') is not None else '-', '%.3f' % s['completion'] if s.get('completion') is not None else '-', src)
    L = ['# Paper tables: every number with its source', '',
         'Written %s by `code\\posthoc_parta.py tables` (D24). **Nothing here is computed anew:** each number is copied from the result or report file named beside it (tables copied whole from a report say so above them). Final-set numbers are from final scoring (experiment 54, `logs\\final_scored.lock`). Rows marked post hoc or sensitivity come from the analyses of D23 and D24, not from the planned run.' % now(), '',
         '## 1. Datasets', '', 'Source: `reports\\FINAL_RESULTS.md` (Table 1), `results\\e07_lists.json`.', '']
    L += md_section(rep('FINAL_RESULTS.md'), 'Table 1. Datasets')[2:]
    for k in ('calibration', 'final'):
        v = e07[k]; L.append('- %s list (`results\\e07_lists.json`): n %s, with violation %s, without %s, top-up from tuning_rest %s, reference violation rate r %.4f (%s), visibility cutoff (largest box share) %.5f.' % (k, v['n'], v['n_with'], v['n_without'], v['top_up_from_tuning_rest'], v['reference_rate_r'], v['reference_pool'], v['visibility_cutoff_largest_box_share']))
    L += ['', '## 2. Screening on the 203 images (Table 2)', '', 'Copied from `reports\\screening.md` (numbers in `results\\e15_screening.json`, selection in `freeze\\selection.json`).', '']
    L += shift(md_section(rep('screening.md'), 'Table 2. Model screening'), 1)[1:] + ['']
    L += shift(md_section(rep('screening.md'), 'Gain from fact questions'), 1) + [''] + shift(md_section(rep('screening.md'), 'GROVE against single-pass models'), 1) + ['']
    L += ['### Selection (experiment 14)', '', '- Main model %s, Electrical from %s of %s, held-out micro-F1 %.4f, runner-up main model %s (`freeze\\selection.json`). Best single-pass for the new images: %s (experiment 46, `freeze\\best_baseline.json`).' % (sel['main_model'], sel['electrical_source']['option'], sel['electrical_source']['model'], sel['held_out_micro_f1'], sel['runner_up_main_model'], (bb.get('best') or {}).get('model')), '']
    L += ['## 3. GROVE, main questions and best single-pass (Table 3)', '',
          '| Set | Thresholds | System | Micro-F1 [95% interval where saved] | Precision | Recall | F1 per category | False alarms per 100 negatives | Completion | Source |', '|---|---|---|---|---:|---:|---|---:|---:|---|']
    k203 = {'GROVE': 'GROVE', 'Main questions only (m) %s' % sel['main_model']: 'main questions (%s)' % sel['main_model'], 'single-pass gemma4:31b': 'single-pass gemma4:31b (frozen best single-pass)', 'single-pass qwen3.5:27b': 'single-pass qwen3.5:27b (best on the 203)'}
    for k, lab in k203.items(): L.append(row('203 (Fall, Electrical, PPE)', 'held-out folds (10 x 5 grouped, fit on training folds); single-pass fixed', lab, e15[k], '`results\\e15_screening.json`'))
    for k, lab in (('e25 GROVE', 'GROVE'), ('e25 Main-question model', 'main questions (%s)' % sel['main_model']), ('e25 single-pass', 'single-pass qwen3.5:27b (best on the 203)')):
        L.append(row('203 (Fall, PPE only; experiment 25)', 'held-out folds; single-pass fixed', lab, e24[k], '`results\\e24_30.json`'))
    L.append('| 203 | first-freeze (fit on all 203) | all systems | not saved by the run (only the thresholds, `results\\e_thresholds_all203.json`; these are in-sample) | | | | | | - |')
    for thr in ('first_freeze', 'refit'):
        for k, lab in (('GROVE', 'GROVE'), ('main_question', 'main questions (%s)' % sel['main_model']), ('single-pass gemma4:31b', 'single-pass gemma4:31b (frozen best single-pass)'), ('single-pass qwen3.5:27b', 'single-pass qwen3.5:27b'), ('second_GROVE_questions', 'GROVE questions, runner-up model %s' % sel['runner_up_main_model'])):
            if k in e48[thr]: L.append(row('Calibration 500 (Fall, PPE; not independent)', {'first_freeze': 'first-freeze (from the 203)', 'refit': 'refit on these 500 (in-sample)'}[thr], lab, e48[thr][k], '`results\\e48.json`'))
    for k, lab in (('GROVE', 'GROVE'), ('main_question', 'main questions (%s)' % sel['main_model']), ('best single-pass', 'single-pass gemma4:31b (best single-pass)')):
        L.append(row('**Final 1,000** (Fall, PPE)', 'refit on calibration (primary); single-pass fixed', lab, e54[k], '`results\\e54_final.json`', e54[k].get('f1_ci')))
    L.append('| Final 1,000 | first-freeze | per-system scores | not saved by the run; only GROVE minus best single-pass below | | | | | | - |')
    cr = e54['criteria']; t = lambda x: '%+.4f [%+.4f, %+.4f]' % tuple(x)
    L += ['', 'Criteria on the final 1,000 (`results\\e54_final.json`, `criteria`):', '',
          '- Primary, GROVE minus best single-pass micro-F1: %s, met %s.' % (t(cr['primary']['difference']), cr['primary']['met']),
          '- False alarms per 100 negatives, GROVE minus best single-pass: %s, met %s.' % (t(cr['secondary_false_alarms']['difference_GROVE_minus_baseline']), cr['secondary_false_alarms']['met']),
          '- GROVE minus main questions: %s, met %s.' % (t(cr['secondary_main_question']['difference']), cr['secondary_main_question']['met']),
          '- Top-box F1 at 0.5: GROVE %.4f, best single-pass %.4f, met %s.' % (cr['secondary_top_box']['GROVE']['iou_0.5']['f1'], cr['secondary_top_box']['best single-pass']['iou_0.5']['f1'], cr['secondary_top_box']['met']),
          '- Valid-only sensitivity (%d images): %s. First-freeze thresholds, GROVE minus best single-pass: %s.' % (cr['valid_only_sensitivity']['images'], t(cr['valid_only_sensitivity']['difference']), t(cr['first_freeze_thresholds_sensitivity'])),
          '- Per category, GROVE minus best single-pass: %s.' % '; '.join('%s %s' % (SHORT[c], t(v)) for c, v in cr['per_category'].items()),
          '- Calibration (`results\\e48.json`), refit thresholds (in-sample): GROVE minus best single-pass micro-F1 %s, false alarms per 100 negatives %s; GROVE minus main questions %s. First-freeze thresholds: GROVE minus best single-pass micro-F1 %s, false alarms %s; GROVE minus main questions %s.' % (
                t(e48['refit']['GROVE minus best single-pass']['f1']), t(e48['refit']['GROVE minus best single-pass']['fa']), t(e48['refit']['GROVE minus main-question']),
                t(e48['first_freeze']['GROVE minus best single-pass']['f1']), t(e48['first_freeze']['GROVE minus best single-pass']['fa']), t(e48['first_freeze']['GROVE minus main-question'])), '']
    L += ['## 4. Per category (Table 4)', '', '203 images: F1 per category in section 2 and section 3 (held-out). Calibration and final: copied from `reports\\per_category_subgroups.md` (numbers in `results\\e57_59.json`).', '']
    for s_ in ('Calibration (500 images, not independent)', 'Final test (1000 images)'):
        sec = md_section(rep('per_category_subgroups.md'), s_); cut = next((i for i, l in enumerate(sec) if l.startswith('####')), len(sec)); L += shift(sec[:cut], 1) + ['']
    L += ['## 5. Subgroups', '', 'Copied from `reports\\per_category_subgroups.md` (experiment 58) and `reports\\calibration.md`.', '']
    for s_ in ('Subgroups, Calibration (500 images, not independent), GROVE', 'Subgroups, Calibration (500 images, not independent), main_question', 'Subgroups, Calibration (500 images, not independent), single-pass gemma4:31b',
               'Subgroups, Final test (1000 images), GROVE', 'Subgroups, Final test (1000 images), main_question', 'Subgroups, Final test (1000 images), single-pass gemma4:31b'):
        L += md_section(rep('per_category_subgroups.md'), s_) + ['']
    L += ['## 6. False alarms and prevalence-standardized precision', '',
          '- Calibration and final: the false-alarm and prevalence-standardized tables in section 4 (copied from `reports\\per_category_subgroups.md`, experiment 59).',
          '- Final, GROVE minus best single-pass, false alarms per 100 negatives: %s (`results\\e54_final.json`).' % t(cr['secondary_false_alarms']['difference_GROVE_minus_baseline']),
          '- 203 images: copied from `reports\\intervals_addendum.md` (D23, offline, after final scoring):', '']
    L += md_section(rep('intervals_addendum.md'), 'B. False alarms')[2:] + ['']
    L += ['## 7. Removing one part at a time (Table 5)', '', '### 203 images (copied from `reports\\removal_tests.md`, numbers in `results\\e16_21.json`)', '']
    L += [l for l in open(rep('removal_tests.md'), encoding='utf-8').read().splitlines()[2:]] + ['']
    L += ['### Final 1,000 (`results\\e55_removal_final.json`; thresholds from `freeze_2.json`, unchanged)', '', '| Variant | Micro-F1 | Micro-F1 change against GROVE (95% interval) |', '|---|---:|---|']
    for k, v in e55.items(): L.append('| %s | %.4f | %s |' % (k, v['summary']['micro_f1'], t(v['difference_from_GROVE'])))
    e44 = read_json(res('e44.json')); L += ['', '### Calibration 500 (`results\\e44.json`, refit thresholds, in-sample)', '', '| System | Micro-F1 refit | Micro-F1 first-freeze |', '|---|---:|---:|']
    for k, v in e44.items(): L.append('| %s | %s | %s |' % (k, f4((v.get('refit') or {}).get('micro_f1')), f4((v.get('first_freeze') or {}).get('micro_f1'))))
    L += ['', '## 8. Grounding, top box against top box (Table 6)', '', '### 203 images (copied from `reports\\grounding.md`, numbers in `results\\e31_38.json`)', '']
    L += open(rep('grounding.md'), encoding='utf-8').read().splitlines()[2:] + ['', '### Calibration 500 (copied from `reports\\calibration.md`, numbers in `results\\e45.json`)', '']
    L += shift(md_section(rep('calibration.md'), 'Grounding on flagged categories'), 1)[1:]
    gt_ = cr['secondary_top_box']; up5 = cr.get('GROVE_up_to_5_boxes') or {}
    L += ['', '### Final 1,000 (`results\\e54_final.json`, `criteria.secondary_top_box`)', '', '| System | Box F1 at 0.5 | Box precision at 0.5 | Box recall at 0.5 | Box F1 at 0.3 |', '|---|---:|---:|---:|---:|']
    for k in ('GROVE', 'best single-pass'): L.append('| %s top box | %.4f | %.4f | %.4f | %.4f |' % (k, gt_[k]['iou_0.5']['f1'], gt_[k]['iou_0.5']['precision'], gt_[k]['iou_0.5']['recall'], gt_[k]['iou_0.3']['f1']))
    if up5: L.append('| GROVE up to 5 boxes (reported separately, never compared) | %.4f | %.4f | %.4f | %.4f |' % (up5['iou_0.5']['f1'], up5['iou_0.5']['precision'], up5['iou_0.5']['recall'], up5['iou_0.3']['f1']))
    L += ['', '### Sensitivity analysis (D18, D23): single-pass boxes read as 0-1000 grid coordinates (copied from `reports\\box_rescale.md`; intervals from `reports\\intervals_addendum.md`)', '']
    for s_ in ('203 development images', 'Calibration 500', 'Final 1,000'): L += shift(md_section(rep('box_rescale.md'), s_), 2) + ['']
    L += shift(md_section(rep('intervals_addendum.md'), 'A. Top-box F1'), 1) + ['']
    if os.path.exists(rep('box_upper_bound.md')): L += ['Post hoc upper bound for the single-pass boxes: `reports\\box_upper_bound.md` (D24).', '']
    L += ['## 9. Speed and memory (Table 7)', '', 'Copied from `reports\\speed.md` (numbers in `results\\e56_speed.json`).', ''] + open(rep('speed.md'), encoding='utf-8').read().splitlines()[2:] + ['']
    L += ['## 10. Completion', '', 'Copied from `reports\\FINAL_RESULTS.md`.', ''] + md_section(rep('FINAL_RESULTS.md'), 'Completion and failures')[2:] + ['']
    new_file(rep('PAPER_TABLES.md'), '\n'.join(L) + '\n')

if __name__ == '__main__':
    {'tables': run_tables, 'errors': run_errors, 'upper': run_upper}[sys.argv[1]]()
