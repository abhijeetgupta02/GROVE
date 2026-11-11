"""Parallel ranged downloader (stdlib only). Usage: pdl.py URL OUT [--parts N] [--threads T] [--sha256 HEX]
Keeps partial parts for resume; a part that stalls for 30 s is retried on a fresh connection. Never overwrites an existing OUT."""
import argparse, hashlib, os, queue, sys, threading, time, urllib.request
ap = argparse.ArgumentParser(); ap.add_argument('url'); ap.add_argument('out'); ap.add_argument('--parts', type=int, default=32)
ap.add_argument('--threads', type=int, default=12); ap.add_argument('--sha256'); a = ap.parse_args()
UA = {'User-Agent': 'grove-setup/1.0'}
def log(m): print(time.strftime('%H:%M:%S'), m, flush=True)
if os.path.exists(a.out): log('exists, not overwriting: ' + a.out); sys.exit(0)
def size_of(url):
    for _ in range(5):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={**UA, 'Range': 'bytes=0-0'}), timeout=60)
            cr = r.headers.get('Content-Range'); r.close()
            if cr: return int(cr.split('/')[-1])
        except Exception as e: log('size retry: %s' % e); time.sleep(5)
    raise SystemExit('cannot get size')
total = size_of(a.url); log('size %d bytes' % total)
pd = a.out + '.parts'; os.makedirs(pd, exist_ok=True)
n = max(1, min(a.parts, total // (1 << 20) or 1)); step = -(-total // n)
ranges = [(i, i * step, min(total, (i + 1) * step) - 1) for i in range(n) if i * step < total]
q = queue.Queue(); [q.put(r) for r in ranges]; done = [0] * len(ranges); lock = threading.Lock(); failed = []
def work():
    while True:
        try: i, s, e = q.get_nowait()
        except queue.Empty: return
        p = os.path.join(pd, '%04d' % i); want = e - s + 1
        for attempt in range(60):
            have = os.path.getsize(p) if os.path.exists(p) else 0
            if have >= want: break
            try:
                req = urllib.request.Request(a.url, headers={**UA, 'Range': 'bytes=%d-%d' % (s + have, e)})
                with urllib.request.urlopen(req, timeout=30) as r, open(p, 'ab') as f:
                    if r.status != 206: raise IOError('status %s' % r.status)
                    while True:
                        b = r.read(1 << 20)
                        if not b: break
                        f.write(b)
            except Exception as ex:
                time.sleep(min(30, 2 + attempt))
        if os.path.getsize(p) != want: failed.append(i)
        with lock: done[i] = 1
ts = [threading.Thread(target=work, daemon=True) for _ in range(a.threads)]; [t.start() for t in ts]; t0 = time.time()
while any(t.is_alive() for t in ts):
    time.sleep(15); got = sum(os.path.getsize(os.path.join(pd, f)) for f in os.listdir(pd))
    log('%.1f%%  %.1f MB/s' % (100 * got / total, got / 1e6 / max(time.time() - t0, 1)))
if failed: raise SystemExit('parts failed: %s' % failed)
h = hashlib.sha256(); tmp = a.out + '.tmp'
with open(tmp, 'wb') as f:
    for i, _, _ in ranges:
        with open(os.path.join(pd, '%04d' % i), 'rb') as g:
            while True:
                b = g.read(1 << 22)
                if not b: break
                f.write(b); h.update(b)
if os.path.getsize(tmp) != total: raise SystemExit('size mismatch')
d = h.hexdigest(); log('sha256 ' + d)
if a.sha256 and d.lower() != a.sha256.lower(): raise SystemExit('SHA256 MISMATCH, expected ' + a.sha256)
os.replace(tmp, a.out); log('OK ' + a.out)
