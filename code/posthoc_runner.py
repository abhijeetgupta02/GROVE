"""POST HOC model runs after final scoring (owner's request of 2026-11-10, Part B; logs\\deviations.md D24).

Uses the run's own code path (grove_calls.run_job, _attempt, retries, second pass, outage handling), options (SP_OPTIONS, num_ctx 32768,
num_predict ladder), image encoding (tools\\cs10k_q95) and model flags, one model at a time, no pause. Writes only under runs_posthoc\\
and results_posthoc\\ (its own lock, status, log and graphics-memory peaks); reads freeze and lists; changes nothing else.

Jobs (plan in results_posthoc\\plan.json):
  p06_final  qwen3.5:27b  sp   final 1,000        step 6: second baseline, frozen single-pass prompt (same config as experiments 43 and 52)
  p07_cal    qwen3.5:27b  spc  calibration 500    step 7: frozen single-pass prompt and schema plus one integer "confidence" (0 to 100) per category
  p07_final  qwen3.5:27b  spc  final 1,000
  p07_cal    gemma4:31b   spc  calibration 500
  p07_final  gemma4:31b   spc  final 1,000
The confidence prompt and schema are saved once to freeze\\posthoc_confidence_prompt.txt (new file).
Usage: posthoc_runner.py
"""
import copy, json, os, sys, time, traceback
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grove_common as gc
G = gc.G
class PosthocMode(gc.Mode):
    def __init__(self):
        self.name = 'posthoc'; self.root = G
        for d, p in (('runs', os.path.join(G, 'runs_posthoc')), ('results', os.path.join(G, 'results_posthoc')), ('logs', os.path.join(G, 'results_posthoc', 'logs')),
                     ('reports', os.path.join(G, 'reports')), ('freeze', os.path.join(G, 'freeze')), ('lists', os.path.join(G, 'lists'))):
            setattr(self, d, p)
        for d in ('runs', 'results', 'logs'): os.makedirs(getattr(self, d), exist_ok=True)
        self.main_lists = os.path.join(G, 'lists'); self.main_reports = os.path.join(G, 'reports')
gc.MODE = PosthocMode()
from grove_common import *          # noqa: E402  (MODE is now the post hoc mode)
import grove_calls as gcl, grove_data as gd   # noqa: E402

# ---------------------------------------------------------------- step 7a: the confidence prompt and schema
CONF_LINE = 'confidence: how sure you are that this violation is present, 0 to 100.'
SPC_PROMPT = SP_PROMPT.replace('or [] if absent.\n', 'or [] if absent.\n' + CONF_LINE + '\n')
assert SPC_PROMPT != SP_PROMPT and SPC_PROMPT.count(CONF_LINE) == 1
_CC = copy.deepcopy(gc._C); _CC['required'] = _CC['required'] + ['confidence']; _CC['properties']['confidence'] = {'type': 'integer'}
SPC_SCHEMA = {'type': 'object', 'required': CATS3, 'properties': {c: {'$ref': '#/$defs/c'} for c in CATS3}, '$defs': {'c': _CC}}
SPC_SCHEMA_INLINE = {'type': 'object', 'required': CATS3, 'properties': {c: _CC for c in CATS3}}
PROMPT_FILE = os.path.join(G, 'freeze', 'posthoc_confidence_prompt.txt')
def save_prompt():
    txt = ('POST HOC (D24). Single-pass prompt and schema with one change: an integer "confidence" from 0 to 100 for each category.\n'
           'Everything else is the frozen single-pass call: options %s, num_predict ladder %s, think false (removed if rejected), "\\n/nothink" appended for qwen models,\n'
           'schema by $ref (inline if rejected). A response counts as valid only if it is valid under the frozen single-pass rule and every confidence is an integer from 0 to 100.\n'
           'Score used: confidence / 100.\n\n=== PROMPT ({W} and {H} are the image width and height in pixels) ===\n%s\n\n=== SCHEMA ===\n%s\n\n=== SCHEMA (inline form, used only if a model rejects $ref) ===\n%s\n'
           % (json.dumps(SP_OPTIONS), SP_PREDICT_LADDER, SPC_PROMPT, json.dumps(SPC_SCHEMA, indent=1), json.dumps(SPC_SCHEMA_INLINE, indent=1)))
    if os.path.exists(PROMPT_FILE):
        if open(PROMPT_FILE, encoding='utf-8').read() != txt: raise SystemExit('REFUSED: %s exists with different content' % PROMPT_FILE)
        return
    with open(PROMPT_FILE, 'w', encoding='utf-8') as f: f.write(txt)
def _valid_spc(p):
    if not gcl._valid_sp(p): return False
    return all(isinstance(p[c].get('confidence'), int) and not isinstance(p[c].get('confidence'), bool) and 0 <= p[c]['confidence'] <= 100 for c in CATS3)
def _chat_c(model, content, img, options, fmt):
    """grove_calls._chat with the confidence schema (same flags and fallbacks)."""
    f = gcl.flags(model)
    body = {'model': model, 'messages': [{'role': 'user', 'content': content, 'images': [img['b64']]}], 'stream': False, 'keep_alive': '15m', 'options': options}
    if not f.get('no_think'): body['think'] = False
    body['format'] = SPC_SCHEMA_INLINE if f.get('schema_inline') else fmt
    try: return gcl.http_json('/api/chat', body, timeout=TIMEOUT)
    except gcl.CallError as e:
        s = str(e).lower()
        if 'think' in s and not f.get('no_think'): gcl.set_flag(model, 'no_think', True); return _chat_c(model, content, img, options, fmt)
        if ('$ref' in s or 'ref' in s or 'schema' in s or 'format' in s) and not f.get('schema_inline'):
            gcl.set_flag(model, 'schema_inline', True); return _chat_c(model, content, img, options, fmt)
        raise
def call_spc(model, setname, img, it):
    """grove_calls.call_sp with the confidence prompt and schema."""
    P = SPC_PROMPT.format(W=img['W'], H=img['H']) + ('\n/nothink' if model.startswith('qwen') else '')
    steps = []
    for n in SP_PREDICT_LADDER:
        r = _chat_c(model, P, img, dict(SP_OPTIONS, num_predict=n), SPC_SCHEMA); dr = r.get('done_reason')
        steps.append({'num_predict': n, 'done_reason': dr, 'eval_count': r.get('eval_count')})
        if dr != 'length': break
    content = (r.get('message') or {}).get('content', '')
    out = {'content': content, 'steps': steps, 'think_sent': not gcl.flags(model).get('no_think'), 'schema': 'inline' if gcl.flags(model).get('schema_inline') else 'ref'}
    if dr == 'length': return 'cut_off', out, dr
    try: p = json.loads(content)
    except ValueError: return 'parse_failure', out, dr
    if dr != 'stop' or not _valid_spc(p): return 'parse_failure', out, dr
    out['parsed'] = p; out['boxes'] = {c: gcl._box(p[c]['bbox'], img['W'], img['H']) for c in CATS3}
    out['confidence'] = {c: p[c]['confidence'] for c in CATS3}
    return 'valid', out, dr
_orig_job_config = gcl.job_config
def job_config(kind, model, setname, src):
    if kind != 'spc': return _orig_job_config(kind, model, setname, src)
    base = _orig_job_config('sp', model, setname, src)
    base.update({'kind': 'spc', 'prompt': SPC_PROMPT, 'schema': SPC_SCHEMA, 'validity': 'frozen single-pass rule plus integer confidence 0 to 100 for every category',
                 'posthoc': 'D24: frozen single-pass prompt and schema plus one integer confidence per category; score = confidence / 100'})
    return base
gcl.job_config = job_config; gcl.CALL['spc'] = call_spc

PLAN = [('p06_final', 'sp', 'qwen3.5:27b', 'sp', 'final'), ('p07_cal', 'spc', 'qwen3.5:27b', 'spc', 'calibration'), ('p07_final', 'spc', 'qwen3.5:27b', 'spc', 'final'),
        ('p07_cal', 'spc', 'gemma4:31b', 'spc', 'calibration'), ('p07_final', 'spc', 'gemma4:31b', 'spc', 'final')]
def plan_json(ids):
    est = {}
    for m, p in (('qwen3.5:27b', os.path.join(G, 'runs', 'e43', 'qwen3.5_27b__sp.jsonl')), ('gemma4:31b', os.path.join(G, 'runs', 'e52', 'gemma4_31b__sp.jsonl'))):
        s = [json.loads(l)['seconds'] for l in open(p, encoding='utf-8')]; s = [x for x in s if isinstance(x, (int, float))]
        est[m] = round(sum(s) / len(s), 2)
    return {'posthoc': 'Part B of 2026-11-10 (D24)', 'written': now(), 'jobs': [{'exp': e, 'kind': k, 'model': m, 'set': s, 'image_set': which, 'total': len(ids[which]),
            'file': os.path.relpath(gcl.job_path(e, m, s), G), 'est_seconds_per_image': est[m],
            'est_basis': 'mean seconds per image of the same model in the run (%s)' % ('runs\\e43' if m == 'qwen3.5:27b' else 'runs\\e52')} for e, k, m, s, which in PLAN]}

def main():
    if not os.path.exists(os.path.join(G, 'logs', 'final_scored.lock')): print('REFUSED: final scoring has not run'); return 2
    ml = read_json(os.path.join(G, 'logs', 'runner.lock'), {}) or {}
    if ml.get('pid') and pid_alive(ml['pid']) and time.time() - float(ml.get('heartbeat') or 0) < 1800: print('REFUSED: the main runner is running'); return 2
    if os.path.exists(os.path.join(G, 'logs', 'ALL_DONE_posthoc.txt')): print('ALL_DONE_posthoc exists; nothing to do'); return 0
    if not acquire_lock(): return 0
    status_thread(); log('post hoc runner start (D24), pid %d' % os.getpid()); save_prompt()
    ids = {'calibration': gd.list_ids('calibration'), 'final': gd.list_ids('final')}
    pj = os.path.join(MODE.results, 'plan.json')
    if not os.path.exists(pj): write_json(pj, plan_json(ids))
    gcl.ensure_ollama()
    for e, k, m, s, which in PLAN:
        items = [gcl.item(i, 'cs') for i in ids[which]]
        for attempt in range(1, 4):
            try:
                STATUS['note'] = 'post hoc %s %s %s' % (e, m, s); r = gcl.run_job(e, k, m, s, items); log('post hoc job done %s %s %s: %s' % (e, m, s, r)); break
            except Exception:
                log('post hoc job %s %s %s attempt %d failed:\n%s' % (e, m, s, attempt, traceback.format_exc())); time.sleep(60)
    STATUS['note'] = 'post hoc model runs finished'; write_status(); log('post hoc model runs finished')
    write_json(os.path.join(MODE.results, 'model_runs.done.json'), {'at': now()})
    d = read_json(lock_path(), {}) or {}
    if d.get('pid') == os.getpid(): write_json(lock_path(), {'pid': None, 'released': now(), 'heartbeat': 0})
    return 0
if __name__ == '__main__': sys.exit(main())
