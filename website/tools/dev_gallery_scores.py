"""Scores, labels and GROVE boxes of the 29 generated development images, from the run's saved files (read only).
Run with a copy of the run code whose G (code/grove_common.py) points at the run folder: python3 dev_gallery_scores.py
Writes dev_gemini.json, which tools/build_dev_gallery.py turns into src/data/gallery.json and public/gallery/."""
import sys, os, json, base64, io
sys.path.insert(0, os.environ.get('GROVE_CODE', 'code')); sys.dont_write_bytecode = True
import numpy as np
from PIL import Image
import grove_calls as gcl
from grove_common import f_fall, f_ppe, f_elec, FIXED_PHRASES
G = os.environ.get('GROVE_PC', r'C:\GROVE_PC')
GEM = None
def jl(p): return {json.loads(l)['image_name']: json.loads(l) for l in open(p) if l.strip()}
H = jl(G + '/runs/e12/d3_27b__h.jsonl'); M = jl(G + '/runs/e11/d3_27b__m.jsonl'); SP = jl(G + '/runs/e09/gemma4_31b__sp.jsonl')
import grove_data as gdata
D = gdata.g203(); dims = D['dims'] if 'dims' in D else None
lab = {}
for (n, c), bl in D['boxes'].items():
    cc = {'Fall_Hazard': 'fall', 'PPE_Violation': 'ppe', 'Electrocution_Hazard': 'electrical'}.get(c)
    if not cc: continue
    w, h = dims[n]; lab.setdefault(n, {})[cc] = [[x0 / w, y0 / h, x1 / w, y1 / h] for x0, y0, x1, y1 in bl]
coco_names = set(dims)
GEM = [n for n, ai in zip(D['names'], D['ai']) if ai]
print('AI tagged', len(GEM), GEM)
gd = {}
for l in open(G + '/results/gcache_gdino.jsonl'):
    d = json.loads(l); gd[d['k']] = d['v']
TH = {'fall': 0.86, 'ppe': 0.80, 'electrical': 0.32}; FF = {'fall': 0.12, 'ppe': 0.50, 'electrical': 0.32}
KEY = {'fall': 'Fall_Hazard', 'ppe': 'PPE_Violation', 'electrical': 'Electrocution_Hazard'}
def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1])); I = ix * iy
    U = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - I; return I / U if U > 0 else 0
out = []
for n in GEM:
    p = H[n]['output']['probs']; q = {k: np.array([v]) for k, v in p.items()}
    sc = {'fall': float(f_fall(q)[0]), 'ppe': float(f_ppe(q)[0]), 'electrical': float(f_elec(q)[0])}
    d = gcl.load_203(n); pil = Image.open(io.BytesIO(base64.b64decode(d['b64']))).convert('RGB'); W, Hh = pil.size
    L = lab.get(n, {})
    rec = {'id': n, 'in_coco': n in coco_names, 'size': [W, Hh], 'probs': p, 'scores': sc, 'labels': {c: bool(L.get(c)) for c in TH}, 'label_boxes': {c: L.get(c, []) for c in TH},
           'dec': {c: sc[c] >= FF[c] for c in TH}, 'refit': {c: sc[c] >= TH[c] for c in TH}, 'main': {c: M[n]['output']['probs'][KEY[c]] for c in TH} if M.get(n, {}).get('output') else None,
           'grove_boxes': {}, 'phrase': {}, 'top_iou': {}, 'status_h': H[n]['status']}
    for c in TH:
        if not rec['dec'][c]: continue
        keys = list(FIXED_PHRASES[KEY[c]]); k = keys[int(np.argmax([p[x] for x in keys]))]; ph = FIXED_PHRASES[KEY[c]][k]
        dets = gd.get(d['sha'] + '|' + ph, {}).get('dets', [])
        rec['phrase'][c] = ph
        if dets:
            b = dets[0]['box']; bb = [b[0] / W, b[1] / Hh, b[2] / W, b[3] / Hh]; rec['grove_boxes'][c] = [round(v, 4) for v in bb]
            rec['top_iou'][c] = round(max([iou(bb, t) for t in L.get(c, [])] or [0]), 4)
    o = (SP.get(n, {}).get('output') or {}).get('parsed') or {}
    rec['gemma'] = {c: o.get(KEY[c]) for c in TH}
    rec['correct'] = all(rec['dec'][c] == rec['labels'][c] for c in TH)
    rec['good'] = rec['correct'] and all(rec['top_iou'].get(c, 0) >= 0.5 for c in TH if rec['dec'][c])
    rec['gemma_wrong'] = any(bool((rec['gemma'].get(c) or {}).get('present')) != rec['labels'][c] for c in TH)
    out.append(rec)
json.dump(out, open('dev_gemini.json', 'w'), indent=1)
for r in out:
    print(r['id'], r['size'], 'lab', ''.join('FPE'[i] if r['labels'][c] else '-' for i, c in enumerate(TH)), 'dec', ''.join('FPE'[i] if r['dec'][c] else '-' for i, c in enumerate(TH)),
          'sc', {c: round(v, 2) for c, v in r['scores'].items()}, 'iou', r['top_iou'], 'good' if r['good'] else '', 'gemmaWrong' if r['gemma_wrong'] else '')
