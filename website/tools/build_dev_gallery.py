"""Builds src/data/gallery.json and public/gallery/ from our generated development images.

Usage: python3 tools/build_dev_gallery.py <dev_gemini.json from tools/dev_gallery_scores.py> <folder with the 203 development images>
The seven images were picked by looking at the generated images where GROVE is right on all three categories with the
thresholds fit on the 203 development images, with a GroundingDINO box at IoU 0.5 or more for each reported category.
"""
import json, os, sys
from PIL import Image
DEVJ, SRC = sys.argv[1], sys.argv[2]
R = {r['id']: r for r in json.load(open(DEVJ))}
G = json.load(open('src/data/gallery.json', encoding='utf-8'))
SEL = ['191.png', '200.png', '196.png', '183.png', '197.png', '178.png', '181.png']
TEASER = '191'
FF = {'fall': 0.12, 'ppe': 0.50}; MQ = {'fall': 0.16, 'ppe': 0.58}   # thresholds fit on the 203 images (freeze/freeze_1.json)
GAL = 'public/gallery'
for f in os.listdir(GAL): os.remove(os.path.join(GAL, f))
def r4(x): return round(float(x), 4)
imgs = []
for n in SEL:
    r = R[n]; i = n.split('.')[0]; im = Image.open(os.path.join(SRC, n)).convert('RGB'); W0, H0 = im.size
    s = min(1.0, 1600.0 / max(W0, H0)); big = im if s == 1.0 else im.resize((round(W0 * s), round(H0 * s)), Image.LANCZOS)
    th = im.copy(); th.thumbnail((480, 480), Image.LANCZOS); files = {}
    for tag, img in (('', big), ('_thumb', th)):
        for ext, kw in (('webp', dict(format='WEBP', quality=82, method=6)), ('jpg', dict(format='JPEG', quality=82, optimize=True, progressive=True))):
            fn = 'gallery/dev_%s%s.%s' % (i, tag, ext); img.save('public/' + fn, **kw); files[('full_' if not tag else 'thumb_') + ext] = fn
    W, H = r['size']; sp = r['gemma']; p = r['probs']
    gem = {'decisions': {}, 'evidence': {}, 'box_as_written': {}, 'box_drawn': {}, 'fits_pixel_rule': {}, 'fits_grid_reading': {}}
    for c in ('fall', 'ppe'):
        a = sp.get(c) or {}; pres = bool(a.get('present')); gem['decisions'][c] = pres
        if pres:
            gem['evidence'][c] = a.get('evidence'); b = a.get('bbox') or []
            if len(b) == 4:
                gem['box_as_written'][c] = b; gem['box_drawn'][c] = [r4(b[0] / W), r4(b[1] / H), r4(b[2] / W), r4(b[3] / H)]
                gem['fits_pixel_rule'][c] = all(0 <= v for v in b) and b[2] <= W and b[3] <= H; gem['fits_grid_reading'][c] = all(0 <= v <= 1000 for v in b)
    labels = {c: r['labels'][c] for c in ('fall', 'ppe')}
    dec = {c: r['scores'][c] >= FF[c] for c in ('fall', 'ppe')}
    assert all(dec[c] == labels[c] for c in dec) and not r['labels']['electrical'] and not r['dec']['electrical']
    gw = any(gem['decisions'][c] != labels[c] for c in labels)
    imgs.append({'id': i, 'role': 'success', 'failure_type': None, 'draw_reason': 'chosen by the authors from the generated development images where GROVE is right',
        'teaser': i == TEASER, 'files': files, 'width': big.size[0], 'height': big.size[1], 'thumb_width': th.size[0], 'thumb_height': th.size[1],
        'original_width': W0, 'original_height': H0, 'illumination': 'generated with Google Gemini', 'camera_distance': 'development image', 'size_band': None,
        'caption': None, 'label_reason': {'fall': None, 'ppe': None}, 'labels': labels,
        'label_boxes': {c: [[r4(v) for v in b] for b in r['label_boxes'][c]] for c in ('fall', 'ppe')},
        'grove': {'scores': {c: r4(r['scores'][c]) for c in ('fall', 'ppe')}, 'decisions': dec, 'first_freeze_decisions': dec,
                  'boxes': {c: [r['grove_boxes'][c]] for c in ('fall', 'ppe') if dec[c]}, 'phrase': {c: r['phrase'][c] for c in ('fall', 'ppe') if dec[c]},
                  'box_source': {c: 'GroundingDINO' for c in ('fall', 'ppe') if dec[c]}, 'top_iou': {c: r['top_iou'][c] for c in ('fall', 'ppe') if dec[c]},
                  'probs': {k: r4(v) for k, v in p.items()}},
        'main_question': {'scores': {c: r4(r['main'][c]) for c in ('fall', 'ppe')}, 'decisions': {c: r['main'][c] >= MQ[c] for c in ('fall', 'ppe')}},
        'gemma': gem, 'outcome': {'grove_correct': True, 'gemma_wrong': gw, 'disagree': any(gem['decisions'][c] != dec[c] for c in dec)}})
G['images'] = imgs; G['teaser'] = TEASER; G['candidates_successes'] = len(SEL)
with open('src/data/gallery.json', 'w', encoding='utf-8', newline='\n') as f: json.dump(G, f, ensure_ascii=False, indent=1)
print(len(imgs), 'images')
