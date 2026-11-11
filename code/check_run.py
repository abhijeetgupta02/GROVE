"""Health check: runner lock, duplicate terminal lines (same key and config_hash), progress. Usage: check_run.py [main|pilot]"""
import collections, glob, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grove_common import *
M = set_mode(sys.argv[1] if len(sys.argv) > 1 else 'main')
lk = read_json(M.path('logs', 'runner.lock'), {}) or {}; print('lock:', lk.get('pid'), 'heartbeat age s:', round(time.time() - float(lk.get('heartbeat') or 0)), 'alive:', pid_alive(lk['pid']) if lk.get('pid') else None)
dups = 0; tot = 0
for p in sorted(glob.glob(M.path('runs', '*', '*.jsonl'))):
    cp = p[:-6] + '.config.json'
    if not os.path.exists(cp): continue
    h = read_json(cp)['config_hash']; c = collections.Counter(d.get('key') for d in read_jsonl(p) if d.get('config_hash') == h and d.get('terminal'))
    d2 = {k: v for k, v in c.items() if v > 1}; dups += len(d2); tot += len(c)
    print('%-60s terminal %4d  duplicates %d' % (os.path.relpath(p, M.root), len(c), len(d2)))
print('TOTAL terminal %d, images with more than one terminal line: %d' % (tot, dups))
print(open(M.path('logs', 'status.txt'), encoding='utf-8').read() if os.path.exists(M.path('logs', 'status.txt')) else 'no status.txt')
