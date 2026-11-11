"""Stage A, labels only: experiments 5, 6, 7 (Section 14 Part 7). Usage: stage_a.py e05 | e06 | e06_confirm CUTOFF NOTE | e07"""
import collections, io, json, os, random, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grove_common import *
import grove_data as gd
M = set_mode('main')

def e05():
    meta = gd.meta(); sp = gd.splits(); rows = []; js = {}
    for name in ('tuning_sample', 'validation', 'tuning_rest'):
        ids = [str(i) for i in sp[name]]; miss = [i for i in ids if i not in meta]
        c = collections.Counter(); nb = collections.Counter(); sh = []
        for i in ids:
            if i not in meta: continue
            r = meta[i]['rules']
            for j in '1234':
                if r[j] is not None: c['rule %s' % j] += 1; nb['rule %s boxes' % j] += len(r[j]['boxes'])
            v = any(r[j] is not None for j in '123'); c['violation (rule 1, 2 or 3)'] += v; c['no rule 1-3'] += not v
            c['rule 4 only'] += (not v) and r['4'] is not None; c['no rule at all'] += all(r[j] is None for j in '1234')
            if v: sh.append(gd.largest_scored_share(i))
        q = np.percentile(sh, [0, 10, 50, 90, 100]).tolist() if sh else []
        js[name] = {'images': len(ids), 'missing_from_parquet': len(miss), 'counts': dict(c), 'boxes': dict(nb), 'largest_scored_box_share_percentiles_0_10_50_90_100': q,
                    'natural_violation_rate': c['violation (rule 1, 2 or 3)'] / max(len(ids) - len(miss), 1)}
    allb = [b for m in meta.values() for j in '1234' if m['rules'][j] for b in m['rules'][j]['boxes']]
    fmt = {'boxes_total': len(allb), 'all_length_4': all(len(b) == 4 for b in allb), 'min_value': min(min(b) for b in allb), 'max_value': max(max(b) for b in allb),
           'x1<x2 and y1<y2 share': float(np.mean([b[0] < b[2] and b[1] < b[3] for b in allb]))}
    js['bounding_box_format'] = fmt; js['parquet_rows'] = len(meta); write_json(M.path('results', 'e05_label_audit.json'), js)
    L = ['# Experiment 5. ConstructionSite10k label audit (labels only, no model calls)', '', 'Generated %s from `packet\\data\\constructionsite10k\\train` (%d rows) and `splits\\train_splits.json` (seed %s).' % (now(), len(meta), sp.get('seed')), '',
         '## Box format', '', '`rule_k_violation` is null when the rule is not violated, otherwise `{bounding_box, reason}`. `bounding_box` is a list of boxes, each `[x1, y1, x2, y2]` as fractions of image width and height (%d boxes; all of length 4: %s; values %.2f to %.2f; x1<x2 and y1<y2 in %.1f%%). Parsed as normalized xyxy and multiplied by the decoded image size.' % (fmt['boxes_total'], fmt['all_length_4'], fmt['min_value'], fmt['max_value'], 100 * fmt['x1<x2 and y1<y2 share']), '',
         '## Counts per split', '', '| Split | Images | Rule 1 | Rule 2 | Rule 3 | Rule 4 | Violation (1-3) | No rule 1-3 | Rule 4 only | Natural violation rate |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for n in ('tuning_sample', 'validation', 'tuning_rest'):
        c = js[n]['counts']; L.append('| %s | %d | %d | %d | %d | %d | %d | %d | %d | %.4f |' % (n, js[n]['images'], c.get('rule 1', 0), c.get('rule 2', 0), c.get('rule 3', 0), c.get('rule 4', 0), c.get('violation (rule 1, 2 or 3)', 0), c.get('no rule 1-3', 0), c.get('rule 4 only', 0), js[n]['natural_violation_rate']))
    L += ['', '## Largest scored box (rules 1-3) as a share of image area, violation images', '', '| Split | min | 10th pct | median | 90th pct | max |', '|---|---:|---:|---:|---:|---:|']
    for n in ('tuning_sample', 'validation', 'tuning_rest'):
        q = js[n]['largest_scored_box_share_percentiles_0_10_50_90_100']; L.append('| %s | %s |' % (n, ' | '.join('%.4f' % x for x in q)))
    L += ['', 'Mapping (Section 6.2): rule 1 = PPE_Violation; rules 2 and 3 = Fall_Hazard; rule 4 not scored. No Electrical label exists in this dataset.']
    write_text(M.path('reports', 'label_audit.md'), '\n'.join(L) + '\n'); print('\n'.join(L))

def dhash(im):
    g = im.convert('L').resize((17, 16), Image.Resampling.LANCZOS); a = np.asarray(g, dtype=np.int16)
    return np.packbits((a[:, 1:] > a[:, :-1]).flatten())   # 256 bits -> 32 bytes
def e06():
    import pyarrow.parquet as pq
    d = gd.g203(); H = {}; src = {}
    for n in d['names']: H[n] = dhash(Image.open(os.path.join(gd.D203, 'encoded_q95', n + '.q95.jpg'))); src[n] = '203'
    for f in gd.parquet_files():
        pf = pq.ParquetFile(f)
        for rg in range(pf.num_row_groups):
            for r in pf.read_row_group(rg, columns=['image_id', 'image']).to_pylist():
                b = r['image']['bytes']; H[str(r['image_id'])] = dhash(Image.open(io.BytesIO(b))); src[str(r['image_id'])] = 'cs10k'
    keys = list(H); X = np.stack([H[k] for k in keys]).view(np.uint64)   # N x 4
    N = len(keys); best = []; pairs = []
    for s in range(0, N, 400):
        D = np.bitwise_count(X[s:s + 400, None, :] ^ X[None, :, :]).sum(2)
        for i in range(D.shape[0]):
            a = s + i; row = D[i, a + 1:]
            for j in np.where(row <= 90)[0]: best.append((int(row[j]), keys[a], keys[a + 1 + j]))
    best.sort(); write_json(M.path('results', 'e06_hashes_close_pairs.json'), {'note': 'all pairs at 90 bits or fewer', 'pairs': [[a, b, dd] for dd, a, b in best]})
    k63, k79 = [n for n in d['names'] if gd.fnum(n) == 63][0], [n for n in d['names'] if gd.fnum(n) == 79][0]
    d6379 = int(np.bitwise_count(H[k63].view(np.uint64) ^ H[k79].view(np.uint64)).sum())
    cross = [(dd, a, b) for dd, a, b in best if src[a] != src[b]]; within = [(dd, a, b) for dd, a, b in best if src[a] == src[b] == 'cs10k']
    def sheet(lst, title, path):
        W = 2 * 260 + 30; Hh = 40 + 200 * len(lst); im = Image.new('RGB', (W, max(Hh, 60)), 'white'); dr = ImageDraw.Draw(im); dr.text((10, 10), title, fill='black')
        for k, (dd, a, b) in enumerate(lst):
            for c, key in enumerate((a, b)):
                p = os.path.join(gd.D203, 'encoded_q95', key + '.q95.jpg') if src[key] == '203' else None
                if p: x = Image.open(p).convert('RGB')
                else:
                    m = gd.meta()[key]; t = pq.ParquetFile(os.path.join(gd.DCS, 'train', m['file'])).read_row_group(m['row_group'], columns=['image_id', 'image']).to_pylist()
                    x = Image.open(io.BytesIO([r for r in t if str(r['image_id']) == key][0]['image']['bytes'])).convert('RGB')
                x.thumbnail((250, 170)); im.paste(x, (10 + c * 270, 40 + k * 200))
            dr.text((10, 40 + k * 200 + 175), '%d bits: %s (%s) vs %s (%s)' % (dd, a, src[a], b, src[b]), fill='black')
        im.save(path)
    cut = 60
    sheet([x for x in cross if x[0] <= cut][-20:], 'Cross-dataset pairs at or below 60 bits (closest to the cutoff)', M.path('reports', 'scene_check_cross_below.png'))
    sheet([x for x in cross if x[0] > cut][:20], 'Cross-dataset pairs above 60 bits (closest to the cutoff)', M.path('reports', 'scene_check_cross_above.png'))
    sheet([x for x in within if x[0] <= cut][-20:], 'ConstructionSite10k pairs at or below 60 bits (closest to the cutoff)', M.path('reports', 'scene_check_cs_below.png'))
    sheet([x for x in within if x[0] > cut][:20], 'ConstructionSite10k pairs above 60 bits (closest to the cutoff)', M.path('reports', 'scene_check_cs_above.png'))
    js = {'images_hashed': N, 'hash': 'difference hash, 16 x 16 = 256 bits, grayscale, Lanczos resize to 17 x 16', 'cutoff_bits': cut, 'files_63_79_distance': d6379,
          'pairs_at_or_below_cutoff': {'cross_dataset': sum(1 for x in cross if x[0] <= cut), 'within_cs10k': sum(1 for x in within if x[0] <= cut),
                                       'within_203': sum(1 for dd, a, b in best if src[a] == src[b] == '203' and dd <= cut)}}
    write_json(M.path('results', 'e06_draft.json'), js); print(json.dumps(js, indent=1))
def e06_confirm(cut, note):
    best = read_json(M.path('results', 'e06_hashes_close_pairs.json'))['pairs']; d = gd.g203(); n203 = set(d['names'])
    pairs = [p for p in best if p[2] <= cut]; js = read_json(M.path('results', 'e06_draft.json')); js['cutoff_bits'] = cut; js['visual_check'] = note
    js['pairs_at_or_below_cutoff_total'] = len(pairs); write_json(M.path('results', 'e06_near_copy_pairs.json'), {'cutoff_bits': cut, 'pairs': pairs}); write_json(M.path('results', 'e06_scene_check.json'), js)
    cs_near_203 = sorted({b if a in n203 else a for a, b, _ in pairs if (a in n203) != (b in n203)})
    L = ['# Experiment 6. Related scenes across all sets', '', 'Difference hash, 16 by 16 (256 bits), on the 203 images (encoded_q95 bytes) and all %d training images. Pairs at %d bits or fewer are near copies.' % (js['images_hashed'] - 203, cut), '',
         '- Files 63 and 79 (identical): distance %d bits -> %s.' % (js['files_63_79_distance'], 'match' if js['files_63_79_distance'] <= cut else 'NO MATCH'),
         '- Near-copy pairs: %d in total; across datasets %d; within ConstructionSite10k %d; within the 203 %d.' % (len(pairs), sum(1 for a, b, _ in pairs if (a in n203) != (b in n203)), sum(1 for a, b, _ in pairs if a not in n203 and b not in n203), sum(1 for a, b, _ in pairs if a in n203 and b in n203)),
         '- ConstructionSite10k images that are near copies of a 203 image (removed from candidates): %d %s' % (len(cs_near_203), cs_near_203[:50]), '',
         '## Cutoff validation (viewed before any model ran)', '', note, '',
         'Contact sheets: `scene_check_cross_below.png`, `scene_check_cross_above.png`, `scene_check_cs_below.png`, `scene_check_cs_above.png`.', '',
         'This catches near copies, not the same site photographed from another angle.']
    write_text(M.path('reports', 'scene_check.md'), '\n'.join(L) + '\n'); print('\n'.join(L))

def e07():
    meta = gd.meta(); sp = gd.splits(); pairs = read_json(M.path('results', 'e06_near_copy_pairs.json'))['pairs']; n203 = set(gd.g203()['names'])
    nb = collections.defaultdict(set)
    for a, b, _ in pairs: nb[a].add(b); nb[b].add(a)
    near203 = {k for k in nb if k not in n203 and nb[k] & n203}
    def viol(i): return any(meta[i]['rules'][j] is not None for j in '123')
    def draw(pool, k):
        pool = sorted(pool)
        return list(pool) if len(pool) <= k else random.Random(SEED).sample(pool, k)
    def build(main, rest, need, exclude):
        out, top = {}, {}
        for g, want in (('with', True), ('without', False)):
            p = [i for i in main if i not in exclude and viol(i) == want]; r = [i for i in rest if i not in exclude and viol(i) == want]
            got = draw(p, need); top[g] = max(0, need - len(got))
            if top[g]: got = got + draw(r, top[g])
            out[g] = got
        return out, top
    ts = [str(i) for i in sp['tuning_sample']]; va = [str(i) for i in sp['validation']]; tr = [str(i) for i in sp['tuning_rest']]
    cal, ctop = build(ts, tr, 250, near203); calset = set(cal['with'] + cal['without'])
    near_cal = {k for k in nb if nb[k] & calset}
    fin, ftop = build(va, [i for i in tr if i not in calset], 500, near203 | near_cal | calset); finset = set(fin['with'] + fin['without'])
    vis = float(np.percentile([gd.largest_scored_share(i) for i in tr if viol(i)], 10))
    r_val = np.mean([viol(i) for i in va]); r_ts = np.mean([viol(i) for i in ts])
    C = {'set': 'calibration', 'ids': sorted(calset), 'n': len(calset), 'n_with': len(cal['with']), 'n_without': len(cal['without']), 'top_up_from_tuning_rest': ctop, 'seed': SEED,
         'visibility_cutoff_largest_box_share': vis, 'reference_rate_r': float(r_ts), 'reference_pool': 'tuning_sample'}
    F = {'set': 'final', 'ids': sorted(finset), 'n': len(finset), 'n_with': len(fin['with']), 'n_without': len(fin['without']), 'top_up_from_tuning_rest': ftop, 'seed': SEED,
         'visibility_cutoff_largest_box_share': vis, 'reference_rate_r': float(r_val), 'reference_pool': 'validation'}
    for nm_, obj in (('calibration', C), ('final', F)):
        p = M.path('lists', nm_ + '.json')
        if os.path.exists(p): raise SystemExit('list exists, not overwriting: ' + p)
        write_json(p, obj)
    used = calset | finset; pool_p = [i for i in tr if i not in used and i not in near203 and not (nb.get(i, set()) & used)]
    pil = sorted(draw([i for i in pool_p if viol(i)], 5) + draw([i for i in pool_p if not viol(i)], 5))
    P = set_mode('pilot')
    for nm_ in ('calibration', 'final'): write_json(P.path('lists', nm_ + '.json'), {'set': 'pilot ' + nm_, 'ids': pil, 'n': len(pil), 'note': '10 tuning_rest images in neither list, used in place of both lists in the pilot', 'reference_rate_r': float(r_ts if nm_ == 'calibration' else r_val), 'visibility_cutoff_largest_box_share': vis})
    d = gd.g203(); Y = d['Y'](CATS3).any(1); pos = [n for n, y in zip(d['names'], Y) if y]; neg = [n for n, y in zip(d['names'], Y) if not y]
    sub = sorted(random.Random(SEED).sample(pos, 5) + random.Random(SEED).sample(neg, 5)); write_json(P.path('lists', 'g203_subset.json'), {'ids': sub})
    set_mode('main')
    hashes = {f: sha256_file(M.path('lists', f)) for f in ('calibration.json', 'final.json')}; write_json(M.path('lists', 'hashes.json'), hashes)
    print('calibration: %d (with %d, without %d), top-up %s' % (C['n'], C['n_with'], C['n_without'], ctop))
    print('final: %d images, top-up counts %s' % (F['n'], ftop)); print('natural violation rate: validation %.4f, tuning_sample %.4f' % (r_val, r_ts))
    print('visibility cutoff (10th percentile of largest scored box share, tuning_rest violation images): %.5f' % vis); print('list SHA-256:', hashes)
    print('pilot images:', pil, '| pilot 203 subset:', sub)
    n = gd.prepare_cs(sorted(calset | finset | set(pil))); print('encoded images written:', n)
    write_json(M.path('results', 'e07_lists.json'), {'calibration': {k: v for k, v in C.items() if k != 'ids'}, 'final': {k: v for k, v in F.items() if k != 'ids'}, 'hashes': hashes, 'pilot_ids': pil, 'pilot_203': sub, 'at': now()})
if __name__ == '__main__':
    a = sys.argv[1]
    if a == 'e05': e05()
    elif a == 'e06': e06()
    elif a == 'e06_confirm': e06_confirm(int(sys.argv[2]), sys.argv[3])
    elif a == 'e07': e07()
