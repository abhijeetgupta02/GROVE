"""Sensitivity analysis for single-pass boxes (added to the plan on 2026-11-05, before any full-run box score existed; logs\\deviations.md D18).

For all 6 single-pass models, each saved raw box (output.parsed[category].bbox, as the model wrote it) is treated as 0-1000 grid
coordinates of the image the model saw, converted to pixels (x * width / 1000, y * height / 1000), and scored with the same
top-box matching as experiments 37, 45 and 54 (grove_score.box_eval, one-to-one, IoU 0.5 and 0.3). The as-written result
(the frozen rule: 4 integers inside the image in pixels) is recomputed with the same code path and shown beside it, and checked
against the stored results.

Sets: the 203 images (experiment 9, Fall, Electrical, PPE), the calibration images (experiment 43, the models that ran),
and the final images (experiment 52) only if logs\\final_scored.lock exists.

Writes only reports\\box_rescale_sensitivity.md (or --out). Changes no result, report, freeze file, list or rule; the frozen
pixel rule stays primary. Refuses to run before logs\\ALL_DONE.txt exists.
Usage: box_rescale.py [--mode main|pilot] [--out PATH]
"""
import argparse, hashlib, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
GRID = 1000

def grid_box(b):
    """True if b is 4 integers with 0 <= x1 < x2 <= 1000 and 0 <= y1 < y2 <= 1000 (the grid version of the pixel rule)."""
    if not (isinstance(b, list) and len(b) == 4 and all(isinstance(v, int) and not isinstance(v, bool) for v in b)): return False
    x1, y1, x2, y2 = b
    return 0 <= x1 < x2 <= GRID and 0 <= y1 < y2 <= GRID

def to_pixels(b, W, H):
    x1, y1, x2, y2 = b
    return [x1 * W / GRID, y1 * H / GRID, x2 * W / GRID, y2 * H / GRID]

def pixel_box(b, W, H):
    """The frozen rule (grove_calls._box): 4 integers with 0 <= x1 < x2 <= W and 0 <= y1 < y2 <= H."""
    if not (isinstance(b, list) and len(b) == 4 and all(isinstance(v, int) and not isinstance(v, bool) for v in b)): return False
    x1, y1, x2, y2 = b
    return 0 <= x1 < x2 <= W and 0 <= y1 < y2 <= H

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''): h.update(blk)
    return h.hexdigest()

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--mode', default='main'); ap.add_argument('--out', default=None); a = ap.parse_args(argv)
    from grove_common import set_mode, read_json, now, CATS2, CATS3, GENERATORS, G, PK
    MODE = set_mode(a.mode)
    if not os.path.exists(MODE.path('logs', 'ALL_DONE.txt')):
        print('REFUSED: logs\\ALL_DONE.txt does not exist yet; run this after the run has finished.'); return 2
    import grove_data as gd, grove_score as gs, grove_stages as st, grove_calls as gcl
    from PIL import Image
    lock = os.path.exists(MODE.path('logs', 'final_scored.lock'))
    sizes = {}
    def size(name, src):
        if (name, src) not in sizes:
            p = os.path.join(PK, 'data', 'grove203', 'encoded_q95', name + '.q95.jpg') if src == '203' else os.path.join(gcl.CS_CACHE, '%s.q95.jpg' % name)
            with Image.open(p) as im: sizes[(name, src)] = im.size  # the image size the model saw (same file as the call)
        return sizes[(name, src)]

    def rescaled(exp, model, names, src, cats):
        R = gcl.load_results(exp, model, 'sp', set(names)); B = {}; n = dict(valid=0, present=0, pixel_ok=0, grid_ok=0, both_ok=0, neither=0)
        for name in names:
            r = R.get(name)
            if not r or r['status'] != 'valid': continue
            n['valid'] += 1; p = r['output']['parsed']; W, H = size(name, src)
            for c in cats:
                if p[c]['present'] is not True: continue
                b = p[c]['bbox']; n['present'] += 1; px, gr = pixel_box(b, W, H), grid_box(b)
                n['pixel_ok'] += px; n['grid_ok'] += gr; n['both_ok'] += px and gr; n['neither'] += (not px) and (not gr)
                if gr: B[(name, c)] = [to_pixels(b, W, H)]
        return B, n

    def stored(path, *keys):
        d = read_json(MODE.path('results', path))
        for k in keys:
            if not isinstance(d, dict) or k not in d: return None
            d = d[k]
        return d

    def same(x, y):
        if not isinstance(y, dict): return 'no stored value'
        ok = all(abs(x['iou_%s' % c][k] - y['iou_%s' % c][k]) < 1e-9 for c in ('0.5', '0.3') for k in ('f1', 'matched', 'pred_boxes', 'true_boxes'))
        return 'yes' if ok else 'NO'

    sets = [('203 images (experiment 9; Fall, Electrical, PPE)', 'e09', list(gd.g203()['names']), '203', CATS3, st.true_203, ('e31_38.json', 'evaluation', '37 single-pass {m}', 'top'), ('e31_38.json', 'evaluation', '36 both, as designed', 'top')),
            ('Calibration images (experiment 43; Fall, PPE)', 'e43', gd.list_ids('calibration'), 'cs', CATS2, None, ('e45.json', 'evaluation', 'single-pass {m}'), ('e45.json', 'evaluation', 'GROVE top box'))]
    if lock:
        sets.append(('Final images (experiment 52; Fall, PPE)', 'e52', gd.list_ids('final'), 'cs', CATS2, None, ('e54_final.json', 'criteria', 'secondary_top_box', 'best single-pass'), ('e54_final.json', 'criteria', 'secondary_top_box', 'GROVE')))
    me = os.path.abspath(__file__); f1 = read_json(MODE.path('freeze', 'freeze_1.json')) or {}; f2 = read_json(MODE.path('freeze', 'freeze_2.json')) or {}
    reg1 = (f1.get('code_hashes') or {}).get('box_rescale.py'); reg2 = (f2.get('code_hashes') or {}).get('box_rescale.py'); mine = sha256(me)
    L = ['# Single-pass box sensitivity: raw boxes read as 0-1000 grid coordinates', '',
         'Written %s by code\\box_rescale.py (%s mode). **Sensitivity only.** The frozen rule (a box counts only if it is 4 integers inside the image in pixels) stays the primary result; nothing here changes any result, report, threshold, selection, freeze file or criterion.' % (now(), MODE.name), '',
         '- Rescaled: every answer with present = true whose raw box is 4 integers with 0 <= x1 < x2 <= 1000 and 0 <= y1 < y2 <= 1000 is converted to pixels as (x * width / 1000, y * height / 1000), using the size of the image the model was sent. Other boxes count as no box, as in the frozen rule.',
         '- Scoring: the same one-to-one top-box matching as experiments 37, 45 and 54 (grove_score.box_eval), IoU 0.5 (primary) and 0.3, against the same true boxes (all boxes in the scored categories).',
         '- As written: recomputed with the experiment code path (grove_stages.load_sp, then box_eval) and checked against the stored result.',
         '- Final images: %s.' % ('included (logs\\final_scored.lock exists)' if lock else 'not included (logs\\final_scored.lock does not exist)'),
         '- code\\box_rescale.py SHA-256 now %s; in freeze_1.json code hashes: %s; in freeze_2.json: %s.' % (mine, 'same' if reg1 == mine else (reg1 or 'not recorded'), 'same' if reg2 == mine else (reg2 or 'not recorded')), '']
    f = lambda x: '-' if x is None or (isinstance(x, float) and math.isnan(x)) else '%.4f' % x
    for title, exp, names, src, cats, truef, skey, gkey in sets:
        T = truef(names, cats) if truef else st.true_cs(names, cats)
        L += ['## ' + title, '', 'Images %d; true boxes %d.' % (len(names), sum(len(v) for v in T.values())), '',
              '| Model | Valid answers | Answers with present = true | Raw boxes inside the image as pixels | Raw boxes inside the 0-1000 grid | Inside both | Inside neither | Box F1 at 0.5, as written | Box F1 at 0.5, rescaled | Box F1 at 0.3, as written | Box F1 at 0.3, rescaled | Precision / recall at 0.5, as written | Precision / recall at 0.5, rescaled | As written equals stored result |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
        ran = [m for m in GENERATORS if os.path.exists(gcl.job_path(exp, m, 'sp'))]
        for m in GENERATORS:
            if m not in ran: L.append('| %s | not run in experiment %d | | | | | | | | | | | | |' % (m, int(exp[1:]))); continue
            P, v, Bw, _, _, _ = st.load_sp(exp, m, names, cats=cats)
            Br, n = rescaled(exp, m, names, src, cats)
            ew, _ = gs.box_eval(Bw, T); er, _ = gs.box_eval(Br, T)
            sk = [k.format(m=m) for k in skey]; chk = same(ew, stored(*sk))
            L.append('| %s | %d | %d | %d | %d | %d | %d | %s | %s | %s | %s | %s / %s | %s / %s | %s |' % (
                m, n['valid'], n['present'], n['pixel_ok'], n['grid_ok'], n['both_ok'], n['neither'], f(ew['iou_0.5']['f1']), f(er['iou_0.5']['f1']), f(ew['iou_0.3']['f1']), f(er['iou_0.3']['f1']),
                f(ew['iou_0.5']['precision']), f(ew['iou_0.5']['recall']), f(er['iou_0.5']['precision']), f(er['iou_0.5']['recall']), chk))
        g = stored(*gkey)
        if isinstance(g, dict):
            L += ['', 'For reference (stored result, unchanged): GROVE top box F1 at 0.5 %s, at 0.3 %s.' % (f(g['iou_0.5']['f1']), f(g['iou_0.3']['f1']))]
        L.append('')
    out = a.out or MODE.path('reports', 'box_rescale_sensitivity.md')
    with open(out + '.tmp', 'w', encoding='utf-8') as fh: fh.write('\n'.join(L) + '\n')
    os.replace(out + '.tmp', out); print('written', out); return 0

if __name__ == '__main__':
    sys.exit(main())
