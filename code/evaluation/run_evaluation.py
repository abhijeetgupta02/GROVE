#!/usr/bin/env python3
"""
End-to-end evaluation driver.

Runs the three scoring scripts over every prediction workbook in
``predictions/`` and writes the result CSVs into ``results/``:

    identification_eval.py        -> results/identification/identification_results.csv
    grounding_eval.py             -> results/grounding/master_grounding_summary.csv
    cataware_gt_covers_pred.py    -> results/grounding/gt_covers_pred_comparison.csv

These regenerate the identification (Tables 3, 4, 9) and spatial-grounding
(Tables 5, 6, 10) numbers reported in the paper directly from the bundled
predictions and ground truth, with no model inference or internet access.

Usage (run from code/evaluation/):
    python run_evaluation.py
    python run_evaluation.py --gt /path/to/annotations.coco.json
    python run_evaluation.py --predictions-dir /path/to/predictions
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = [
    "identification_eval.py",
    "grounding_eval.py",
    "cataware_gt_covers_pred.py",
]


def main():
    parser = argparse.ArgumentParser(description="Run all GROVE evaluation scripts.")
    parser.add_argument("--gt", default=None, help="Path to the COCO ground-truth JSON.")
    parser.add_argument("--predictions-dir", default=None,
                        help="Directory of prediction workbooks.")
    args = parser.parse_args()

    passthrough = []
    if args.gt:
        passthrough += ["--gt", args.gt]
    if args.predictions_dir:
        passthrough += ["--predictions-dir", args.predictions_dir]

    for script in SCRIPTS:
        print(f"\n{'=' * 70}\n  Running {script}\n{'=' * 70}")
        subprocess.run([sys.executable, str(HERE / script), *passthrough], check=True)

    print("\nAll evaluation scripts completed. Results written under results/.")


if __name__ == "__main__":
    main()
