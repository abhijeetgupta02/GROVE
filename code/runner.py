"""GROVE runner. One runner only (logs\\runner.lock with heartbeat). Usage: runner.py [--mode main|pilot]"""
import argparse, collections, json, os, subprocess, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('--mode', default='main'); ap.add_argument('--only', default=''); A = ap.parse_args()
os.environ['GROVE_MODE'] = A.mode
import grove_common as gc
from grove_common import *
set_mode(A.mode)
import grove_calls as gcl, grove_stages as st
PY = sys.executable

def stage_J(c):
    if MODE.name == 'pilot': return pilot_score_final_test()
    r = subprocess.run([PY, os.path.join(G, 'code', 'score_final.py'), '--mode', MODE.name], capture_output=True, text=True); log('score_final exit %d: %s' % (r.returncode, r.stdout.strip()[-300:]))
    if r.returncode not in (0, 2, 3): raise RuntimeError('score_final failed: %s %s' % (r.stdout[-500:], r.stderr[-1500:]))
def pilot_score_final_test():
    env = dict(os.environ, GROVE_MODE='pilot'); sf = os.path.join(G, 'code', 'score_final.py'); res = {}
    def run(extra_env=None, approval=True):
        e = dict(env, **(extra_env or {})); r = subprocess.run([PY, sf, '--mode', 'pilot'] + (['--i-have-approval'] if approval else []), capture_output=True, text=True, env=e); return r.returncode, r.stdout.strip()[-300:], r.stderr.strip()[-800:]
    outs = [MODE.path('results', 'e54_final.json'), MODE.path('results', 'e55_removal_final.json')]
    res['auto_run'] = run({'GROVE_TEST_STOP_BEFORE_LOCK': '1'}, approval=False)   # held (3) or stopped before the lock (6)
    if os.path.exists(MODE.path('logs', 'final_scored.lock')): res['note'] = 'lock already existed; test cannot run'; write_json(MODE.path('results', 'pilot_score_final_test.json'), res); return
    res['stop_before_lock'] = run({'GROVE_TEST_STOP_BEFORE_LOCK': '1'}); h1 = {os.path.basename(p): sha256_file(p) for p in outs if os.path.exists(p)}
    res['rerun'] = run(); h2 = {os.path.basename(p): sha256_file(p) for p in outs if os.path.exists(p)}
    res['identical_outputs'] = bool(h1) and h1 == h2; res['lock_exists'] = os.path.exists(MODE.path('logs', 'final_scored.lock'))
    res['after_lock'] = run(); res['refused_after_lock'] = res['after_lock'][0] == 2
    res['pass'] = res['auto_run'][0] in (3, 6) and res['identical_outputs'] and res['lock_exists'] and res['refused_after_lock'] and res['stop_before_lock'][0] == 6 and res['rerun'][0] == 0
    write_json(MODE.path('results', 'pilot_score_final_test.json'), res); log('pilot score_final test: %s' % res['pass'])
    if not res['pass']: raise RuntimeError('pilot score_final test failed: %s' % json.dumps(res)[:1500])
def pilot_resume_test(c):
    s = st.selection(); M = s['main_model']; R = gcl.load_results('e12', M, 'h'); names = [n for n in c.names if n in R][:3]
    if len(names) < 3: raise RuntimeError('resume test needs 3 terminal lines')
    p = gcl.job_path('resume_test', M, 'h'); os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p): os.replace(p, p + '.%d.old' % int(time.time()))
    a, b, cc = (dict(R[n]) for n in names); b['terminal'] = False; cc['config_hash'] = 'another-hash'
    for x in (a, b, cc): append_jsonl(p, x)
    before = len(read_jsonl(p)); gcl.run_job('resume_test', 'decision', M, 'h', [gcl.item(n, '203') for n in names]); lines = read_jsonl(p)
    h = read_json(p[:-6] + '.config.json')['config_hash']; new = lines[before:]; cnt = collections.Counter(d['key'] for d in lines if d.get('config_hash') == h and d.get('terminal'))
    ok = sorted(d['key'] for d in new) == sorted([names[1], names[2]]) and all(cnt[n] == 1 for n in names)
    res = {'terminal_line_skipped': names[0] not in [d['key'] for d in new], 'non_terminal_rerun': names[1] in [d['key'] for d in new], 'other_hash_rerun': names[2] in [d['key'] for d in new],
           'one_terminal_line_each': all(cnt[n] == 1 for n in names), 'pass': ok}
    write_json(MODE.path('results', 'pilot_resume_test.json'), res); log('pilot resume test: %s' % res)
    if not ok: raise RuntimeError('resume test failed: %s' % res)

STAGES = [('C', st.stage_C), ('D', st.stage_D), ('E', st.stage_E), ('F', st.stage_F), ('G', st.stage_G), ('H', st.stage_H), ('I', st.stage_I), ('J', stage_J), ('K', st.stage_K)]
def main():
    if os.path.exists(MODE.path('logs', 'ALL_DONE.txt')): print('ALL_DONE exists; nothing to do'); return 0
    if not acquire_lock(): return 0
    status_thread(); log('runner start, mode %s, pid %d' % (MODE.name, os.getpid()))
    if not os.path.exists(MODE.path('results', 'run_started.json')): write_json(MODE.path('results', 'run_started.json'), {'at': now()})
    gcl.ensure_ollama(); c = st.Ctx()
    for name, fn in STAGES:
        if A.only and name not in A.only: continue
        if os.path.exists(MODE.path('results', 'stage_%s.done.json' % name)): continue
        for attempt in range(1, 4):
            try:
                STATUS['note'] = 'stage %s' % name; fn(c); write_json(MODE.path('results', 'stage_%s.done.json' % name), {'at': now()}); break
            except Exception:
                tb = traceback.format_exc(); log('STAGE %s attempt %d failed:\n%s' % (name, attempt, tb))
                write_json(MODE.path('results', 'stage_%s.attempt%d.failed.json' % (name, attempt)), {'error': tb, 'at': now()}); time.sleep(60 if MODE.name == 'main' else 5)
        else:
            write_json(MODE.path('results', 'stage_%s.failed.json' % name), {'at': now()}); log('STAGE %s marked failed after 3 attempts; continuing' % name)
        if MODE.name == 'pilot' and name == 'C' and not os.path.exists(MODE.path('results', 'pilot_resume_test.json')):
            try: pilot_resume_test(c)
            except Exception: log('resume test error:\n' + traceback.format_exc())
    STATUS['note'] = 'finished'; write_status(); log('runner finished')
    d = read_json(lock_path(), {}) or {}
    if d.get('pid') == os.getpid(): write_json(lock_path(), {'pid': None, 'released': now(), 'heartbeat': 0})
    return 0
if __name__ == '__main__': sys.exit(main())
