"""Grounding: GroundingDINO primary box search, DETR + OpenCLIP fallback (Section 5.2, Section 14 Part 7 'Grounding')."""
import io, os, sys, time
import numpy as np
from PIL import Image
from grove_common import *
GD_DIR = os.path.join(G, 'tools', 'GroundingDINO'); sys.path.insert(0, GD_DIR)
GD_CFG = os.path.join(GD_DIR, 'groundingdino', 'config', 'GroundingDINO_SwinT_OGC.py')
GD_W = os.path.join(G, 'tools', 'groundingdino_swint_ogc.pth')
BOX_T, TEXT_T, NMS_T, KEEP = 0.35, 0.25, 0.5, 5
DETR_T, SIM_T = 0.5, 0.25

class Grounder:
    def __init__(self, device=None):
        import torch, torchvision, open_clip
        from transformers import DetrForObjectDetection, DetrImageProcessor
        from groundingdino.util.slconfig import SLConfig
        from groundingdino.models import build_model
        from groundingdino.util.utils import clean_state_dict
        import groundingdino.datasets.transforms as T
        self.torch, self.tv = torch, torchvision
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        try:
            from groundingdino import _C  # noqa: F401
            self.gd_ext = True
        except Exception: self.gd_ext = False
        self.gd_device = self.device if (self.device == 'cpu' or self.gd_ext) else 'cpu'
        args = SLConfig.fromfile(GD_CFG); args.device = self.gd_device
        self.gd = build_model(args); ck = torch.load(GD_W, map_location='cpu', weights_only=False)
        self.gd.load_state_dict(clean_state_dict(ck['model']), strict=False); self.gd.eval().to(self.gd_device)
        self.gd_tf = T.Compose([T.RandomResize([800], max_size=1333), T.ToTensor(), T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
        from groundingdino.util.utils import get_phrases_from_posmap
        self.posmap = get_phrases_from_posmap
        self.detr_p = DetrImageProcessor.from_pretrained('facebook/detr-resnet-50')
        self.detr = DetrForObjectDetection.from_pretrained('facebook/detr-resnet-50', use_pretrained_backbone=False).eval().to(self.device)
        self.clip, _, self.clip_pre = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai', device=self.device, force_quick_gelu=True); self.clip.eval()
        self.clip_tok = open_clip.get_tokenizer('ViT-B-32'); self._temb = {}
        log('Grounder ready: device %s, GroundingDINO on %s (CUDA extension %s)' % (self.device, self.gd_device, self.gd_ext))
    def info(self):
        import torch, transformers, open_clip
        return {'device': self.device, 'groundingdino_device': self.gd_device, 'groundingdino_cuda_extension': self.gd_ext, 'torch': torch.__version__,
                'transformers': transformers.__version__, 'open_clip': open_clip.__version__, 'gd_config': 'GroundingDINO_SwinT_OGC', 'gd_weights_sha256': sha256_file(GD_W)}
    def gdino(self, pil, phrase):
        torch = self.torch; W, H = pil.size; x, _ = self.gd_tf(pil, None)
        cap = phrase.lower().strip(); cap = cap if cap.endswith('.') else cap + '.'
        with torch.no_grad(): o = self.gd(x[None].to(self.gd_device), captions=[cap])
        lg = o['pred_logits'].sigmoid()[0].cpu(); bx = o['pred_boxes'][0].cpu()
        keep = lg.max(1)[0] > BOX_T; lg, bx = lg[keep], bx[keep]
        if not len(bx): return []
        xyxy = torch.stack([(bx[:, 0] - bx[:, 2] / 2) * W, (bx[:, 1] - bx[:, 3] / 2) * H, (bx[:, 0] + bx[:, 2] / 2) * W, (bx[:, 1] + bx[:, 3] / 2) * H], 1)
        sc = lg.max(1)[0]; k = self.tv.ops.nms(xyxy, sc, NMS_T)[:KEEP]
        tok = self.gd.tokenizer(cap); out = []
        for i in k.tolist():
            lab = self.posmap(lg[i] > TEXT_T, tok, self.gd.tokenizer).replace('.', '').strip()
            b = xyxy[i].tolist(); b = [max(0.0, b[0]), max(0.0, b[1]), min(float(W), b[2]), min(float(H), b[3])]
            out.append({'box': [round(v, 2) for v in b], 'logit': round(float(sc[i]), 5), 'label': lab})
        return out
    def detr_dets(self, pil):
        torch = self.torch; inp = self.detr_p(images=pil, return_tensors='pt').to(self.device)
        with torch.no_grad(): o = self.detr(**inp)
        r = self.detr_p.post_process_object_detection(o, target_sizes=[(pil.size[1], pil.size[0])], threshold=DETR_T)[0]
        return [{'box': [round(float(v), 2) for v in b], 'score': round(float(s), 5), 'label': self.detr.config.id2label[int(l)]}
                for s, l, b in zip(r['scores'].cpu(), r['labels'].cpu(), r['boxes'].cpu())]
    def temb(self, t):
        if t not in self._temb:
            with self.torch.no_grad():
                e = self.clip.encode_text(self.clip_tok([t]).to(self.device)); self._temb[t] = (e / e.norm(dim=-1, keepdim=True))[0].cpu().numpy()
        return self._temb[t]
    def text_sim(self, a, b): return float(np.dot(self.temb(a), self.temb(b)))
    def fallback(self, dets, phrase):
        best = None
        for d in dets:
            s = self.text_sim(d['label'], phrase)
            if s >= SIM_T and (best is None or s > best['similarity'] or (s == best['similarity'] and d['score'] > best['score'])): best = dict(d, similarity=round(s, 5))
        return best
    def crop_sim(self, pil, box, phrase):
        x1, y1, x2, y2 = [int(round(v)) for v in box]
        if x2 - x1 < 2 or y2 - y1 < 2: return None
        im = self.clip_pre(pil.crop((x1, y1, x2, y2))).unsqueeze(0).to(self.device)
        with self.torch.no_grad(): e = self.clip.encode_image(im); e = (e / e.norm(dim=-1, keepdim=True))[0].cpu().numpy()
        return float(np.dot(e, self.temb(phrase)))
    def close(self):
        for a in ('gd', 'detr', 'clip'): setattr(self, a, None)
        import gc as _gc; _gc.collect()
        if self.torch.cuda.is_available(): self.torch.cuda.empty_cache()
def pil_from_item(it):
    import grove_calls as gcl, base64
    d = gcl.load_item(it); return Image.open(io.BytesIO(base64.b64decode(d['b64']))).convert('RGB'), d['sha']
