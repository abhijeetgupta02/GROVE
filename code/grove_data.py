"""Labels, groups and images for the 203 benchmark and ConstructionSite10k (Section 6, Section 14 Part 7)."""
import collections, csv, io, json, os, re, sys
import numpy as np
from PIL import Image
from grove_common import *
sys.path.insert(0, os.path.join(PK, 'code', 'reference_mac'))
import hazard_taxonomy as ht
D203 = os.path.join(PK, 'data', 'grove203'); DCS = os.path.join(PK, 'data', 'constructionsite10k')
GROUPS_203 = '36,56,57,58,59,60,61,62,63,77,78,79,80 | 65,66,67,68,69,70 | 52,53 | 38,44,45,49 | 93,106 | 102,105 | 87,97,104 | 91,98,107 | 95,96 | 100,103'
AI_TAGGED = [int(x) for x in '90,125,126,171,172,173,175,176,177,178,179,180,181,182,183,185,186,187,188,189,190,191,194,196,197,198,200,201,202'.split(',')]
BLOCKS = [(1, 35), (36, 80), (81, 107), (108, 170), (171, 203)]
ALL7 = ht.CANONICAL_CATEGORIES

def fnum(n): return int(re.match(r'\d+', n).group())
_G203 = None
def g203():
    """names sorted as strings (like the Mac scripts), labels, boxes (xyxy pixels), same-scene groups."""
    global _G203
    if _G203: return _G203
    names = sorted(ht.normalize_image_name(r['image_name']) for r in csv.DictReader(open(os.path.join(D203, 'image_list.csv'), encoding='utf-8')))
    assert len(names) == 203 and len(set(names)) == 203
    coco = json.load(open(os.path.join(D203, 'annotations.coco.json'), encoding='utf-8'))
    cn = {c['id']: c['name'] for c in coco['categories']}; nm = {i['id']: ht.normalize_image_name(i['file_name']) for i in coco['images']}
    dims = {nm[i['id']]: (int(float(i['width'])), int(float(i['height']))) for i in coco['images']}
    gt = collections.defaultdict(set); boxes = collections.defaultdict(list); raw_boxes = collections.Counter()
    for a in coco['annotations']:
        n = nm[a['image_id']]; c = ht.map_gt_category(cn[a['category_id']]); gt[n].add(c); raw_boxes[c] += 1
        x, y, w, h = [float(v) for v in a['bbox']]; boxes[(n, c)].append([x, y, x + w, y + h])
    assert set(gt) <= set(names)
    ID = {n: k for k, n in enumerate(names)}; grp = np.arange(203)
    for g in GROUPS_203.split('|'):
        nums = [int(x) for x in g.split(',')]; members = [ID[n] for k in nums for n in names if fnum(n) == k]
        first = [ID[n] for n in names if fnum(n) == nums[0]][0]
        for i in members: grp[i] = first
    nums = np.array([fnum(n) for n in names])
    def Y(cats): return np.array([[c in gt.get(n, set()) for c in cats] for n in names])
    _G203 = dict(names=names, ID=ID, gt=gt, boxes=boxes, dims=dims, groups=grp, nums=nums, Y=Y, raw_box_counts=raw_boxes,
                 labeled=np.array([len(gt.get(n, set())) > 0 for n in names]), ai=np.isin(nums, AI_TAGGED))
    return _G203

# ---------------------------------------------------------------- ConstructionSite10k
META_P = os.path.join(G, 'tools', 'cs10k_meta.json')
def parquet_files(): return sorted(os.path.join(DCS, 'train', f) for f in os.listdir(os.path.join(DCS, 'train')) if f.endswith('.parquet'))
def splits(): return json.load(open(os.path.join(DCS, 'splits', 'train_splits.json'), encoding='utf-8'))
def build_meta():
    """One pass over the parquet files: labels, boxes, conditions and image size per image_id. Cached in tools\\cs10k_meta.json."""
    import pyarrow.parquet as pq
    meta = {}
    for f in parquet_files():
        pf = pq.ParquetFile(f); row0 = 0
        for rg in range(pf.num_row_groups):
            t = pf.read_row_group(rg).to_pylist()
            for k, r in enumerate(t):
                im = r['image']; b = im['bytes'] if isinstance(im, dict) else im
                with Image.open(io.BytesIO(b)) as I: W, H = I.size
                rules = {}
                for j in (1, 2, 3, 4):
                    v = r.get('rule_%d_violation' % j)
                    rules[str(j)] = None if v is None else {'boxes': v.get('bounding_box') or [], 'reason': v.get('reason')}
                meta[str(r['image_id'])] = {'file': os.path.basename(f), 'row_group': rg, 'row': k, 'W': W, 'H': H, 'rules': rules,
                    'camera_distance': r.get('camera_distance'), 'illumination': r.get('illumination'), 'view': r.get('view'), 'quality_of_info': r.get('quality_of_info')}
            row0 += len(t)
    write_json(META_P, meta); return meta
_META = None
def meta():
    global _META
    if _META is None: _META = read_json(META_P) or build_meta()
    return _META
def cs_labels(i):
    """Fall = rule 2 or 3, PPE = rule 1, rule 4 not scored. Returns dict."""
    r = meta()[i]['rules']; fall = r['2'] is not None or r['3'] is not None; ppe = r['1'] is not None
    return {'Fall_Hazard': fall, 'PPE_Violation': ppe, 'violation': fall or ppe, 'rule4': r['4'] is not None}
def cs_boxes(i):
    """True boxes in pixels, xyxy, per scored category."""
    m = meta()[i]; W, H = m['W'], m['H']; out = {'Fall_Hazard': [], 'PPE_Violation': []}
    for j, c in (('1', 'PPE_Violation'), ('2', 'Fall_Hazard'), ('3', 'Fall_Hazard')):
        v = m['rules'][j]
        for b in (v['boxes'] if v else []):
            if len(b) == 4: out[c].append([b[0] * W, b[1] * H, b[2] * W, b[3] * H])
    return out
def largest_scored_share(i):
    m = meta()[i]; best = 0.0
    for j in ('1', '2', '3'):
        v = m['rules'][j]
        for b in (v['boxes'] if v else []):
            if len(b) == 4: best = max(best, max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1]))
    return best
def Ycs(ids, cats=CATS2): return np.array([[cs_labels(i)[c] for c in cats] for i in ids])

def prepare_cs(ids):
    """Encodes the needed images once: parquet image -> RGB -> JPEG quality 95 (Pillow)."""
    import pyarrow.parquet as pq
    os.makedirs(os.path.join(G, 'tools', 'cs10k_q95'), exist_ok=True); M = meta()
    need = [i for i in ids if not os.path.exists(os.path.join(G, 'tools', 'cs10k_q95', '%s.q95.jpg' % i))]
    byrg = collections.defaultdict(list)
    for i in need: byrg[(M[i]['file'], M[i]['row_group'])].append(i)
    for (f, rg), lst in sorted(byrg.items()):
        t = pq.ParquetFile(os.path.join(DCS, 'train', f)).read_row_group(rg, columns=['image_id', 'image']).to_pylist(); want = set(lst)
        for r in t:
            if str(r['image_id']) in want:
                im = r['image']; b = im['bytes'] if isinstance(im, dict) else im; buf = io.BytesIO()
                Image.open(io.BytesIO(b)).convert('RGB').save(buf, format='JPEG', quality=95)
                p = os.path.join(G, 'tools', 'cs10k_q95', '%s.q95.jpg' % r['image_id']); open(p + '.tmp', 'wb').write(buf.getvalue()); os.replace(p + '.tmp', p)
    return len(need)
def list_ids(name, mode=None):
    """Image IDs of lists/<name>.json for the current mode (pilot uses its own lists)."""
    d = read_json((mode or MODE).path('lists', name + '.json')); return d['ids']
def cs_groups(ids):
    """Near-copy groups within a set (experiment 6). Every other image is its own group."""
    pairs = read_json(os.path.join(G, 'results', 'e06_near_copy_pairs.json'), {'pairs': []})['pairs']
    idx = {i: k for k, i in enumerate(ids)}; par = list(range(len(ids)))
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for a, b, _ in pairs:
        if a in idx and b in idx: par[find(idx[a])] = find(idx[b])
    return np.array([find(k) for k in range(len(ids))])
