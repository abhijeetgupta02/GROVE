"""Experiment 4 and Part 4 records: ollama list with full digests, ollama show per model (family, parameters, quantization, license, source)."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grove_common import *
set_mode('main'); import grove_calls as gcl
EXPECT = {'clef:27b': '039c167bd0ec', 'clef-flash:9b': '0a2a05d6a581', 'pplx-decider:27b': '733585a9ebb6', 'd3:9b': None, 'd3:27b': '66f8405a50c4', 'qwen3.5:9b': '6488c96fa5fa',
          'qwen3.5:27b': None, 'gemma4:31b': None, 'mistral-small3.2:24b': '5a408ab55df5', 'ministral-3:14b': '4760c35aeb9d', 'qwen3-vl:32b': 'ff2e46876908'}
tags = {x['name']: x for x in gcl.http_json('/api/tags', timeout=60)['models']}
lst = subprocess.run([OLLAMA_EXE, 'list'], capture_output=True, text=True).stdout
L = ['ollama list (frozen Ollama %s, %s)' % (OLLAMA_VERSION, now()), '', lst, '', 'Run models: tag | ID (first 12) | expected | match | size bytes | full digest']
for m, e in EXPECT.items():
    t = tags.get(m, {}); d = t.get('digest', ''); L.append('%s | %s | %s | %s | %s | %s' % (m, d[:12], e or '(none recorded)', ('MATCH' if d[:12] == e else 'DIFFERS') if e else 'n/a', t.get('size'), d))
write_text(MODE.path('freeze', 'models.txt'), '\n'.join(L) + '\n')
R = ['# Experiment 4. What each model is built on', '', 'From `POST /api/show` on the frozen Ollama %s (%s). Fields as reported by each model package; "-" means not shown. Each needs a citable source before submission (open item).' % (OLLAMA_VERSION, now()), '',
     '| Tag | ID | Family | Families | Parameter size | Quantization | Format | Architecture (model_info) | Base model / FROM | License (first line) |', '|---|---|---|---|---|---|---|---|---|---|']
raw = {}
for m in EXPECT:
    try: s = gcl.http_json('/api/show', {'model': m}, timeout=120)
    except Exception as ex: R.append('| %s | - | error %s |' % (m, ex)); continue
    raw[m] = {k: s.get(k) for k in ('details', 'modelfile', 'license', 'model_info', 'capabilities', 'parameters', 'template')}
    det = s.get('details') or {}; mi = s.get('model_info') or {}
    frm = [l for l in (s.get('modelfile') or '').splitlines() if l.startswith('FROM ')]; base = mi.get('general.basename') or mi.get('general.base_model.0.name') or ''
    lic = ((s.get('license') or '').strip().splitlines() or ['-'])[0][:80]
    R.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (m, tags.get(m, {}).get('digest', '')[:12], det.get('family', '-'), ', '.join(det.get('families') or []) or '-', det.get('parameter_size', '-'), det.get('quantization_level', '-'),
             det.get('format', '-'), mi.get('general.architecture', '-'), (base + ' ' + (frm[0][5:60] if frm else '')).strip() or '-', lic.replace('|', '/')))
R += ['', 'Capabilities per model: ' + '; '.join('%s: %s' % (m, ','.join(v.get('capabilities') or [])) for m, v in raw.items())]
write_text(MODE.path('reports', 'model_details.md'), '\n'.join(R) + '\n'); write_json(MODE.path('results', 'e04_ollama_show.json'), raw); print('\n'.join(L)); print('\n'.join(R))
