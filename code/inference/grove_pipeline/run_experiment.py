"""
Experiment 01 - Modular Glass-Box Pipeline
============================================
Qwen3.5:9B (caption + hazard analysis) -> GroundingDINO -> DETR/CLIP fallback

Usage (from code/inference):
    python grove_pipeline/run_experiment.py --start 1 --end 5 --delay 7
    python grove_pipeline/run_experiment.py --run 1 --resume
"""
import os
import sys
import re
import json
import time
import argparse
import traceback
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ── Fix imports: add code_files to path ─────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CODE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, CODE_DIR)

import config
from shared.vlm_caller import ollama_chat, gpu_mem_mb, gpu_mem_peak_mb, reset_gpu_peak
from shared.data_schema import new_result_record, append_jsonl, get_processed_ids, export_to_excel
from shared.datasets import list_construction_ppe_images, select_by_ordinal

# ── Add GroundingDINO to path ───────────────────────────────────────────────
if os.path.exists(config.GDINO_REPO):
    sys.path.insert(0, config.GDINO_REPO)

import torch

# ── Annotated image colors & font ───────────────────────────────────────────
BOX_COLORS = [
    (239, 68, 68),    # red
    (249, 115, 22),   # orange
    (234, 179, 8),    # yellow
    (168, 85, 247),   # purple
    (6, 182, 212),    # cyan
    (34, 197, 94),    # green
]

def _get_font(size=18):
    for name in ["arialbd.ttf", "arial.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

FONT_BOX = _get_font(18)
FONT_NUM = _get_font(22)


def draw_annotated_image(image_path, hazards, save_path):
    """
    Draw numbered bounding boxes on the image and save.
    Each hazard gets a colored box + circled number + short label.
    Returns the save_path if successful, None otherwise.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)

        for idx, hz in enumerate(hazards):
            box = hz.get("bbox_xyxy")
            if not box:
                continue

            x1, y1, x2, y2 = box
            color = BOX_COLORS[idx % len(BOX_COLORS)]
            num = str(idx + 1)

            # Draw thick box border
            for w in range(4):
                draw.rectangle([x1 - w, y1 - w, x2 + w, y2 + w], outline=color)

            # Draw numbered circle in top-left corner
            circle_r = 16
            cx, cy = x1 + circle_r + 4, y1 + circle_r + 4
            # Shadow
            draw.ellipse([cx - circle_r - 2, cy - circle_r - 2,
                          cx + circle_r + 2, cy + circle_r + 2], fill=(0, 0, 0))
            # Filled circle
            draw.ellipse([cx - circle_r, cy - circle_r,
                          cx + circle_r, cy + circle_r], fill=color, outline=(255, 255, 255))
            # Number
            bbox = FONT_NUM.getbbox(num)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((cx - tw // 2, cy - th // 2 - 2), num, fill=(255, 255, 255), font=FONT_NUM)

            # Short label below the number circle
            label = hz.get("hazard", "Unknown")[:50]
            src = hz.get("grounding_source", "")
            src_short = "GD" if "GroundingDINO" in (src or "") else "DC" if "DETR" in (src or "") else "?"
            conf = hz.get("bbox_confidence")
            conf_str = f" ({conf:.2f})" if conf else ""
            tag = f"{num}. [{src_short}{conf_str}] {label}"
            draw.text((x1, max(0, y1 - 20)), tag, fill=color, font=FONT_BOX)

        # Add legend at bottom
        legend_y = img.size[1] - 25
        draw.rectangle([0, legend_y - 5, img.size[0], img.size[1]], fill=(0, 0, 0, 180))
        legend = f"EXP01 Modular | {len([h for h in hazards if h.get('bbox_xyxy')])} grounded / {len(hazards)} hazards"
        draw.text((10, legend_y - 2), legend, fill=(255, 255, 255), font=FONT_BOX)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        img.save(save_path, format="JPEG", quality=92)
        return save_path
    except Exception as e:
        print(f"    Annotated image save failed: {e}")
        return None


# ── Lazy model loading ──────────────────────────────────────────────────────
_models_loaded = False
_gdino = None
_processor_detr = None
_model_detr = None
_clip_model = None
_gdino_available = False
_detr_available = False
_clip_available = False


def _load_models():
    global _models_loaded, _gdino, _processor_detr, _model_detr, _clip_model
    global _gdino_available, _detr_available, _clip_available
    if _models_loaded:
        return
    DEVICE = config.GPU_DEVICE

    # GroundingDINO
    try:
        from groundingdino.util.inference import load_model as load_gdino_model
        print("Loading GroundingDINO...")
        _gdino = load_gdino_model(config.GDINO_CONFIG, config.GDINO_WEIGHTS, device=DEVICE)
        _gdino_available = True
        print("  GroundingDINO loaded OK")
    except Exception as e:
        print(f"  GroundingDINO FAILED: {e}")

    # DETR
    try:
        from transformers import DetrImageProcessor, DetrForObjectDetection
        print("Loading DETR...")
        _processor_detr = DetrImageProcessor.from_pretrained(config.DETR_MODEL_ID)
        _model_detr = DetrForObjectDetection.from_pretrained(config.DETR_MODEL_ID)
        _model_detr.to(DEVICE)
        _detr_available = True
        print("  DETR loaded OK")
    except Exception as e:
        print(f"  DETR FAILED: {e}")

    # OpenCLIP
    try:
        import open_clip
        print("Loading OpenCLIP...")
        _clip_model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
        _clip_model.to(DEVICE).eval()
        _clip_available = True
        print("  OpenCLIP loaded OK")
    except Exception as e:
        print(f"  OpenCLIP FAILED: {e}")

    _models_loaded = True
    print(f"\nModels: GDINO={_gdino_available}, DETR={_detr_available}, CLIP={_clip_available}")
    print(f"GPU Memory: {gpu_mem_mb()} MB\n")


# ── Grounding ───────────────────────────────────────────────────────────────
def gdino_ground(image_pil, phrase):
    global _gdino_available
    if not _gdino_available:
        return None, None
    import groundingdino.datasets.transforms as T
    from groundingdino.util.inference import predict as gdino_predict
    w, h = image_pil.size
    transform = T.Compose([
        T.RandomResize([800], max_size=1333),
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    img_tensor, _ = transform(image_pil, None)
    try:
        boxes, logits, _ = gdino_predict(
            model=_gdino, image=img_tensor, caption=phrase,
            box_threshold=config.GDINO_BOX_THRESHOLD,
            text_threshold=config.GDINO_TEXT_THRESHOLD,
            device=config.GPU_DEVICE,
        )
        if len(boxes) == 0:
            return None, None
        best = torch.argmax(logits).item()
        cx, cy, bw, bh = boxes[best].cpu().numpy()
        x1, y1 = int((cx - bw/2) * w), int((cy - bh/2) * h)
        x2, y2 = int((cx + bw/2) * w), int((cy + bh/2) * h)
        return [x1, y1, x2, y2], round(float(logits[best].item()), 4)
    except Exception as e:
        msg = str(e)
        if "_C" in msg and "not defined" in msg:
            print("    GDINO custom ops unavailable; disabling GDINO for this run.")
            _gdino_available = False
        else:
            print(f"    GDINO error for '{phrase}': {e}")
        return None, None


def detr_clip_ground(image_pil, phrase):
    if not (_detr_available and _clip_available):
        return None, None, None
    import open_clip
    DEVICE = config.GPU_DEVICE
    try:
        inputs = _processor_detr(images=image_pil, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            outputs = _model_detr(**inputs)
        target_sizes = torch.tensor([image_pil.size[::-1]], device=DEVICE)
        results = _processor_detr.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=config.DETR_THRESHOLD
        )[0]
        if "labels" not in results or len(results["labels"]) == 0:
            return None, None, None
        labels = [_model_detr.config.id2label[i.item()] for i in results["labels"]]
        boxes = results["boxes"].cpu()
        scores = results["scores"].cpu()

        label_tokens = open_clip.tokenize(labels).to(DEVICE)
        hazard_token = open_clip.tokenize([phrase]).to(DEVICE)
        with torch.no_grad():
            label_feats = _clip_model.encode_text(label_tokens)
            label_feats /= label_feats.norm(dim=-1, keepdim=True)
            hazard_feat = _clip_model.encode_text(hazard_token)
            hazard_feat /= hazard_feat.norm(dim=-1, keepdim=True)
        sims = (label_feats @ hazard_feat.T).squeeze(1)
        best = torch.argmax(sims).item()
        best_sim = float(sims[best].item())
        if best_sim < config.CLIP_SIMILARITY_MIN:
            return None, None, None
        box = [int(c) for c in boxes[best].tolist()]
        score = round(float(scores[best].item()), 4)
        src = f"DETR+CLIP (Sim={best_sim:.2f}, Match='{labels[best]}')"
        return box, score, src
    except Exception:
        return None, None, None


# ── Parsing ─────────────────────────────────────────────────────────────────
def parse_hazards(raw_resp):
    blocks = re.findall(
        r"Hazard:\s*(.*?)\s*\nCategory:\s*(.*?)\s*\nRisk Level:\s*(.*?)\s*\nMitigation:\s*(.*?)(?=\n\s*\n|\nHazard:|\Z)",
        raw_resp, re.DOTALL | re.IGNORECASE,
    )
    hazards = []
    for name, cat, risk, mit in blocks:
        hazards.append({
            "hazard": name.strip(), "category": cat.strip(),
            "risk_level": risk.strip(), "mitigation": mit.strip(),
            "bbox_xyxy": None, "bbox_confidence": None,
            "grounding_source": None, "bbox_area_px": None, "bbox_area_pct": None,
        })
    if len(hazards) == 1:
        h = hazards[0]["hazard"].upper().replace("_", " ").strip()
        if h in ["NO HAZARD", "NO_HAZARD", "NONE", "COMPLIANT"]:
            return []
    return hazards


def validate_structured_output(hazards):
    valid_cat = sum(1 for h in hazards if h["category"].lower().strip() in config.VALID_OSHA_CATEGORIES)
    valid_risk = sum(1 for h in hazards if h["risk_level"].lower().strip() in config.VALID_RISK_LEVELS)
    valid_mit = sum(1 for h in hazards if len(h["mitigation"].strip()) > 5)
    n = max(len(hazards), 1)
    return valid_cat, valid_risk, valid_mit, round((valid_cat + valid_risk + valid_mit) / (n * 3) * 100, 1)


def extract_caption_phrases(caption, max_phrases=10):
    if not caption:
        return []
    stop = {"the","a","an","and","or","to","of","in","on","at","with","for","is","are",
            "this","that","it","as","by","from","be","has","have","had","was","were","into"}
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]+", caption.lower())
    words = [w for w in words if w not in stop and len(w) > 2]
    safety_kw = {"worker","workers","ladder","scaffold","roof","edge","harness","guardrail",
                 "helmet","vest","gloves","excavation","trench","crane","forklift","truck",
                 "wires","electrical","panel","barrier","cone","debris","material"}
    phrases = [w for w in words if w in safety_kw or w.endswith("ing")]
    for i in range(len(words) - 1):
        bi = f"{words[i]} {words[i+1]}"
        if any(k in bi for k in ["hard hat","safety vest","power line","roof edge","guard rail"]):
            phrases.append(bi)
    seen = set()
    unique = []
    for p in phrases:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique[:max_phrases]


# ── Main per-image ──────────────────────────────────────────────────────────
def analyze_one_image(image_path, run_number=1, gpu_delay=7, annotated_dir=None):
    MODEL_TAG = config.MODELS["modular_qwen9b"]["ollama_tag"]
    EXP_ID = "exp01_modular_qwen"
    rec = new_result_record(image_path, EXP_ID, MODEL_TAG, run_number)

    try:
        img = Image.open(image_path).convert("RGB")
        rec["image_width_px"] = img.size[0]
        rec["image_height_px"] = img.size[1]
        rec["image_format"] = os.path.splitext(image_path)[1].lstrip(".").lower()
        rec["image_filesize_kb"] = round(os.path.getsize(image_path) / 1024, 1)
    except Exception as e:
        rec["error"] = f"Image load failed: {e}"
        return rec

    import tempfile, uuid
    tmp_jpg = os.path.join(tempfile.gettempdir(), f"exp01_{uuid.uuid4().hex}.jpg")
    img.save(tmp_jpg, format="JPEG", quality=95)

    total_t0 = time.time()
    reset_gpu_peak()
    rec["gpu_mem_before_mb"] = gpu_mem_mb()

    try:
        # STEP 1: Caption
        cap_t0 = time.time()
        caption_msg = [{
            "role": "user",
            "content": (
                "Describe this construction site image in detail. Include:\n"
                "- What workers are doing and their positions\n"
                "- All visible safety equipment (hard hats, vests, harnesses, guardrails, barriers, safety nets, signage)\n"
                "- Site conditions (cleanliness, material storage, weather)\n"
                "- Any equipment or machinery visible\n"
                "Be purely descriptive and factual. Do not make safety assessments or judgments."
            ),
            "images": [tmp_jpg],
        }]
        caption, cap_elapsed, cap_retries = ollama_chat(
            MODEL_TAG, caption_msg, temperature=config.OLLAMA_TEMPERATURE,
            num_ctx=config.OLLAMA_NUM_CTX, num_predict=config.OLLAMA_NUM_PREDICT, gpu_delay=gpu_delay,
        )
        rec["caption_text"] = caption
        rec["caption_word_count"] = len(caption.split())
        rec["caption_time_sec"] = round(time.time() - cap_t0, 2)

        # STEP 2: Hazard Assessment
        hz_t0 = time.time()
        hazard_prompt = (
            f"Analyze this construction site image for OSHA violations.\n\n"
            f"Scene description: '{caption}'\n\n"
            f"Rules:\n"
            f"- Flag ONLY visible violations (missing PPE, unguarded edges, unsafe equipment use, poor housekeeping, electrical exposure)\n"
            f"- Normal construction activity with proper safety measures = COMPLIANT\n"
            f"- Workers with correct PPE for their task = COMPLIANT\n"
            f"- Guardrails, barriers, and safety signage = protective, not hazardous\n\n"
            f"If COMPLIANT, respond EXACTLY:\n"
            f"Hazard: NO_HAZARD\nCategory: COMPLIANT\nRisk Level: NONE\nMitigation: Scene appears compliant.\n\n"
            f"If violations found, list up to 3:\n"
            f"Hazard: [specific violation]\nCategory: [OSHA category]\nRisk Level: [High/Medium/Low]\nMitigation: [action needed]\n\n"
            f"Only output hazard blocks or NO_HAZARD. Nothing else."
        )
        hazard_msg = [{"role": "user", "content": hazard_prompt, "images": [tmp_jpg]}]
        raw_resp, hz_elapsed, hz_retries = ollama_chat(
            MODEL_TAG, hazard_msg, temperature=config.OLLAMA_TEMPERATURE,
            num_ctx=config.OLLAMA_NUM_CTX, num_predict=config.OLLAMA_NUM_PREDICT, gpu_delay=gpu_delay,
        )
        rec["raw_vlm_response"] = raw_resp
        rec["hazard_analysis_time_sec"] = round(time.time() - hz_t0, 2)
        rec["retry_count"] = cap_retries + hz_retries

        hazards = parse_hazards(raw_resp)
        rec["n_hazards_pred"] = len(hazards)
        rec["is_safe_pred"] = len(hazards) == 0

        if len(hazards) == 0:
            rec["hazards_json"] = "[]"
            rec["total_inference_time_sec"] = round(time.time() - total_t0, 2)
            rec["gpu_mem_after_mb"] = gpu_mem_mb()
            rec["gpu_mem_peak_mb"] = gpu_mem_peak_mb()
            return rec

        # STEP 3: Grounding
        ground_t0 = time.time()
        phrases = extract_caption_phrases(caption)
        path_a_boxes = {}
        for phrase in phrases:
            box, score = gdino_ground(img, phrase)
            if box is None:
                box, score, _ = detr_clip_ground(img, phrase)
            if box is not None:
                path_a_boxes[phrase] = True
        rec["path_a_grounded_phrases"] = json.dumps(sorted(path_a_boxes.keys()))

        img_area = img.size[0] * img.size[1]
        n_boxes = 0; n_gdino = 0; n_detr = 0; n_high = 0; n_med = 0
        for hz in hazards:
            phrase = hz["hazard"]
            box, score = gdino_ground(img, phrase)
            src = "GroundingDINO"
            if box is None:
                box, score, src = detr_clip_ground(img, phrase)
            if box is not None:
                hz["bbox_xyxy"] = box
                hz["bbox_confidence"] = score
                hz["grounding_source"] = src
                box_area = (box[2] - box[0]) * (box[3] - box[1])
                hz["bbox_area_px"] = box_area
                hz["bbox_area_pct"] = round(box_area / img_area * 100, 2) if img_area > 0 else 0
                n_boxes += 1
                if "GroundingDINO" in (src or ""):
                    n_gdino += 1
                else:
                    n_detr += 1
            phrase_tokens = set(re.findall(r"[a-zA-Z]+", phrase.lower()))
            matched = any(len(phrase_tokens & set(re.findall(r"[a-zA-Z]+", k))) >= 1 for k in path_a_boxes)
            if matched:
                hz["confidence"] = "HIGH"; n_high += 1
            else:
                hz["confidence"] = "MEDIUM"; n_med += 1

        rec["grounding_time_sec"] = round(time.time() - ground_t0, 2)
        rec["n_boxes_pred"] = n_boxes
        rec["grounding_coverage_pct"] = round(n_boxes / max(len(hazards), 1) * 100, 1)
        rec["n_gdino_boxes"] = n_gdino
        rec["n_detr_fallback_boxes"] = n_detr
        rec["n_high_confidence"] = n_high
        rec["n_medium_confidence"] = n_med

        vc, vr, vm, compliance = validate_structured_output(hazards)
        rec["has_valid_category"] = vc == len(hazards)
        rec["has_valid_risk_level"] = vr == len(hazards)
        rec["has_valid_mitigation"] = vm == len(hazards)
        rec["structured_compliance_pct"] = compliance
        rec["hazards_json"] = json.dumps(hazards, ensure_ascii=False)

        # STEP 4: Save annotated image with bounding boxes
        if annotated_dir and n_boxes > 0:
            img_id = rec["image_id"]
            ann_filename = f"{img_id}_annotated.jpg"
            ann_path = os.path.join(annotated_dir, ann_filename)
            saved = draw_annotated_image(image_path, hazards, ann_path)
            rec["annotated_image_path"] = saved
        elif annotated_dir and n_boxes == 0:
            rec["annotated_image_path"] = None  # hazards found but none grounded

    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        traceback.print_exc()
    finally:
        try: os.remove(tmp_jpg)
        except: pass

    rec["total_inference_time_sec"] = round(time.time() - total_t0, 2)
    rec["gpu_mem_after_mb"] = gpu_mem_mb()
    rec["gpu_mem_peak_mb"] = gpu_mem_peak_mb()
    rec["timestamp"] = datetime.now().isoformat()
    return rec


# ── Main ────────────────────────────────────────────────────────────────────
def _timestamped_appendix_dir(dataset, split, experiment_id, run):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(
        config.BASE_DIR,
        "appendix_results",
        dataset.replace("-", "_"),
        f"{experiment_id}_{split}_run{run}_{stamp}",
    )


def _select_original_images(start, end, max_images=None):
    images = []
    for img in config.get_image_list():
        try:
            image_num = int(config.image_id_from_name(os.path.basename(img)))
        except ValueError:
            continue
        if start <= image_num <= end:
            images.append(img)
    if max_images is not None:
        images = images[:max_images]
    return images


def _select_dataset_images(dataset, dataset_root, split, start, end, max_images=None):
    if dataset == "original":
        return _select_original_images(start, end, max_images=max_images)
    if dataset == "construction-ppe":
        if not dataset_root:
            raise ValueError("--dataset-root is required when --dataset construction-ppe")
        images = list_construction_ppe_images(dataset_root, split)
        return [str(path) for path in select_by_ordinal(images, start, end, max_images=max_images)]
    raise ValueError(f"Unknown dataset: {dataset}")


def main():
    parser = argparse.ArgumentParser(description="Exp01: Modular Qwen3.5:9B Pipeline")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=9999)
    parser.add_argument("--run", type=int, default=1, choices=[1, 2, 3])
    parser.add_argument("--delay", type=int, default=7)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dataset", choices=["original", "construction-ppe"], default="original")
    parser.add_argument("--dataset-root", default=None)
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--max-images", type=int, default=None)
    args = parser.parse_args()

    if args.output_dir:
        results_dir = os.path.abspath(args.output_dir)
    elif args.dataset == "original":
        results_dir = os.path.join(SCRIPT_DIR, "results")
    else:
        results_dir = _timestamped_appendix_dir(args.dataset, args.split, "exp01_modular_qwen", args.run)
    annotated_dir = os.path.join(results_dir, f"annotated_run{args.run}")

    run_tag = f"run{args.run}"
    jsonl_path = os.path.join(results_dir, f"exp01_{run_tag}.jsonl")
    excel_path = os.path.join(results_dir, f"exp01_{run_tag}.xlsx")
    protect_existing = args.dataset != "original" or args.output_dir is not None
    if protect_existing and not args.resume:
        if os.path.isdir(results_dir) and os.listdir(results_dir):
            raise SystemExit(f"Refusing to write into non-empty appendix output dir without --resume: {results_dir}")
        existing_outputs = [path for path in [jsonl_path, excel_path] if os.path.exists(path)]
        if existing_outputs:
            raise SystemExit(
                "Refusing to overwrite existing appendix outputs without --resume: "
                + ", ".join(existing_outputs)
            )

    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(annotated_dir, exist_ok=True)

    print("=" * 60)
    print(f"  EXP01: Modular Qwen3.5:9B + GroundingDINO + DETR/CLIP")
    print(f"  Run: {args.run}  |  Delay: {args.delay}s")
    print(f"  Dataset: {args.dataset}  |  Split: {args.split}")
    if args.dataset_root:
        print(f"  Dataset root: {args.dataset_root}")
    print(f"  Images: {args.start} to {args.end}" + (f"  |  Max: {args.max_images}" if args.max_images else ""))
    print(f"  Output: {jsonl_path}")
    print(f"  Annotated: {annotated_dir}")
    print("=" * 60)

    images = _select_dataset_images(
        args.dataset,
        args.dataset_root,
        args.split,
        args.start,
        args.end,
        max_images=args.max_images,
    )
    if not images:
        location = args.dataset_root if args.dataset != "original" else config.IMAGE_DIR
        print(f"ERROR: No images found in {location}")
        return
    print(f"\nImages to process: {len(images)}")

    _load_models()

    processed = set()
    if args.resume:
        processed = get_processed_ids(jsonl_path)
        print(f"Already done: {len(processed)}")

    success = 0; errors = 0
    for i, img_path in enumerate(images):
        img_id = config.image_id_from_name(os.path.basename(img_path))
        if args.resume and (img_id, args.run) in processed:
            continue

        print(f"\n[{i+1}/{len(images)}] {os.path.basename(img_path)}")
        try:
            rec = analyze_one_image(img_path, run_number=args.run, gpu_delay=args.delay,
                                    annotated_dir=annotated_dir)
            append_jsonl(jsonl_path, rec)
            status = "SAFE" if rec["is_safe_pred"] else f"{rec['n_hazards_pred']} hazards"
            boxes = f"{rec['n_boxes_pred']} boxes ({rec['grounding_coverage_pct']}%)"
            timing = f"{rec['total_inference_time_sec']}s"
            ann = "IMG" if rec.get("annotated_image_path") else ""
            print(f"  {status} | {boxes} | {timing} {ann}")
            if rec["error"]:
                print(f"  ERROR: {rec['error']}"); errors += 1
            else:
                success += 1
        except Exception as e:
            print(f"  FATAL: {e}"); errors += 1

    print(f"\n{'='*60}")
    print(f"  DONE: {success} ok, {errors} errors")
    ann_count = len([f for f in os.listdir(annotated_dir) if f.endswith(".jpg")])
    print(f"  Annotated images saved: {ann_count} in {annotated_dir}")
    export_to_excel(jsonl_path, excel_path, config.EXCEL_SUMMARY_COLUMNS)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
