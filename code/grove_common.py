"""GROVE run system: shared settings, Ollama client, resumable model-call jobs, lock and status.
Design: GROVE_Experiment_Design.md (5 Nov 2026), Section 14. Windows PC, frozen Ollama 0.40.14."""
import base64, hashlib, io, json, os, re, shutil, socket, subprocess, sys, threading, time, traceback, urllib.error, urllib.request
from datetime import datetime
import numpy as np

G = r'C:\GROVE_PC'
PK = os.path.join(G, 'packet')
OLLAMA_EXE = os.path.join(G, 'ollama', '0.40.14', 'ollama.exe')
OLLAMA_VERSION = '0.40.14'
HOST = 'http://127.0.0.1:11434'
SEED = 20260422
TIMEOUT = 1800
# Restart 2026-11-05 (logs\deviations.md): wait before every decision-model call (/v1/systemone, sets h, m and S0) and every GROVE phrase call;
# no wait before single-pass calls. The wait is never counted in any seconds field or speed figure.
PAUSE_SECONDS = {'decision': 0.0, 'phrase': 0.0, 'sp': 0.0}  # 2026-11-06 (D22, owner's request): 7 s pause removed; kept in config_hash as 0 for decision and phrase calls
QUICK_RETRY_TEXT = 'Context size has been exceeded'  # decision call, HTTP 500 with this text: one immediate retry before the normal 10/60/300 s schedule
RETRY_DELAYS = [10, 60, 300]
CATS3 = ['Fall_Hazard', 'Electrocution_Hazard', 'PPE_Violation']
CATS2 = ['Fall_Hazard', 'PPE_Violation']
SHORT = {'Fall_Hazard': 'Fall', 'Electrocution_Hazard': 'Electrical', 'PPE_Violation': 'PPE', 'Housekeeping_Storage': 'Housekeeping'}
DECISION = ['clef:27b', 'clef-flash:9b', 'pplx-decider:27b', 'd3:9b', 'd3:27b']
GENERATORS = ['qwen3.5:9b', 'qwen3.5:27b', 'gemma4:31b', 'mistral-small3.2:24b', 'ministral-3:14b', 'qwen3-vl:32b']
PHRASE_MODEL = 'qwen3.5:9b'
ENV = {'OLLAMA_MODELS': r'C:\Users\Shruti Singh\.ollama\models', 'OLLAMA_MAX_LOADED_MODELS': '1', 'OLLAMA_NUM_PARALLEL': '1',
       'OLLAMA_KEEP_ALIVE': '15m', 'HF_HOME': os.path.join(G, 'tools', 'hf'), 'TORCH_HOME': os.path.join(G, 'tools', 'torch'),
       'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'PYTHONUTF8': '1'}
for _k, _v in ENV.items(): os.environ.setdefault(_k, _v)

# ---------------------------------------------------------------- mode and folders
class Mode:
    def __init__(self, name):
        self.name = name
        self.root = G if name == 'main' else os.path.join(G, 'runs', 'pilot')
        for d in ('runs', 'results', 'reports', 'freeze', 'lists', 'logs'):
            p = os.path.join(G, d) if name == 'main' else os.path.join(self.root, d)
            setattr(self, d, p); os.makedirs(p, exist_ok=True)
        self.main_lists = os.path.join(G, 'lists'); self.main_reports = os.path.join(G, 'reports')
    def path(self, kind, *parts): return os.path.join(getattr(self, kind), *parts)
MODE = Mode(os.environ.get('GROVE_MODE', 'main'))
def set_mode(name):
    global MODE; MODE = Mode(name); return MODE

def now(): return datetime.now().isoformat(timespec='seconds')
LOG_LOCK = threading.Lock()
def log(msg):
    line = '%s  %s' % (now(), msg)
    with LOG_LOCK:
        with open(MODE.path('logs', 'run.log'), 'a', encoding='utf-8') as f: f.write(line + '\n')
    print(line, flush=True)

# ---------------------------------------------------------------- files
def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def sha256_text(s): return sha256_bytes(s.encode('utf-8'))
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()
def write_json(p, obj):
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f: json.dump(obj, f, indent=1, ensure_ascii=False, default=str)
    os.replace(tmp, p)
def read_json(p, default=None):
    if not os.path.exists(p): return default
    with open(p, encoding='utf-8') as f: return json.load(f)
def write_text(p, s):
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f: f.write(s)
    os.replace(tmp, p)
def append_jsonl(p, rec):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n'); f.flush(); os.fsync(f.fileno())
def read_jsonl(p):
    out = []
    if not os.path.exists(p): return out
    with open(p, encoding='utf-8') as f:
        for l in f:
            l = l.strip()
            if not l: continue
            try: out.append(json.loads(l))
            except ValueError: pass   # a line cut by a crash is ignored
    return out

# ---------------------------------------------------------------- question sets and prompts
PROMPTS = read_json(os.path.join(PK, 'prompts', 'prompts.json'))
SET_M_KEYS = ['Fall_Hazard', 'Electrocution_Hazard', 'PPE_Violation', 'Housekeeping_Storage']
SETS = {'h': PROMPTS['h'], 'S0': PROMPTS['S0'],
        'm': {'state': PROMPTS['h']['state'], 'questions': {k: PROMPTS['h']['questions'][k] for k in SET_M_KEYS}}}
assert len(SETS['h']['questions']) == 16 and len(SETS['S0']['questions']) == 7 and len(SETS['m']['questions']) == 4
SP_PROMPT = ('Inspect this construction site image for visible safety violations.\n'
 'Judge only visible physical conditions. Safety equipment (guardrails, harnesses, hard hats, vests, barriers) and normal tools in safe use are NOT violations.\n'
 'Image size: {W} x {H} pixels.\n\nAnswer for each category:\n'
 'Fall_Hazard: Is a worker exposed to falling into an unguarded trench/opening or from an elevated edge, roof, ladder, or scaffold that lacks guardrails or a tied-off harness?\n'
 'Electrocution_Hazard: Is there an unprotected electrical hazard, such as damaged or exposed live wiring, makeshift power hookups, or work dangerously close to overhead power lines?\n'
 'PPE_Violation: Is a visible construction worker missing a required hard hat, high-visibility vest, eye protection, or task-specific protective gear (excluding fall harnesses)?\n\n'
 'For each category give:\npresent: true only if the violation is clearly visible, otherwise false.\nevidence: one short clause describing what you see.\n'
 'bbox: [x1, y1, x2, y2] integer pixel coordinates of the violation, or [] if absent.\n\nReturn JSON only.')
_C = {'type': 'object', 'required': ['present', 'evidence', 'bbox'], 'properties': {'present': {'type': 'boolean'}, 'evidence': {'type': 'string'},
      'bbox': {'type': 'array', 'items': {'type': 'integer'}}}}
SP_SCHEMA = {'type': 'object', 'required': CATS3, 'properties': {c: {'$ref': '#/$defs/c'} for c in CATS3}, '$defs': {'c': _C}}
SP_SCHEMA_INLINE = {'type': 'object', 'required': CATS3, 'properties': {c: _C for c in CATS3}}
SP_OPTIONS = {'temperature': 0, 'num_ctx': 32768, 'num_predict': 1024, 'seed': SEED}  # restart 2026-11-05: 8192 -> 32768 (owner's decision; logs\deviations.md)
SP_PREDICT_LADDER = [1024, 2048, 4096]
PHRASE_PROMPT = ('Look at this construction site image. The concern is a possible {C} violation. If an object showing this violation is clearly visible, '
 'write a 2-to-4 word phrase naming it, such as "worker on roof edge", "open trench edge", "exposed electrical wires" or "worker without hard hat". '
 'If nothing showing it is clearly visible, reply NONE. Reply with the phrase or NONE only.')
PHRASE_OPTIONS = {'temperature': 0, 'num_predict': 32, 'seed': SEED}
CAT_DISPLAY = {'Fall_Hazard': 'Fall Hazard', 'Electrocution_Hazard': 'Electrocution Hazard', 'PPE_Violation': 'PPE Violation'}
FIXED_PHRASES = {'Fall_Hazard': {'f_fall_edge': 'worker on elevated edge', 'f_fall_opening': 'open trench or floor opening'},
                 'Electrocution_Hazard': {'f_elec_wire': 'exposed electrical wires', 'f_elec_lines': 'overhead power lines'},
                 'PPE_Violation': {'f_ppe_nohat': 'worker without hard hat', 'f_ppe_novest': 'worker without safety vest', 'f_ppe_noeye_glove': 'worker using power tool'}}
ENC_203 = 'grove203:packet encoded_q95 bytes as stored'
def enc_cs10k():
    import PIL; return 'cs10k:parquet image -> RGB -> JPEG quality 95, Pillow %s' % PIL.__version__

# ---------------------------------------------------------------- formulas (fixed weights, Section 5.4)
def mx(*a): return np.maximum.reduce([np.asarray(x, float) for x in a])
def f_fall(q, protection=True, opening=True):
    side = mx(q['f_fall_edge'], q['f_fall_opening']) if opening else np.asarray(q['f_fall_edge'], float)
    s = 0.5 * (np.asarray(q['Fall_Hazard'], float) + side)
    return s * (1 - 0.35 * np.asarray(q['ok_fall_protected'], float)) if protection else s
def f_ppe(q, worker=True, vest=True):
    keys = ['f_ppe_nohat', 'f_ppe_novest', 'f_ppe_noeye_glove'] if vest else ['f_ppe_nohat', 'f_ppe_noeye_glove']
    w = np.asarray(q['f_worker'], float) if worker else 1.0
    return 0.5 * (np.asarray(q['PPE_Violation'], float) + w * mx(*[q[k] for k in keys]))
def f_elec(q): return 0.5 * (np.asarray(q['Electrocution_Hazard'], float) + mx(q['f_elec_wire'], q['f_elec_lines'])) * (1 - 0.40 * np.asarray(q['ok_elec_testing'], float))
def f_house(q): return (np.asarray(q['Housekeeping_Storage'], float) + np.asarray(q['f_house_trip'], float) + np.asarray(q['f_house_debris'], float)) / 3
FORMULA_TEXT = {'Fall': 'Fall = 0.5*(Fall_Hazard + max(f_fall_edge, f_fall_opening)) * (1 - 0.35*ok_fall_protected)',
                'PPE': 'PPE = 0.5*(PPE_Violation + f_worker*max(f_ppe_nohat, f_ppe_novest, f_ppe_noeye_glove))',
                'Electrical formula': 'Electrical = 0.5*(Electrocution_Hazard + max(f_elec_wire, f_elec_lines)) * (1 - 0.40*ok_elec_testing)',
                'Housekeeping': 'Housekeeping = (Housekeeping_Storage + f_house_trip + f_house_debris)/3'}

# ---------------------------------------------------------------- lock, heartbeat, status
STATUS = {'experiment': '', 'model': '', 'done': 0, 'total': 0, 'recent': [], 'failures': 0, 'note': '', 'started': time.time()}
GPU_PEAK = {}
def lock_path(): return MODE.path('logs', 'runner.lock')
def pid_alive(pid):
    try:
        out = subprocess.run(['tasklist', '/FI', 'PID eq %d' % int(pid), '/NH'], capture_output=True, text=True, timeout=30).stdout
        return str(int(pid)) in out
    except Exception: return True
def acquire_lock():
    p = lock_path(); d = read_json(p, None) if os.path.exists(p) else None
    if d:
        age = time.time() - float(d.get('heartbeat', 0))
        if pid_alive(d.get('pid', -1)) and age < 1800:
            print('another runner (pid %s) holds the lock, heartbeat %.0f s ago; exiting' % (d.get('pid'), age)); return False
        if pid_alive(d.get('pid', -1)):
            subprocess.run(['taskkill', '/PID', str(d['pid']), '/F', '/T'], capture_output=True)
            log('stopped old runner pid %s (heartbeat %.0f s old)' % (d.get('pid'), age))
    write_json(p, {'pid': os.getpid(), 'heartbeat': time.time(), 'started': now()}); return True
def heartbeat():
    p = lock_path(); d = read_json(p, {}) or {}
    if d.get('pid') == os.getpid():
        d['heartbeat'] = time.time(); d['heartbeat_iso'] = now()
        try: write_json(p, d)
        except Exception: pass
def gpu_stats():
    try:
        o = subprocess.run(['nvidia-smi', '--query-gpu=temperature.gpu,memory.used,memory.total,utilization.gpu', '--format=csv,noheader,nounits'],
                           capture_output=True, text=True, timeout=30).stdout.strip().split(',')
        return {'temp_c': round(float(o[0]), 1), 'mem_used_mib': int(float(o[1])), 'mem_total_mib': int(float(o[2])), 'util_pct': int(float(o[3]))}
    except Exception: return {}
def write_status():
    s = STATUS; g = gpu_stats(); key = '%s|%s' % (s['experiment'], s['model'])
    if g.get('mem_used_mib') is not None:
        GPU_PEAK[key] = max(GPU_PEAK.get(key, 0), g['mem_used_mib'])
        try: write_json(MODE.path('results', 'gpu_peaks.json'), {**read_json(MODE.path('results', 'gpu_peaks.json'), {}), key: GPU_PEAK[key]})
        except Exception: pass
    rec = s['recent'][-30:]; spi = (sum(rec) / len(rec)) if rec else None
    if MODE.name == 'main':  # restart 2026-11-05: per-job estimate, recomputed every minute (code\grove_eta.py); no pause since 2026-11-06 (D22)
        try:
            import grove_eta; e = grove_eta.estimate(G, live=(s['experiment'], s['model'], spi))
            s['overall_eta'] = '%s (%.1f h left; %s)' % (e['finish'], e['remaining_h'], e['basis'])
        except Exception: s['overall_eta'] = '-'
    else: s['overall_eta'] = '-'
    left = max(s['total'] - s['done'], 0); eta = (time.time() + left * spi) if spi else None
    txt = ('updated: %s\nmode: %s\nexperiment: %s\nmodel: %s\nimages done: %d / %d\nseconds per image (last 30): %s\n'
           'estimated finish of this step: %s\nestimated finish of the whole run: %s\nGPU temperature C: %s\nGPU memory MiB: %s / %s\nGPU utilization %%: %s\n'
           'failures so far (terminal, not valid): %d\nnote: %s\n') % (
        now(), MODE.name, s['experiment'], s['model'], s['done'], s['total'], ('%.1f' % spi) if spi else '-',
        datetime.fromtimestamp(eta).isoformat(timespec='minutes') if eta else '-', s.get('overall_eta', '-'),
        g.get('temp_c', '-'), g.get('mem_used_mib', '-'), g.get('mem_total_mib', '-'), g.get('util_pct', '-'), s['failures'], s['note'])
    try: write_text(MODE.path('logs', 'status.txt'), txt)
    except Exception: pass
def status_thread():
    def loop():
        while True:
            try: write_status(); heartbeat()
            except Exception: pass
            time.sleep(60)
    t = threading.Thread(target=loop, daemon=True); t.start(); return t
def wait_for_disk():
    while shutil.disk_usage(G).free < 20e9:
        STATUS['note'] = 'free disk below 20 GB, waiting'; log('free disk %.1f GB < 20 GB; waiting 10 minutes' % (shutil.disk_usage(G).free / 1e9))
        heartbeat(); time.sleep(600)
    if STATUS['note'].startswith('free disk'): STATUS['note'] = ''
