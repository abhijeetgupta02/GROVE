"""Check gallery scores, decisions, labels and new evidence boxes against saved sources."""
from pathlib import Path
import json,re
SITE=Path(__file__).resolve().parents[1];REPO=SITE.parent
G=json.loads((SITE/'src/data/gallery.json').read_text())
def norm(n):return str(int(re.match(r'\d+',n)[0]))
def jl(p):return {norm(x['image_name']):x for x in map(json.loads,(REPO/p).read_text().splitlines())}
H=jl('runs/e12/d3_27b__h.jsonl');M=jl('runs/e11/d3_27b__m.jsonl');B=jl('runs/e09/gemma4_31b__sp.jsonl')
co=json.loads((REPO/'packet/data/grove203/annotations.coco.json').read_text());im={x['id']:x for x in co['images']};cat={x['id']:x['name'] for x in co['categories']};labels={}
for a in co['annotations']:
 c={'Fall from Height':'fall','PPE Deficiency':'ppe'}.get(cat[a['category_id']])
 if c:labels.setdefault(norm(im[a['image_id']]['file_name']),{}).setdefault(c,[]).append(list(map(float,a['bbox'])))
ground={(norm(x['image']),x['category']):x for x in json.loads((REPO/'results/e31_38.json').read_text())['items']['31 fixed phrases']}
keys={'fall':'Fall_Hazard','ppe':'PPE_Violation'};checks=0
for x in G['images']:
 n=x['id'];p=H[n]['output']['probs'];W,Hh=x['original_width'],x['original_height'];assert H[n]['status']==M[n]['status']==B[n]['status']=='valid'
 s={'fall':.5*(p['Fall_Hazard']+max(p['f_fall_edge'],p['f_fall_opening']))*(1-.35*p['ok_fall_protected']),'ppe':.5*(p['PPE_Violation']+p['f_worker']*max(p['f_ppe_nohat'],p['f_ppe_novest'],p['f_ppe_noeye_glove']))}
 def nb(b):return [v/d for v,d in zip(b,[W,Hh,W,Hh])]
 for c,k in keys.items():
  assert abs(x['grove']['scores'][c]-s[c])<=.000051;assert x['grove']['decisions'][c]==(s[c]>=G['thresholds'][c]);assert x['labels'][c]==bool(labels.get(n,{}).get(c));assert x['gemma']['decisions'][c]==B[n]['output']['parsed'][k]['present'];checks+=4
  if x['grove']['decisions'][c]:
   stored=ground[(n,k)];assert x['grove']['phrase'][c]==stored['phrase'];assert x['grove']['box_source'][c]==stored['source'];checks+=2
   assert all(abs(a-b)<=.000051 for a,b in zip(x['grove']['boxes'][c][0],nb(stored['boxes'][0])));checks+=1
  expected=[nb([a,b,a+w,b+h]) for a,b,w,h in labels.get(n,{}).get(c,[])]
  assert len(x['label_boxes'][c])==len(expected)
  for aa,bb in zip(x['label_boxes'][c],expected):assert all(abs(a-b)<=.000051 for a,b in zip(aa,bb))
  checks+=1
 assert x['role']=='failure' or all(x['grove']['decisions'][c]==x['labels'][c] and (not x['grove']['decisions'][c] or x['grove']['top_iou'][c]>=.5) for c in keys)
print(f'Gallery source verification: {checks} checks passed across {len(G["images"])} scenes. No inference.')
