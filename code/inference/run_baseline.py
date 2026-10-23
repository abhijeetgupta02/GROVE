#!/usr/bin/env python3
"""
Single-pass baseline runner.

Runs one of the eleven single-pass vision-language baselines end-to-end (image
-> hazards directly, no grounding pipeline) and writes per-image JSONL/XLSX
prediction records, using the same output schema as the GROVE pipeline so the
evaluation scripts treat every system identically.

The model is selected by its key in ``config.MODELS``; the paper labels map to
these keys as documented in ``MODEL_IDENTIFIERS.md``. Inference requires a local
Ollama server serving the corresponding ``ollama_tag``; the cached predictions
used for the paper are provided under ``predictions/`` so the reported tables
can be reproduced without re-running inference.

Usage (run from code/inference/):
    python run_baseline.py --list
    python run_baseline.py --model e2e_qwen35_27b
    python run_baseline.py --model e2e_gemma4_31b --start 1 --end 10
"""
import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import config
from shared.e2e_runner import run_e2e_experiment

# Eleven single-pass baselines reported in the paper (Table 2 / Table 4).
PAPER_BASELINE_KEYS = [
    "e2e_qwen35_2b", "e2e_qwen35_4b", "e2e_qwen35_9b", "e2e_qwen35_27b",
    "e2e_qwen36_35b",
    "e2e_gemma4_e2b", "e2e_gemma4_e4b", "e2e_gemma4_26b", "e2e_gemma4_31b",
    "e2e_llama32_vision_11b_apr2026",
    "e2e_internvl3_5_8b",
]


def main():
    parser = argparse.ArgumentParser(description="Run a single-pass VLM baseline.")
    parser.add_argument("--model", default=None,
                        help="Model key from config.MODELS (see --list).")
    parser.add_argument("--list", action="store_true",
                        help="List the paper baseline model keys and exit.")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=9999)
    parser.add_argument("--run", type=int, default=1, choices=[1, 2, 3])
    parser.add_argument("--delay", type=int, default=config.GPU_DELAY_SECONDS)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.list or not args.model:
        print("Paper single-pass baselines (model key -> Ollama tag):")
        for key in PAPER_BASELINE_KEYS:
            print(f"  {key:<34} {config.MODELS[key]['ollama_tag']}")
        if not args.model:
            return

    if args.model not in config.MODELS:
        raise SystemExit(f"Unknown model key '{args.model}'. Use --list to see valid keys.")

    run_e2e_experiment(
        args.model,
        start=args.start,
        end=args.end,
        run=args.run,
        delay=args.delay,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
