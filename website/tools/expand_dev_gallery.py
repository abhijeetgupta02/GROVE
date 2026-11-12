"""Expand the public Gemini gallery from saved outputs. No inference.

Usage: python tools/expand_dev_gallery.py /path/to/gemini_development_images
Only the six NEW images are encoded. Existing seven records/assets stay intact.
Scores/boxes use the original development thresholds, NOT the target refit.
"""
import collections, hashlib, json, re, sys
from pathlib import Path
from PIL import Image

SITE = Path(__file__).resolve().parents[1]
REPO = SITE.parent
SOURCE = Path(sys.argv[1])
def load(path): return json.loads((REPO / path).read_text())
def number(name): return str(int(re.match(r"\d+", name)[0]))
def records(path): return {number(x["image_name"]): x for x in map(json.loads, (REPO / path).read_text().splitlines())}
H = records("runs/e12/d3_27b__h.jsonl")
M = records("runs/e11/d3_27b__m.jsonl")
B = records("runs/e09/gemma4_31b__sp.jsonl")
COCO = load("packet/data/grove203/annotations.coco.json")
category = {x["id"]: x["name"] for x in COCO["categories"]}
images = {number(x["file_name"]): x for x in COCO["images"]}
by_id = {x["id"]: number(x["file_name"]) for x in COCO["images"]}
MAP = {"Fall from Height": "fall", "PPE Deficiency": "ppe"}
KEY = {"fall": "Fall_Hazard", "ppe": "PPE_Violation"}
labels = collections.defaultdict(lambda: collections.defaultdict(list))
for a in COCO["annotations"]:
    c = MAP.get(category[a["category_id"]])
    if c:
        x, y, w, h = map(float, a["bbox"])
        labels[by_id[a["image_id"]]][c].append([x, y, x+w, y+h])
ground = {(number(x["image"]), x["category"]): x for x in load("results/e31_38.json")["items"]["31 fixed phrases"]}
TITLES = {
    "191": "An unguarded work platform", "200": "Fall exposure and missing PPE",
    "194": "An opening in the work floor", "125": "Missing head protection",
    "176": "An unguarded stairwell", "183": "Protection during workshop tasks",
    "197": "Cutting without eye protection", "178": "No scored violation on the haul road",
    "181": "No alert in the warehouse", "196": "Fall exposure at night",
    "201": "An alert with imprecise grounding", "198": "Debris without a Fall label",
    "182": "An alert without a matching Fall label",
}
ORDER = list(TITLES)
TH = {"fall": .12, "ppe": .50}
MQ = {"fall": .16, "ppe": .58}
def iou(a,b):
    inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    return inter/max(1e-9,(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter)
G = json.loads((SITE / "src/data/gallery.json").read_text())
old = {x["id"]: x for x in G["images"]}
manifest = []
out = []
for n in ORDER:
    if n in {"191", "200", "196", "183", "197", "178", "181"}:
        rec = old[n]
    else:
        assert H[n]["status"] == M[n]["status"] == B[n]["status"] == "valid"
        p = H[n]["output"]["probs"]
        s = {"fall": .5*(p["Fall_Hazard"]+max(p["f_fall_edge"],p["f_fall_opening"]))*(1-.35*p["ok_fall_protected"]),
             "ppe": .5*(p["PPE_Violation"]+p["f_worker"]*max(p["f_ppe_nohat"],p["f_ppe_novest"],p["f_ppe_noeye_glove"]))}
        dec = {c: s[c] >= TH[c] for c in KEY}
        truth = {c: bool(labels[n][c]) for c in KEY}
        im = Image.open(SOURCE / f"{n}.png").convert("RGB")
        W,Hh=im.size
        assert [W,Hh] == [int(float(images[n]["width"])), int(float(images[n]["height"]))]
        def normalized(box): return [round(float(v)/([W,Hh,W,Hh][k]), 4) for k,v in enumerate(box)]
        files={}
        for suffix, size in [("",1600),("_thumb",640)]:
            pic=im.copy();pic.thumbnail((size,size),Image.Resampling.LANCZOS)
            for ext,opts in [("webp",dict(format="WEBP",quality=84,method=6)),("jpg",dict(format="JPEG",quality=84,optimize=True,progressive=True))]:
                rel=f"gallery/dev_{n}{suffix}.{ext}";pic.save(SITE/"public"/rel,**opts)
                files[("thumb_" if suffix else "full_")+ext]=rel
            if suffix: tw,th=pic.size
            else: fw,fh=pic.size
        grove={"scores":{c:round(s[c],4) for c in KEY},"decisions":dec,"first_freeze_decisions":dec,
               "boxes":{},"phrase":{},"box_source":{},"top_iou":{},"probs":{k:round(v,4) for k,v in p.items()}}
        for c,key in KEY.items():
            if not dec[c]: continue
            item=ground[(n,key)]
            grove["boxes"][c]=[normalized(b) for b in item["boxes"]]
            grove["phrase"][c]=item["phrase"]
            grove["box_source"][c]=item["source"]
            grove["top_iou"][c]=round(max([iou(item["boxes"][0],b) for b in labels[n][c]] or [0]),4) if item["boxes"] else 0
        gem={k:{} for k in ["decisions","evidence","box_as_written","box_drawn","fits_pixel_rule","fits_grid_reading"]}
        for c,key in KEY.items():
            a=B[n]["output"]["parsed"][key];pres=bool(a["present"]);gem["decisions"][c]=pres
            if pres:
                gem["evidence"][c]=a["evidence"];b=a["bbox"]
                if len(b)==4:
                    gem["box_as_written"][c]=b;gem["box_drawn"][c]=normalized(b)
                    gem["fits_pixel_rule"][c]=0<=b[0]<b[2]<=W and 0<=b[1]<b[3]<=Hh
                    gem["fits_grid_reading"][c]=all(0<=v<=1000 for v in b)
        correct=all(dec[c]==truth[c] for c in KEY)
        grounded=all(grove["top_iou"].get(c,0)>=.5 for c in KEY if dec[c])
        failure=None if correct and grounded else "grounding overlap below 0.5" if correct else "false Fall alert"
        rec={"id":n,"role":"success" if correct and grounded else "failure","failure_type":failure,
            "draw_reason":"selected for clear Fall/PPE illustration" if failure is None else "selected to show a development-set limitation",
            "teaser":False,"files":files,"width":fw,"height":fh,"thumb_width":tw,"thumb_height":th,
            "original_width":W,"original_height":Hh,"illumination":"generated with Google Gemini","camera_distance":"development image",
            "size_band":None,"caption":None,"label_reason":{"fall":None,"ppe":None},"labels":truth,
            "label_boxes":{c:[normalized(b) for b in labels[n][c]] for c in KEY},"grove":grove,
            "main_question":{"scores":{c:round(M[n]["output"]["probs"][key],4) for c,key in KEY.items()},
                             "decisions":{c:M[n]["output"]["probs"][key]>=MQ[c] for c,key in KEY.items()}},
            "gemma":gem,"outcome":{"grove_correct":correct,"gemma_wrong":any(gem["decisions"][c]!=truth[c] for c in KEY),"disagree":any(gem["decisions"][c]!=dec[c] for c in KEY)}}
        manifest.append({"id":n,"source_image":f"gemini_development_images/{n}.png","source_sha256":hashlib.sha256((SOURCE/f"{n}.png").read_bytes()).hexdigest(),"decisions_correct":correct,"grounding_meets_0_5":grounded})
    rec["title"]=TITLES[n]
    out.append(rec)
G["images"]=out
G["thresholds"]=TH # Explicitly development thresholds in all gallery consumers.
G["featured"]=["191","194","197","125","176","200"]
G["selection_rule"]=("Author-selected examples from our Gemini-generated development images, showing Fall and protective equipment only. "
    "Ten illustrate correct identification and, where an alert is raised, a top evidence box at IoU ≥ 0.5. "
    "Three show limitations: two false Fall alerts and one correctly identified Fall hazard with imprecise grounding. "
    "Development thresholds (Fall 0.12, PPE 0.50) were fit on these same 203 images. These are in-sample illustrations, not a representative test; Electrical is not illustrated. "
    "Final-set performance is reported separately in Results.")
G["candidates_successes"]=sum(x["role"]=="success" for x in out)
G["failure_types"]=["false Fall alert","grounding overlap below 0.5"]
G["sources"]["boxes"]="results/e31_38.json -> items.31 fixed phrases (new examples); results/gcache_gdino.jsonl (original examples)"
(SITE/"src/data/gallery.json").write_text(json.dumps(G,ensure_ascii=False,indent=1)+"\n")
(SITE/"src/data/gallery_expansion_manifest.json").write_text(json.dumps({"selection":"13 selected development examples; six added from existing saved outputs","new_images":manifest},indent=2)+"\n")
print(f"Gallery: {len(out)} examples; {len(manifest)} added; no model calls.")
