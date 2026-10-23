"""
SiteCortex EAAI — Shared Configuration
=======================================
All paths, model configs, and constants in one place.

VISION MODELS ONLY — llama3.2:1b, llama3.3:70b, llama2 are TEXT-ONLY
and cannot process images, so they are excluded.
"""
import os
import re

# ── HARDWARE ────────────────────────────────────────────────────────────────
GPU_DEVICE = "cuda"
GPU_DELAY_SECONDS = 7
MIN_GPU_COOLDOWN_SECONDS = 6

# ── PATHS ───────────────────────────────────────────────────────────────────
# All paths resolve relative to this supplementary package by default and can
# be overridden with environment variables. The bundled 203-image evaluation
# set and its COCO ground truth live under <package>/data/.
_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))          # code/inference
PACKAGE_ROOT = os.environ.get(
    "GROVE_ROOT", os.path.abspath(os.path.join(_THIS_DIR, os.pardir, os.pardir))
)
BASE_DIR       = PACKAGE_ROOT
CODE_DIR       = _THIS_DIR
IMAGE_DIR      = os.environ.get("GROVE_IMAGE_DIR", os.path.join(PACKAGE_ROOT, "data", "images"))
GT_COCO_JSON   = os.environ.get("GROVE_GT_JSON",   os.path.join(PACKAGE_ROOT, "data", "annotations.coco.json"))
PAPER_EVAL_DIR = os.environ.get("GROVE_RESULTS_DIR", os.path.join(PACKAGE_ROOT, "results"))

# ── GROUNDING BACKENDS ───────────────────────────────────────────────────────
# GroundingDINO weights and repository are external (~700 MB) and are NOT
# bundled with this package. To re-run inference, clone GroundingDINO and point
# GROUNDINGDINO_HOME at it (see code/README.md). Evaluation does not need these.
GDINO_HOME     = os.environ.get("GROUNDINGDINO_HOME", "")
GDINO_REPO     = os.path.join(GDINO_HOME, "GroundingDINO") if GDINO_HOME else ""
GDINO_CONFIG   = (os.path.join(GDINO_REPO, "groundingdino", "config",
                               "GroundingDINO_SwinT_OGC.py") if GDINO_REPO else "")
GDINO_WEIGHTS  = os.environ.get(
    "GROUNDINGDINO_WEIGHTS",
    os.path.join(GDINO_HOME, "weights", "groundingdino_swint_ogc.pth") if GDINO_HOME else "",
)
DETR_MODEL_ID  = "facebook/detr-resnet-50"

# ── MODEL REGISTRY ──────────────────────────────────────────────────────────
MODELS = {
    # 1. Modular glass-box pipeline
    "modular_qwen9b": {
        "description": "Modular Glass-Box: Qwen3.5:9B + GroundingDINO + DETR/CLIP",
        "ollama_tag": "qwen3.5:9b",
        "type": "modular",
        "vram_gb": 10,
        "uses_grounding": True,
    },
    # 2+. End-to-end single-pass models (all have vision)
    "e2e_gemma3_12b": {
        "description": "End-to-End: Gemma3:12B",
        "ollama_tag": "gemma3:12b",
        "type": "end_to_end",
        "vram_gb": 10,
    },
    "e2e_gemma3_4b": {
        "description": "End-to-End: Gemma3:4B (lightweight)",
        "ollama_tag": "gemma3:4b",
        "type": "end_to_end",
        "vram_gb": 4,
    },
    "e2e_qwen_9b": {
        "description": "End-to-End: Qwen3.5:9B direct (no grounding pipeline)",
        "ollama_tag": "qwen3.5:9b",
        "type": "end_to_end",
        "vram_gb": 10,
    },
    "e2e_qwen_4b": {
        "description": "End-to-End: Qwen3.5:4B (lightweight)",
        "ollama_tag": "qwen3.5:4b",
        "type": "end_to_end",
        "vram_gb": 4,
    },
    "e2e_qwen_35b": {
        "description": "End-to-End: Qwen3.5:35B (large, high-accuracy)",
        "ollama_tag": "qwen3.5:35b",
        "type": "end_to_end",
        "vram_gb": 24,
    },
    "e2e_llama32_vision_11b": {
        "description": "End-to-End: Llama3.2-Vision:11B",
        "ollama_tag": "llama3.2-vision:11b",
        "type": "end_to_end",
        "family": "llama3.2-vision",
        "campaign": "new_ollama_vision_2026_04",
        "category": "llama_vision",
        "size_gb": 7.8,
        "context_window": "128K",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 12,
        "supports_images": True,
        "source_url": "https://ollama.com/library/llama3.2-vision",
    },
    "e2e_internvl3_5_8b": {
        "description": "End-to-End: InternVL3.5:8B",
        "ollama_tag": "blaifa/InternVL3_5:8b",
        "type": "end_to_end",
        "vram_gb": 8,
    },

    # 2026-04 added Qwen 3.5 vision campaign variants.
    "e2e_qwen35_2b": {
        "description": "End-to-End: Qwen3.5:2B",
        "ollama_tag": "qwen3.5:2b",
        "type": "end_to_end",
        "family": "qwen3.5",
        "campaign": "new_ollama_vision_2026_04",
        "category": "qwen3.5_vision",
        "context_window": "?",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 3,
        "supports_images": True,
        "source_url": "https://ollama.com/library/qwen3.5",
    },
    "e2e_qwen35_4b": {
        "description": "End-to-End: Qwen3.5:4B",
        "ollama_tag": "qwen3.5:4b",
        "type": "end_to_end",
        "family": "qwen3.5",
        "campaign": "new_ollama_vision_2026_04",
        "category": "qwen3.5_vision",
        "context_window": "?",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 4,
        "supports_images": True,
        "source_url": "https://ollama.com/library/qwen3.5",
        "notes": "April rerun folder kept separate from old exp_e2e_qwen_4b baseline.",
    },
    "e2e_qwen35_9b": {
        "description": "End-to-End: Qwen3.5:9B",
        "ollama_tag": "qwen3.5:9b",
        "type": "end_to_end",
        "family": "qwen3.5",
        "campaign": "new_ollama_vision_2026_04",
        "category": "qwen3.5_vision",
        "context_window": "?",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 10,
        "supports_images": True,
        "source_url": "https://ollama.com/library/qwen3.5",
        "notes": "April rerun folder kept separate from old exp_e2e_qwen_9b baseline.",
    },
    "e2e_qwen35_27b": {
        "description": "End-to-End: Qwen3.5:27B",
        "ollama_tag": "qwen3.5:27b",
        "type": "end_to_end",
        "family": "qwen3.5",
        "campaign": "new_ollama_vision_2026_04",
        "category": "qwen3.5_vision",
        "context_window": "?",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 24,
        "supports_images": True,
        "source_url": "https://ollama.com/library/qwen3.5",
    },

    # 2026-04 new Ollama vision campaign: Qwen 3.6
    "e2e_qwen36_latest": {
        "description": "End-to-End: Qwen3.6 latest",
        "ollama_tag": "qwen3.6:latest",
        "type": "end_to_end",
        "family": "qwen3.6",
        "campaign": "new_ollama_vision_2026_04",
        "category": "qwen_vision",
        "size_gb": 24.0,
        "context_window": "256K",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 24,
        "supports_images": True,
        "source_url": "https://ollama.com/library/qwen3.6",
        "notes": "User requested command: ollama run qwen3.6",
    },
    "e2e_qwen36_35b": {
        "description": "End-to-End: Qwen3.6:35B",
        "ollama_tag": "qwen3.6:35b",
        "type": "end_to_end",
        "family": "qwen3.6",
        "campaign": "new_ollama_vision_2026_04",
        "category": "qwen_vision",
        "size_gb": 24.0,
        "context_window": "256K",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 24,
        "supports_images": True,
        "source_url": "https://ollama.com/library/qwen3.6",
        "notes": "User requested command: ollama run qwen3.6:35b",
    },

    # 2026-04 new Ollama vision campaign: Gemma 4 local models.
    # gemma4:31b-cloud is intentionally excluded because it is a cloud model.
    "e2e_gemma4_latest": {
        "description": "End-to-End: Gemma4 latest",
        "ollama_tag": "gemma4:latest",
        "type": "end_to_end",
        "family": "gemma4",
        "campaign": "new_ollama_vision_2026_04",
        "category": "gemma4_edge",
        "size_gb": 9.6,
        "context_window": "128K",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 10,
        "supports_images": True,
        "source_url": "https://ollama.com/library/gemma4",
    },
    "e2e_gemma4_e2b": {
        "description": "End-to-End: Gemma4:E2B",
        "ollama_tag": "gemma4:e2b",
        "type": "end_to_end",
        "family": "gemma4",
        "campaign": "new_ollama_vision_2026_04",
        "category": "gemma4_edge",
        "size_gb": 7.2,
        "context_window": "128K",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 8,
        "supports_images": True,
        "source_url": "https://ollama.com/library/gemma4",
    },
    "e2e_gemma4_e4b": {
        "description": "End-to-End: Gemma4:E4B",
        "ollama_tag": "gemma4:e4b",
        "type": "end_to_end",
        "family": "gemma4",
        "campaign": "new_ollama_vision_2026_04",
        "category": "gemma4_edge",
        "size_gb": 9.6,
        "context_window": "128K",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 10,
        "supports_images": True,
        "source_url": "https://ollama.com/library/gemma4",
    },
    "e2e_gemma4_26b": {
        "description": "End-to-End: Gemma4:26B MoE",
        "ollama_tag": "gemma4:26b",
        "type": "end_to_end",
        "family": "gemma4",
        "campaign": "new_ollama_vision_2026_04",
        "category": "gemma4_workstation",
        "size_gb": 18.0,
        "context_window": "256K",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 18,
        "supports_images": True,
        "source_url": "https://ollama.com/library/gemma4",
    },
    "e2e_gemma4_31b": {
        "description": "End-to-End: Gemma4:31B Dense",
        "ollama_tag": "gemma4:31b",
        "type": "end_to_end",
        "family": "gemma4",
        "campaign": "new_ollama_vision_2026_04",
        "category": "gemma4_workstation",
        "size_gb": 20.0,
        "context_window": "256K",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 20,
        "supports_images": True,
        "source_url": "https://ollama.com/library/gemma4",
    },

    # 2026-04 new Ollama vision campaign: Llama 3.2 Vision.
    "e2e_llama32_vision_latest": {
        "description": "End-to-End: Llama3.2-Vision latest",
        "ollama_tag": "llama3.2-vision:latest",
        "type": "end_to_end",
        "family": "llama3.2-vision",
        "campaign": "new_ollama_vision_2026_04",
        "category": "llama_vision",
        "size_gb": 7.8,
        "context_window": "128K",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 8,
        "supports_images": True,
        "source_url": "https://ollama.com/library/llama3.2-vision",
    },
    "e2e_llama32_vision_11b_apr2026": {
        "description": "End-to-End: Llama3.2-Vision:11B (April 2026 rerun)",
        "ollama_tag": "llama3.2-vision:11b",
        "type": "end_to_end",
        "family": "llama3.2-vision",
        "campaign": "new_ollama_vision_2026_04",
        "category": "llama_vision",
        "size_gb": 7.8,
        "context_window": "128K",
        "input_modalities": ["Text", "Image"],
        "vram_gb": 8,
        "supports_images": True,
        "source_url": "https://ollama.com/library/llama3.2-vision",
        "notes": "Separate April folder to avoid appending into the old baseline llama3.2-vision:11b results.",
    },
}

ACTIVE_NEW_VISION_MODEL_KEYS = [
    "e2e_gemma4_e2b",
    "e2e_qwen35_2b",
    "e2e_qwen35_4b",
    "e2e_llama32_vision_11b_apr2026",
    "e2e_qwen35_9b",
    "e2e_gemma4_e4b",
    "e2e_gemma4_26b",
    "e2e_gemma4_31b",
    "e2e_qwen35_27b",
    "e2e_qwen36_35b",
]

NEW_VISION_MODEL_KEYS = ACTIVE_NEW_VISION_MODEL_KEYS

DUPLICATE_NEW_VISION_MODEL_KEYS = {
    "e2e_gemma4_latest": "e2e_gemma4_e4b",
    "e2e_qwen36_latest": "e2e_qwen36_35b",
    "e2e_llama32_vision_latest": "e2e_llama32_vision_11b_apr2026",
}

NEW_OLLAMA_MODEL_GROUPS = {
    "qwen3.5": ["e2e_qwen35_2b", "e2e_qwen35_4b", "e2e_qwen35_9b", "e2e_qwen35_27b"],
    "qwen3.6": ["e2e_qwen36_35b"],
    "gemma4_edge": ["e2e_gemma4_e2b", "e2e_gemma4_e4b"],
    "gemma4_workstation": ["e2e_gemma4_26b", "e2e_gemma4_31b"],
    "llama3.2-vision": ["e2e_llama32_vision_11b_apr2026"],
}


def model_supports_images(model_key):
    """Return True when a model can be used by the image-based e2e runner."""
    return MODELS[model_key].get("supports_images", True)

# ── OLLAMA SETTINGS ─────────────────────────────────────────────────────────
OLLAMA_NUM_CTX     = 8192
OLLAMA_NUM_PREDICT = 512
OLLAMA_TEMPERATURE = 0.1
OLLAMA_MAX_RETRIES = 3
MAX_HAZARDS_PER_IMAGE = 3

# ── GROUNDING THRESHOLDS ────────────────────────────────────────────────────
GDINO_BOX_THRESHOLD  = 0.35
GDINO_TEXT_THRESHOLD  = 0.25
DETR_THRESHOLD        = 0.5
CLIP_SIMILARITY_MIN   = 0.25

# ── EVALUATION ──────────────────────────────────────────────────────────────
MAJORITY_VOTE_RUNS = 3
IOU_THRESHOLDS     = [0.25, 0.50, 0.75]
GROUNDING_IOG_THRESHOLDS = [0.1, 0.3]

CANONICAL_HAZARD_CATEGORIES = [
    "Fall_Hazard",
    "StruckBy_Hazard",
    "Electrocution_Hazard",
    "CaughtInBetween_hazard",
    "PPE_Violation",
    "Housekeeping_Storage",
    "Other",
]

# ── VALID OSHA CATEGORIES ──────────────────────────────────────────────────
VALID_OSHA_CATEGORIES = {
    "fall hazard", "fall protection",
    "struck-by hazard", "struck-by",
    "caught-in/between hazard", "caught-in/between",
    "electrocution hazard", "electrocution", "electrical safety",
    "ppe violation", "ppe",
    "housekeeping & material storage", "housekeeping",
    "scaffolding", "ladder safety", "ladders",
    "excavation/trenching", "excavation",
    "fire safety", "fire hazard",
    "traffic safety",
    "crane safety", "rigging",
    "confined space",
    "general safety", "general safety & health",
    "machine guarding",
    "signage", "equipment use",
    "respiratory protection", "hearing protection",
    "personal protective equipment",
    "compliant",
}

VALID_RISK_LEVELS = {"high", "medium", "low", "none"}

EXCEL_SUMMARY_COLUMNS = [
    "image_id", "image_name", "model_tag", "run_number", "architecture",
    "is_safe_pred", "n_hazards_pred", "n_boxes_pred",
    "hazard_label", "canonical_hazard_label",
    "gt_hazard_label", "gt_canonical_hazard_label",
    "grounding_coverage_pct",
    "n_gdino_boxes", "n_detr_fallback_boxes",
    "total_inference_time_sec",
    "caption_word_count",
    "structured_compliance_pct",
    "n_high_confidence", "n_medium_confidence",
    "error",
]

EXPECTED_PAPER_IMAGE_COUNT = 203


def get_image_list(image_dir=None):
    """Return sorted list of all image paths in IMAGE_DIR."""
    image_dir = image_dir or IMAGE_DIR
    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".avif"}
    images = []
    if not os.path.isdir(image_dir):
        print(f"WARNING: image directory does not exist: {image_dir}")
        return images
    for f in sorted(os.listdir(image_dir)):
        if os.path.splitext(f)[1].lower() in exts:
            images.append(os.path.join(image_dir, f))
    return images


def image_id_from_name(filename):
    """Extract numeric ID from filename like '42.webp' -> '042'."""
    stem = os.path.splitext(filename)[0]
    match = re.match(r"(\d+)", stem)
    if match:
        return match.group(1).zfill(3)
    return stem
