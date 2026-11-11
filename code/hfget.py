"""Download chosen files of Hugging Face repos into an offline HF cache (HF_HOME/hub), pinned to the current commit.
Usage: hfget.py HF_HOME repo_id=file1,file2 ...   (big files go through pdl.py)."""
import json, os, subprocess, sys, time, urllib.request
HOME = sys.argv[1]; HUB = os.path.join(HOME, 'hub'); PDL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdl.py')
UA = {'User-Agent': 'grove-setup/1.0'}
def get(u, t=60): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
out = {}
for spec in sys.argv[2:]:
    repo, files = spec.split('=', 1); files = files.split(',')
    info = json.loads(get('https://huggingface.co/api/models/%s/revision/main' % repo)); sha = info['sha']
    sib = {s['rfilename'] for s in info.get('siblings', [])}
    base = os.path.join(HUB, 'models--' + repo.replace('/', '--')); snap = os.path.join(base, 'snapshots', sha)
    os.makedirs(snap, exist_ok=True); os.makedirs(os.path.join(base, 'refs'), exist_ok=True)
    with open(os.path.join(base, 'refs', 'main'), 'w') as f: f.write(sha)
    rec = {'sha': sha, 'files': {}}
    for fn in files:
        if fn not in sib: print(repo, 'missing in repo:', fn, flush=True); rec['files'][fn] = 'MISSING'; continue
        dst = os.path.join(snap, fn); url = 'https://huggingface.co/%s/resolve/%s/%s' % (repo, sha, fn)
        if os.path.exists(dst): rec['files'][fn] = os.path.getsize(dst); continue
        r = subprocess.run([sys.executable, '-I', PDL, url, dst, '--parts', '16', '--threads', '8'], capture_output=True, text=True)
        print(repo, fn, r.stdout.strip().splitlines()[-1:] , r.stderr.strip()[-300:], flush=True)
        rec['files'][fn] = os.path.getsize(dst) if os.path.exists(dst) else 'FAILED'
    out[repo] = rec
json.dump(out, open(os.path.join(HOME, 'hfget_%d.json' % int(time.time())), 'w'), indent=1); print(json.dumps(out, indent=1))
