#!/usr/bin/env python
"""Do this PC and the Mac give the same scores on 5 images? Loads one model at a time. Writes logs/check_match.json. --dry-run only checks files."""
import base64, json, os, sys, urllib.request
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); HOST = 'http://127.0.0.1:11434'
NAMES = ['1.jpg', '38.jpeg', '113.jpg', '149.jpeg', '171.png']
CHECKS = [('clef:27b', 'h', 'clef_27b__h.jsonl'), ('clef-flash:9b', 'S0', 'clef-flash_9b__S0.jsonl'), ('pplx-decider:27b', 'h', 'pplx-decider_27b__h.jsonl')]
P = json.load(open(R + '/prompts/prompts.json', encoding='utf-8'))
def ref(f):
    out = {}
    for l in open(R + '/reference_mac/' + f, encoding='utf-8'):
        d = json.loads(l); out[d['image_name']] = d['probs']
    return out
def img(n): return open(R + '/data/grove203/encoded_q95/' + n + '.q95.jpg', 'rb').read()
def post(path, body, timeout=900):
    q = urllib.request.Request(HOST + path, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ollama'})
    return json.load(urllib.request.urlopen(q, timeout=timeout))
if '--dry-run' in sys.argv:
    for m, s, f in CHECKS:
        r = ref(f); assert all(n in r for n in NAMES) and set(P[s]['questions']) <= set(r[NAMES[0]]), f
        print('ok', m, s, len(r), 'rows', sum(len(img(n)) for n in NAMES), 'image bytes')
    sys.exit(0)
print('Ollama', json.load(urllib.request.urlopen(HOST + '/api/version'))); res = []; worst = 0.0
for m, s, f in CHECKS:
    r = ref(f); qs = {k: {'type': 'noul', 'instructions': v} for k, v in P[s]['questions'].items()}
    for n in NAMES:
        a = post('/v1/systemone', {'model': m, 'state': P[s]['state'], 'images': [base64.b64encode(img(n)).decode()], 'keep_alive': '5m', 'questions': qs})['answers']
        d = max(abs(a[k]['noul'] - r[n][k]) for k in qs); worst = max(worst, d); res.append({'model': m, 'set': s, 'image': n, 'max_abs_diff': d}); print(m, s, n, 'max difference %.2e' % d, flush=True)
    post('/api/generate', {'model': m, 'keep_alive': 0})
os.makedirs(R + '/logs', exist_ok=True); json.dump({'worst': worst, 'rows': res}, open(R + '/logs/check_match.json', 'w'), indent=1)
print('RESULT', 'EXACT MATCH' if worst == 0 else ('CLOSE' if worst < 1e-3 else 'DIFFERENT'), 'worst difference %.2e' % worst)
