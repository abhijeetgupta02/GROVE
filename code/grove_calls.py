"""Ollama client and resumable jobs (one line per image, terminal/non-terminal, config_hash). Section 14 Part 7 running rules."""
import base64, http.client, json, os, re, socket, subprocess, time, urllib.error, urllib.request
from PIL import Image
from grove_common import *
import grove_common as gc

class OllamaDown(Exception): pass
class CallError(Exception): pass
DETACHED = 0x00000008 | 0x00000200 | 0x08000000

def http_json(path, body=None, timeout=60):
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(HOST + path, data=data, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ollama'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raise CallError('HTTP %s: %s' % (e.code, e.read().decode('utf-8', 'ignore')[:600]))
    except (urllib.error.URLError, ConnectionError, socket.timeout, TimeoutError, http.client.HTTPException, OSError) as e:
        raise OllamaDown('%s: %s' % (type(e).__name__, e))

def serving_version():
    try: return http_json('/api/version', timeout=15).get('version')
    except Exception: return None
def _ps(cmd, timeout=60):
    return subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', cmd], capture_output=True, text=True, timeout=timeout).stdout.strip()
def listener():
    # A listening socket has remote port 0. On this PC Windows can report it as 'Closed' instead of 'Listen', so the state is not used.
    out = _ps("$c = Get-NetTCPConnection -LocalPort 11434 -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 -and $_.RemotePort -eq 0 } | Select-Object -First 1; if ($c) { $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue; '{0}|{1}' -f $c.OwningProcess, $p.Path }")
    if '|' not in out: return None, None
    pid, path = out.split('|', 1); return int(pid), path.strip()
def stop_other_ollama(pid):
    subprocess.run(['taskkill', '/IM', 'ollama app.exe', '/F'], capture_output=True)
    if pid: subprocess.run(['taskkill', '/PID', str(pid), '/F', '/T'], capture_output=True)
    time.sleep(5)
def start_ollama():
    env = dict(os.environ); env.update(ENV); env.pop('OLLAMA_HOST', None)
    f = open(MODE.path('logs', 'ollama_serve.log'), 'ab')
    subprocess.Popen([OLLAMA_EXE, 'serve'], cwd=os.path.dirname(OLLAMA_EXE), env=env, stdout=f, stderr=f, creationflags=DETACHED, close_fds=True)
    log('started frozen Ollama: ' + OLLAMA_EXE)
def ensure_ollama(max_wait=900):
    """The frozen 0.40.14 binary must be the one listening on 11434. Anything else (the desktop app) is stopped."""
    t0 = time.time(); restarted = False
    while True:
        v = serving_version(); pid, path = listener()
        if v == OLLAMA_VERSION and path and os.path.normcase(path) == os.path.normcase(OLLAMA_EXE): return True
        if pid and (not path or os.path.normcase(path) != os.path.normcase(OLLAMA_EXE) or v is None):
            log('port 11434 held by pid %s (%s, version %s); stopping it' % (pid, path, v)); stop_other_ollama(pid)
        elif pid is None and not restarted:
            start_ollama(); restarted = True
        elif pid is None and time.time() - t0 > 60 and v is None:
            start_ollama(); t0 = time.time()
        heartbeat(); time.sleep(10)
        if time.time() - t0 > max_wait:
            STATUS['note'] = 'Ollama not responding; still trying'; log('Ollama not ready after %d s; continuing to wait' % max_wait); t0 = time.time(); restarted = False

_DIG = {}
def model_digest(m):
    if m not in _DIG:
        for x in http_json('/api/tags', timeout=60).get('models', []): _DIG[x['name']] = x.get('digest')
    return _DIG.get(m)
def loaded_models():
    try: return [x['name'] for x in http_json('/api/ps', timeout=30).get('models', [])]
    except Exception: return []
def unload_all():
    for _ in range(15):
        ms = loaded_models()
        if not ms: return True
        for m in ms:
            try: http_json('/api/generate', {'model': m, 'keep_alive': 0}, timeout=120)
            except Exception: pass
        time.sleep(3)
    log('WARNING: /api/ps not empty after unloading: %s' % loaded_models()); return False

FLAGS_P = lambda: MODE.path('results', 'model_flags.json')
def flags(m): return (read_json(FLAGS_P(), {}) or {}).get(m, {})
def set_flag(m, k, v):
    d = read_json(FLAGS_P(), {}) or {}; d.setdefault(m, {})[k] = v; write_json(FLAGS_P(), d); log('model flag %s %s=%s' % (m, k, v))

# ---------------------------------------------------------------- images
CS_CACHE = os.path.join(G, 'tools', 'cs10k_q95')
def load_203(name):
    p = os.path.join(PK, 'data', 'grove203', 'encoded_q95', name + '.q95.jpg'); b = open(p, 'rb').read()
    w, h = Image.open(p).size; return {'b64': base64.b64encode(b).decode(), 'W': w, 'H': h, 'sha': sha256_bytes(b)}
def load_cs(image_id):
    p = os.path.join(CS_CACHE, '%s.q95.jpg' % image_id); b = open(p, 'rb').read()
    w, h = Image.open(p).size; return {'b64': base64.b64encode(b).decode(), 'W': w, 'H': h, 'sha': sha256_bytes(b)}
def item(name, kind, category=None):
    """kind '203' or 'cs'. key = name, or name|category for phrase items."""
    return {'key': name if category is None else '%s|%s' % (name, category), 'image_name': name, 'category': category, 'src': kind}
def load_item(it): return load_203(it['image_name']) if it['src'] == '203' else load_cs(it['image_name'])

# ---------------------------------------------------------------- the three call types
def _num(v): return isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 1
def call_decision(model, setname, img, it):
    S = SETS[setname]; qs = {k: {'type': 'noul', 'instructions': v} for k, v in S['questions'].items()}
    r = http_json('/v1/systemone', {'model': model, 'state': S['state'], 'images': [img['b64']], 'keep_alive': '15m', 'questions': qs}, timeout=TIMEOUT)
    ans = r.get('answers') or {}; probs = {k: (ans.get(k) or {}).get('noul') for k in qs}
    st = 'valid' if all(_num(v) for v in probs.values()) else 'parse_failure'
    return st, {'probs': probs, 'usage': r.get('usage')}, None
def _box(b, W, H):
    if isinstance(b, list) and len(b) == 4 and all(isinstance(v, int) and not isinstance(v, bool) for v in b):
        x1, y1, x2, y2 = b
        if 0 <= x1 < x2 <= W and 0 <= y1 < y2 <= H: return b
    return None
def _valid_sp(p):
    if not isinstance(p, dict): return False
    for c in CATS3:
        d = p.get(c)
        if not isinstance(d, dict) or not isinstance(d.get('present'), bool) or not isinstance(d.get('evidence'), str): return False
        if not isinstance(d.get('bbox'), list) or not all(isinstance(v, int) and not isinstance(v, bool) for v in d['bbox']): return False
    return True
def _chat(model, content, img, options, fmt=None):
    f = flags(model)
    body = {'model': model, 'messages': [{'role': 'user', 'content': content, 'images': [img['b64']]}], 'stream': False, 'keep_alive': '15m', 'options': options}
    if not f.get('no_think'): body['think'] = False
    if fmt is not None: body['format'] = SP_SCHEMA_INLINE if f.get('schema_inline') else fmt
    try: return http_json('/api/chat', body, timeout=TIMEOUT)
    except CallError as e:
        s = str(e).lower()
        if 'think' in s and not f.get('no_think'): set_flag(model, 'no_think', True); return _chat(model, content, img, options, fmt)
        if fmt is not None and ('$ref' in s or 'ref' in s or 'schema' in s or 'format' in s) and not f.get('schema_inline'):
            set_flag(model, 'schema_inline', True); return _chat(model, content, img, options, fmt)
        raise
def call_sp(model, setname, img, it):
    P = SP_PROMPT.format(W=img['W'], H=img['H']) + ('\n/nothink' if model.startswith('qwen') else '')
    steps = []
    for n in SP_PREDICT_LADDER:
        r = _chat(model, P, img, dict(SP_OPTIONS, num_predict=n), SP_SCHEMA); dr = r.get('done_reason')
        steps.append({'num_predict': n, 'done_reason': dr, 'eval_count': r.get('eval_count')})
        if dr != 'length': break
    content = (r.get('message') or {}).get('content', '')
    out = {'content': content, 'steps': steps, 'think_sent': not flags(model).get('no_think'), 'schema': 'inline' if flags(model).get('schema_inline') else 'ref'}
    if dr == 'length': return 'cut_off', out, dr
    try: p = json.loads(content)
    except ValueError: return 'parse_failure', out, dr
    if dr != 'stop' or not _valid_sp(p): return 'parse_failure', out, dr
    out['parsed'] = p; out['boxes'] = {c: _box(p[c]['bbox'], img['W'], img['H']) for c in CATS3}
    return 'valid', out, dr
def clean_phrase(t):
    t = (t or '').strip().strip('"\'`').strip().rstrip('.').strip().strip('"\'`').strip()
    return 'NONE' if t.upper() in ('NONE', 'NONE.') else t
def call_phrase(model, setname, img, it):
    P = PHRASE_PROMPT.format(C=CAT_DISPLAY[it['category']]) + ('\n/nothink' if model.startswith('qwen') else '')
    r = _chat(model, P, img, PHRASE_OPTIONS); dr = r.get('done_reason'); txt = (r.get('message') or {}).get('content', '')
    out = {'content': txt, 'phrase': clean_phrase(txt)}
    if dr == 'length': return 'cut_off', out, dr
    if dr != 'stop' or not out['phrase']: return 'parse_failure', out, dr
    return 'valid', out, dr
CALL = {'decision': call_decision, 'sp': call_sp, 'phrase': call_phrase}

# ---------------------------------------------------------------- jobs
def safe(m): return m.replace(':', '_').replace('/', '_')
def job_path(exp, model, setname): return MODE.path('runs', exp, '%s__%s.jsonl' % (safe(model), setname))
def fail_marker(exp, model, setname): return MODE.path('runs', exp, '%s__%s.model_failed.json' % (safe(model), setname))
_NUM_CTX = {}
def model_num_ctx(model):
    """The decision endpoint takes its context from the model's own num_ctx parameter (request options and OLLAMA_CONTEXT_LENGTH are ignored)."""
    if model not in _NUM_CTX:
        try:
            m = re.search(r'num_ctx\s+(\d+)', http_json('/api/show', {'model': model}, timeout=60).get('parameters') or '')
            _NUM_CTX[model] = int(m.group(1)) if m else None
        except Exception: return None
    return _NUM_CTX[model]
def job_config(kind, model, setname, src):
    enc = ENC_203 if src == '203' else enc_cs10k()
    base = {'kind': kind, 'model': model, 'model_digest': model_digest(model), 'set': setname, 'image_encoding': enc}
    if kind in ('decision', 'phrase'): base['pause_seconds_before_each_call'] = PAUSE_SECONDS.get(kind, 0.0)  # decision and phrase calls only; 0 since 2026-11-06 (D22), so lines written with the 7 s pause do not match
    if kind == 'decision':
        S = SETS[setname]; base.update({'endpoint': '/v1/systemone', 'state': S['state'], 'questions': S['questions'], 'answer_type': 'noul'})
        base['context_size'] = model_num_ctx(model)  # the model's own num_ctx, part of config_hash
    elif kind == 'sp':
        base.update({'endpoint': '/api/chat', 'prompt': SP_PROMPT, 'nothink_suffix': model.startswith('qwen'), 'schema': SP_SCHEMA, 'options': SP_OPTIONS,
                     'num_predict_ladder': SP_PREDICT_LADDER, 'think': 'false, removed if rejected', 'schema_policy': '$ref, inline if rejected'})
        base['context_size'] = SP_OPTIONS['num_ctx']
    else:
        base.update({'endpoint': '/api/chat', 'prompt': PHRASE_PROMPT, 'category_names': CAT_DISPLAY, 'nothink_suffix': model.startswith('qwen'),
                     'options': PHRASE_OPTIONS, 'think': 'false, removed if rejected'})
    return base
def config_hash(cfg): return sha256_text(json.dumps(cfg, sort_keys=True, ensure_ascii=False))

def read_job(path, h):
    term, prev, other = {}, {}, 0
    for d in read_jsonl(path):
        if d.get('config_hash') != h: other += 1; continue
        k = d.get('key', d.get('image_name'))
        if d.get('terminal'): term[k] = d
        else: prev[k] = d.get('attempts', [])
    return term, prev, other

def _attempt(kind, model, setname, it, h, pass_no, prev):
    attempts = list(prev); status, output, dr, sec, outage = 'call_failure', None, None, 0.0, False
    img = load_item(it); pause = PAUSE_SECONDS.get(kind, 0.0)
    delays = [0] + RETRY_DELAYS; step = 0; quick_used = False; tries = 0; quick = False
    while True:
        delay = 0 if quick else delays[step]
        if delay:
            for _ in range(int(delay)): time.sleep(1)
            heartbeat()
        if pause:
            time.sleep(pause); heartbeat()  # the pause is not part of the call time
        t0 = time.time(); err = None; outage = False; tries += 1
        try: status, output, dr = CALL[kind](model, setname, img, it)
        except OllamaDown as e:
            status, err = 'call_failure', str(e)[:500]
            if serving_version() is None: outage = True; log('Ollama down during %s %s: %s' % (model, it['key'], err)); ensure_ollama()
        except CallError as e: status, err = 'call_failure', str(e)[:500]
        except Exception as e: status, err = 'call_failure', ('%s: %s' % (type(e).__name__, e))[:500]
        sec = round(time.time() - t0, 3); heartbeat()
        a = {'pass': pass_no, 'try': tries, 'status': status, 'seconds': sec, 'done_reason': dr, 'error': err, 'outage': outage, 'at': now()}
        if quick: a['immediate_retry'] = True
        attempts.append(a)
        if status != 'call_failure' or outage: break
        if kind == 'decision' and not quick_used and err and err.startswith('HTTP 500') and QUICK_RETRY_TEXT in err:
            quick_used = True; quick = True; continue  # one retry at once (only the pause before it)
        quick = False; step += 1
        if step >= len(delays): break
    rec = {'image_name': it['image_name'], 'key': it['key'], 'category': it.get('category'), 'model': model, 'set': setname, 'config_hash': h,
           'status': status, 'terminal': None, 'attempts': attempts, 'output': output, 'seconds': sec, 'done_reason': dr, 'timestamp': now(), 'image_sha256': img['sha']}
    return rec, outage

def run_job(exp, kind, model, setname, items, label=None):
    """Runs one model over items. Returns dict(valid, failed, total, model_failed). Resumes: skips terminal lines with this config_hash."""
    wait_for_disk(); ensure_ollama()
    path = job_path(exp, model, setname); os.makedirs(os.path.dirname(path), exist_ok=True)
    if model_digest(model) is None:
        write_json(fail_marker(exp, model, setname), {'reason': 'model not installed', 'at': now()}); log('model %s not installed: marked failed' % model)
        return {'valid': 0, 'failed': len(items), 'total': len(items), 'model_failed': True}
    cfg = job_config(kind, model, setname, items[0]['src'] if items else '203'); h = config_hash(cfg)
    write_json(path[:-6] + '.config.json', {'config_hash': h, 'config': cfg})
    term, prev, other = read_job(path, h)
    if other: log('%s: %d lines with another config_hash ignored' % (os.path.basename(path), other))
    todo = [it for it in items if it['key'] not in term]
    STATUS.update({'experiment': exp, 'model': model, 'done': len(items) - len(todo), 'total': len(items), 'recent': []})
    if todo:
        log('job %s %s %s: %d to do of %d' % (exp, model, setname, len(todo), len(items)) + ('; pause %.0f s before each call (not counted in seconds)' % PAUSE_SECONDS[kind] if PAUSE_SECONDS.get(kind, 0.0) else '; no pause'))
        if any(m != model for m in loaded_models()): unload_all()
        n_valid_job = 0; consec = 0
        while todo:
            for pass_no in (1, 2):
                nxt = []
                for it in todo:
                    wait_for_disk()
                    rec, outage = _attempt(kind, model, setname, it, h, pass_no, prev.get(it['key'], []))
                    rec['terminal'] = (rec['status'] == 'valid') or (pass_no == 2 and not outage)
                    append_jsonl(path, rec); prev[it['key']] = rec['attempts']
                    if rec['terminal']: term[it['key']] = rec
                    else: nxt.append(it)
                    if rec['terminal'] and rec['status'] != 'valid': STATUS['failures'] += 1
                    n_valid_job += rec['status'] == 'valid'
                    STATUS['done'] = len(term); STATUS['recent'].append(rec['seconds'])
                    consec = consec + 1 if (rec['status'] == 'call_failure' and not outage) else 0
                    if pass_no == 1 and consec >= 3 and n_valid_job == 0:
                        err = rec['attempts'][-1].get('error')
                        write_json(fail_marker(exp, model, setname), {'reason': 'first 3 images failed every attempt', 'last_error': err, 'at': now()})
                        log('MODEL FAILED %s %s %s: %s' % (exp, model, setname, err)); unload_all()
                        return {'valid': 0, 'failed': len(items), 'total': len(items), 'model_failed': True}
                todo = nxt
                if not todo: break
            if todo:
                STATUS['note'] = 'waiting for Ollama to recover (%d images pending)' % len(todo); log(STATUS['note']); time.sleep(60); ensure_ollama()
        STATUS['note'] = ''
    unload_all()
    if os.path.exists(fail_marker(exp, model, setname)) and any(d['status'] == 'valid' for d in term.values()):
        os.replace(fail_marker(exp, model, setname), fail_marker(exp, model, setname) + '.cleared')
    v = sum(1 for k in (it['key'] for it in items) if k in term and term[k]['status'] == 'valid')
    return {'valid': v, 'failed': len(items) - v, 'total': len(items), 'model_failed': False}

def model_failed(exp, model, setname): return os.path.exists(fail_marker(exp, model, setname))
def run_frozen_job(exp, kind, model, setname, items, comparison):
    """Frozen model: retry every 30 minutes for up to 12 hours, then mark the comparison incomplete."""
    t0 = time.time()
    while True:
        r = run_job(exp, kind, model, setname, items)
        if not r['model_failed']: return r
        if time.time() - t0 > 12 * 3600:
            write_json(MODE.path('results', 'incomplete_%s.json' % comparison), {'model': model, 'exp': exp, 'set': setname, 'at': now()})
            log('COMPARISON INCOMPLETE: %s (%s failed for 12 hours)' % (comparison, model)); return r
        STATUS['note'] = 'frozen model %s failing; retry in 30 minutes' % model; log(STATUS['note'])
        os.replace(fail_marker(exp, model, setname), fail_marker(exp, model, setname) + '.%d' % int(time.time()))
        for _ in range(1800): time.sleep(1); (_ % 60 == 0) and heartbeat()

def load_results(exp, model, setname, keys=None):
    """Terminal lines with the current config_hash (from the saved config). Returns key -> line."""
    path = job_path(exp, model, setname); cp = path[:-6] + '.config.json'
    if not os.path.exists(cp): return {}
    h = read_json(cp)['config_hash']; term, _, _ = read_job(path, h)
    return term if keys is None else {k: v for k, v in term.items() if k in keys}
