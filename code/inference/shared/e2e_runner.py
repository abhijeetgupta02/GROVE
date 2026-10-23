"""
Generic End-to-End VLM Experiment Runner
==========================================
Single-pass: VLM sees image -> outputs hazards directly (no GroundingDINO/DETR).
Used by exp02 (Gemma3:12B), exp03 (Qwen3.5:4B), exp04 (Qwen3.5:9B direct).

This is imported by each experiment's run_experiment.py with its specific model config.
"""
import os
import sys
import re
import json
import time
import traceback
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import config
from shared.vlm_caller import ollama_chat, gpu_mem_mb, gpu_mem_peak_mb, reset_gpu_peak
from shared.data_schema import new_result_record, append_jsonl, get_processed_ids, export_to_excel
from shared.hazard_taxonomy import canonicalize_hazards, labels_from_hazards

# ── Drawing ─────────────────────────────────────────────────────────────────
BOX_COLORS = [(239,68,68),(249,115,22),(234,179,8),(168,85,247),(6,182,212),(34,197,94)]


def _parse_bbox_xyxy(raw_bbox, width, height):
    """Parse bbox text into clamped integer [x1, y1, x2, y2] in pixel space."""
    if not raw_bbox:
        return None

    nums = re.findall(r"-?\d+(?:\.\d+)?", raw_bbox)
    if len(nums) < 4:
        return None

    vals = [float(v) for v in nums[:4]]

    # Support normalized coordinates in [0,1] and percentages.
    if "%" in raw_bbox:
        vals = [vals[0] * width / 100.0, vals[1] * height / 100.0,
                vals[2] * width / 100.0, vals[3] * height / 100.0]
    elif max(vals) <= 1.0 and min(vals) >= 0.0:
        vals = [vals[0] * width, vals[1] * height, vals[2] * width, vals[3] * height]

    x1, y1, x2, y2 = vals
    x1, x2 = sorted([x1, x2])
    y1, y2 = sorted([y1, y2])

    x1 = int(max(0, min(width - 1, round(x1))))
    x2 = int(max(0, min(width - 1, round(x2))))
    y1 = int(max(0, min(height - 1, round(y1))))
    y2 = int(max(0, min(height - 1, round(y2))))

    if x2 <= x1 or y2 <= y1:
        return None
    return [x1, y1, x2, y2]


def _extract_bbox_list_from_followup(raw_resp, width, height, n_hazards):
    """Parse follow-up response lines: Hazard N BBox: [x1, y1, x2, y2]."""
    boxes = [None] * n_hazards
    matches = re.findall(
        r"Hazard\s*(\d+)\s*BBox\s*:\s*(.*?)(?=\n|$)",
        raw_resp,
        flags=re.IGNORECASE,
    )
    for idx_s, raw_box in matches:
        idx = int(idx_s) - 1
        if 0 <= idx < n_hazards:
            boxes[idx] = _parse_bbox_xyxy(raw_box, width, height)
    return boxes

def _get_font(size=18):
    for name in ["arialbd.ttf","arial.ttf","DejaVuSans-Bold.ttf"]:
        try: return ImageFont.truetype(name, size)
        except: continue
    return ImageFont.load_default()

FONT_BOX = _get_font(18)
FONT_NUM = _get_font(22)


def draw_annotated_image(image_path, hazards, save_path, exp_label="E2E"):
    try:
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        for idx, hz in enumerate(hazards):
            box = hz.get("bbox_xyxy")
            if not box: continue
            x1,y1,x2,y2 = box
            color = BOX_COLORS[idx % len(BOX_COLORS)]
            num = str(idx+1)
            for w in range(4):
                draw.rectangle([x1-w,y1-w,x2+w,y2+w], outline=color)
            cr = 16; cx,cy = x1+cr+4, y1+cr+4
            draw.ellipse([cx-cr-2,cy-cr-2,cx+cr+2,cy+cr+2], fill=(0,0,0))
            draw.ellipse([cx-cr,cy-cr,cx+cr,cy+cr], fill=color, outline=(255,255,255))
            bbox = FONT_NUM.getbbox(num)
            tw,th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            draw.text((cx-tw//2, cy-th//2-2), num, fill=(255,255,255), font=FONT_NUM)
            label = hz.get("hazard","Unknown")[:50]
            conf = hz.get("bbox_confidence")
            conf_str = f" ({conf:.2f})" if conf else ""
            draw.text((x1, max(0,y1-20)), f"{num}.{conf_str} {label}", fill=color, font=FONT_BOX)
        n_grounded = len([h for h in hazards if h.get("bbox_xyxy")])
        legend_y = img.size[1] - 25
        draw.rectangle([0,legend_y-5,img.size[0],img.size[1]], fill=(0,0,0))
        draw.text((10,legend_y-2), f"{exp_label} | {n_grounded}/{len(hazards)} grounded", fill=(255,255,255), font=FONT_BOX)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        img.save(save_path, format="JPEG", quality=92)
        return save_path
    except Exception as e:
        print(f"    Annotated save failed: {e}")
        return None


# ── Parsing (same format as modular) ────────────────────────────────────────
def parse_hazards_e2e(raw_resp, image_size=None):
    """Parse hazard blocks and optional native bbox lines."""
    width, height = image_size if image_size else (None, None)
    blocks = re.findall(
        r"Hazard:\s*(.*?)\s*\nCategory:\s*(.*?)\s*\nRisk Level:\s*(.*?)\s*\n(?:BBox\s*:\s*(.*?)\s*\n)?Mitigation:\s*(.*?)(?=\n\s*\n|\nHazard:|\Z)",
        raw_resp, re.DOTALL | re.IGNORECASE,
    )
    hazards = []
    for name, cat, risk, bbox_raw, mit in blocks:
        bbox = _parse_bbox_xyxy(bbox_raw, width, height) if (bbox_raw and width and height) else None
        hazards.append({
            "hazard": name.strip(), "category": cat.strip(),
            "risk_level": risk.strip(), "mitigation": mit.strip(),
            "bbox_xyxy": bbox, "bbox_confidence": None,
            "grounding_source": "LLM-native" if bbox else None,
            "bbox_area_px": None, "bbox_area_pct": None,
        })
    if len(hazards) == 1:
        h = hazards[0]["hazard"].upper().replace("_"," ").strip()
        cat = hazards[0]["category"].upper().strip()
        risk = hazards[0]["risk_level"].upper().strip()
        if h in ["NO HAZARD","NO_HAZARD","NONE","COMPLIANT"] or (cat == "COMPLIANT" and risk in ["NONE", "LOW"]):
            return []
    return hazards


def validate_structured_output(hazards):
    valid_cat = sum(1 for h in hazards if h.get("canonical_category") in config.CANONICAL_HAZARD_CATEGORIES)
    valid_risk = sum(1 for h in hazards if h["risk_level"].lower().strip() in config.VALID_RISK_LEVELS)
    valid_mit = sum(1 for h in hazards if len(h["mitigation"].strip()) > 5)
    n = max(len(hazards), 1)
    return valid_cat, valid_risk, valid_mit, round((valid_cat+valid_risk+valid_mit)/(n*3)*100, 1)


# ── Single-pass analysis ────────────────────────────────────────────────────
def analyze_one_image_e2e(image_path, model_tag, experiment_id, run_number=1,
                          gpu_delay=7, annotated_dir=None):
    """
    End-to-end single-pass: VLM sees image + prompt -> outputs hazards.
    No GroundingDINO, no DETR, no separate captioning step.
    """
    gpu_delay = max(gpu_delay, config.MIN_GPU_COOLDOWN_SECONDS)
    rec = new_result_record(image_path, experiment_id, model_tag, run_number)

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
    tmp_jpg = os.path.join(tempfile.gettempdir(), f"e2e_{uuid.uuid4().hex}.jpg")
    img.save(tmp_jpg, format="JPEG", quality=95)

    total_t0 = time.time()
    reset_gpu_peak()
    rec["gpu_mem_before_mb"] = gpu_mem_mb()

    try:
        # Single prompt: analyze image for OSHA violations directly
        prompt = (
            "You are an OSHA construction safety inspector. Analyze this image for safety violations.\n\n"
            f"Image size: {img.size[0]}x{img.size[1]} pixels.\n"
            "Use exactly one of these seven hazard categories for each hazard:\n"
            "- Fall Hazard\n"
            "- Struck-By Hazard\n"
            "- Electrocution Hazard\n"
            "- Caught-In/Between Hazard\n"
            "- PPE Violation\n"
            "- Housekeeping/Storage\n"
            "- Other\n\n"
            "Rules:\n"
            "- Flag ONLY visible violations (missing PPE, unguarded edges, unsafe equipment use, poor housekeeping, electrical exposure)\n"
            "- Normal construction activity with proper safety measures = COMPLIANT\n"
            "- Workers with correct PPE for their task = COMPLIANT\n"
            "- Guardrails, barriers, and safety signage = protective, not hazardous\n\n"
            "If COMPLIANT, respond EXACTLY:\n"
            "Hazard: NO_HAZARD\nCategory: COMPLIANT\nRisk Level: NONE\nMitigation: Scene appears compliant.\n\n"
            "If violations found, list up to 3 in this exact structure:\n"
            "Hazard: [specific violation]\nCategory: [one of the seven categories above]\nRisk Level: [High/Medium/Low]\nMitigation: [action needed]\n\n"
            "Also include one line before Mitigation for each hazard:\n"
            "BBox: [x1, y1, x2, y2]  (integer pixel coordinates in original image size)\n\n"
            "Only output hazard blocks or NO_HAZARD. Nothing else."
        )

        hz_t0 = time.time()
        msg = [{"role": "user", "content": prompt, "images": [tmp_jpg]}]
        raw_resp, elapsed, retries = ollama_chat(
            model_tag, msg, temperature=config.OLLAMA_TEMPERATURE,
            num_ctx=config.OLLAMA_NUM_CTX, num_predict=config.OLLAMA_NUM_PREDICT,
            gpu_delay=gpu_delay,
        )
        rec["raw_vlm_response"] = raw_resp
        rec["hazard_analysis_time_sec"] = round(time.time() - hz_t0, 2)
        rec["retry_count"] = retries

        # No separate caption step in e2e, but record the raw response length
        rec["caption_text"] = None
        rec["caption_word_count"] = len(raw_resp.split())

        hazards = canonicalize_hazards(parse_hazards_e2e(raw_resp, image_size=img.size))[:config.MAX_HAZARDS_PER_IMAGE]

        # If hazards are present but no coordinates were returned, ask once for coordinates only.
        if hazards and not any(h.get("bbox_xyxy") for h in hazards):
            bbox_prompt = (
                f"Image size is {img.size[0]}x{img.size[1]} pixels.\n"
                "For the hazards below, return ONLY coordinates in this exact format:\n"
                "Hazard 1 BBox: [x1, y1, x2, y2]\n"
                "Hazard 2 BBox: [x1, y1, x2, y2]\n"
                "...\n"
                "Use integer pixel coordinates and include all hazards.\n\n"
                "Hazards:\n" + "\n".join([f"{i+1}. {h['hazard']}" for i, h in enumerate(hazards)])
            )
            try:
                bbox_resp, _, _ = ollama_chat(
                    model_tag,
                    [{"role": "user", "content": bbox_prompt, "images": [tmp_jpg]}],
                    temperature=0.0,
                    num_ctx=config.OLLAMA_NUM_CTX,
                    num_predict=max(256, config.OLLAMA_NUM_PREDICT // 2),
                    gpu_delay=gpu_delay,
                )
                parsed_boxes = _extract_bbox_list_from_followup(bbox_resp, img.size[0], img.size[1], len(hazards))
                for i, box in enumerate(parsed_boxes):
                    if box:
                        hazards[i]["bbox_xyxy"] = box
                        hazards[i]["grounding_source"] = "LLM-native"
            except Exception as e:
                print(f"    BBox follow-up skipped: {e}")

        for h in hazards:
            box = h.get("bbox_xyxy")
            if box:
                x1, y1, x2, y2 = box
                area = max(0, (x2 - x1) * (y2 - y1))
                h["bbox_area_px"] = area
                h["bbox_area_pct"] = round((area / float(img.size[0] * img.size[1])) * 100.0, 3)

        rec["n_hazards_pred"] = len(hazards)
        rec["is_safe_pred"] = len(hazards) == 0
        rec["canonical_hazard_label"] = labels_from_hazards(hazards, display=False)
        rec["hazard_label"] = labels_from_hazards(hazards, display=True)

        if len(hazards) > 0:
            vc, vr, vm, compliance = validate_structured_output(hazards)
            rec["has_valid_category"] = vc == len(hazards)
            rec["has_valid_risk_level"] = vr == len(hazards)
            rec["has_valid_mitigation"] = vm == len(hazards)
            rec["structured_compliance_pct"] = compliance

        n_boxes = sum(1 for h in hazards if h.get("bbox_xyxy"))
        rec["n_boxes_pred"] = n_boxes
        rec["grounding_coverage_pct"] = round((n_boxes / max(len(hazards), 1)) * 100.0, 1)
        rec["hazards_json"] = json.dumps(hazards, ensure_ascii=False)

        # Save an annotated copy for traceability during review.
        if annotated_dir:
            base = os.path.splitext(os.path.basename(image_path))[0]
            ann_path = os.path.join(annotated_dir, f"{base}_annotated.jpg")
            rec["annotated_image_path"] = draw_annotated_image(
                image_path, hazards, ann_path, exp_label=experiment_id.upper()
            )

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


# ── Generic main loop ───────────────────────────────────────────────────────
def run_e2e_experiment(model_key, start=1, end=9999, run=1, delay=7, resume=False,
                       image_dir=None, experiment_suffix="", gt_json_path=None):
    """
    Run an end-to-end experiment for a given model key from config.MODELS.
    Called by each exp folder's run_experiment.py.
    """
    model_cfg = config.MODELS[model_key]
    delay = max(delay, config.MIN_GPU_COOLDOWN_SECONDS)
    if not config.model_supports_images(model_key):
        raise SystemExit(
            f"{model_key} is cataloged as {model_cfg.get('type')} and does not support image input. "
            "Do not run it through the end-to-end VLM image runner."
        )

    model_tag = model_cfg["ollama_tag"]
    experiment_id = f"exp_{model_key}"
    if experiment_suffix:
        clean_suffix = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in experiment_suffix)
        experiment_id = f"{experiment_id}_{clean_suffix}"
    image_dir = image_dir or config.IMAGE_DIR
    if gt_json_path is None and os.path.normcase(os.path.abspath(image_dir)) == os.path.normcase(os.path.abspath(config.IMAGE_DIR)):
        gt_json_path = config.GT_COCO_JSON

    # Results go into each experiment's own folder
    exp_dir = os.path.join(config.CODE_DIR, experiment_id)
    results_dir = os.path.join(exp_dir, "results")
    annotated_dir = os.path.join(results_dir, f"annotated_run{run}")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(annotated_dir, exist_ok=True)

    run_tag = f"run{run}"
    jsonl_path = os.path.join(results_dir, f"{experiment_id}_{run_tag}.jsonl")
    excel_path = os.path.join(results_dir, f"{experiment_id}_{run_tag}.xlsx")

    print("=" * 60)
    print(f"  {experiment_id.upper()}: {model_cfg['description']}")
    print(f"  Model: {model_tag}  |  Run: {run}  |  Delay: {delay}s")
    print(f"  Image dir: {image_dir}")
    print(f"  Images: {start} to {end}")
    print(f"  Output: {jsonl_path}")
    print("=" * 60)

    all_images = config.get_image_list(image_dir=image_dir)
    if not all_images:
        print(f"ERROR: No images found in {image_dir}")
        return

    images = [img for img in all_images
              if start <= int(config.image_id_from_name(os.path.basename(img))) <= end]
    print(f"\nImages to process: {len(images)}")

    processed = set()
    if resume:
        processed = get_processed_ids(jsonl_path)
        print(f"Already done: {len(processed)}")

    success = 0; errors = 0
    for i, img_path in enumerate(images):
        img_id = config.image_id_from_name(os.path.basename(img_path))
        if resume and (img_id, run) in processed:
            continue

        print(f"\n[{i+1}/{len(images)}] {os.path.basename(img_path)}")
        try:
            rec = analyze_one_image_e2e(
                img_path, model_tag, experiment_id,
                run_number=run, gpu_delay=delay, annotated_dir=annotated_dir
            )
            append_jsonl(jsonl_path, rec)
            status = "SAFE" if rec["is_safe_pred"] else f"{rec['n_hazards_pred']} hazards"
            timing = f"{rec['total_inference_time_sec']}s"
            print(f"  {status} | {timing}")
            if rec["error"]:
                print(f"  ERROR: {rec['error']}"); errors += 1
            else:
                success += 1
        except Exception as e:
            print(f"  FATAL: {e}"); errors += 1

        if i < len(images) - 1:
            print(f"  GPU cooldown {delay}s before next image...")
            time.sleep(delay)

    print(f"\n{'='*60}")
    print(f"  DONE: {success} ok, {errors} errors")
    category_review_dir = os.path.join(results_dir, f"category_review_run{run}")
    export_to_excel(
        jsonl_path,
        excel_path,
        config.EXCEL_SUMMARY_COLUMNS,
        gt_json_path=gt_json_path if gt_json_path and os.path.exists(gt_json_path) else None,
        category_review_dir=category_review_dir,
    )
    print(f"{'='*60}\n")
    if errors > 0:
        raise SystemExit(1)
