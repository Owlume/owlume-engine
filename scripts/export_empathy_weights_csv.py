#!/usr/bin/env python3
"""
Owlume — Export Empathy Weights (v0.1 pack) to CSV

Reads your empathy_weights.json (array format) and writes a flat CSV
with columns: move_id, mode, principle, score, n, mean, m2, ci_low, ci_high.

Usage:
  python -u scripts/export_empathy_weights_csv.py \
    --in data/weights/empathy_weights.json \
    --out reports/empathy_weights_export.csv
"""

import argparse, json, csv, os

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True, help="Path to empathy_weights.json (v0.1)")
    ap.add_argument("--out", dest="out_path", required=True, help="Output CSV path")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out_path), exist_ok=True)

    with open(args.in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    moves = data.get("weights", [])
    if not isinstance(moves, list):
        raise ValueError("weights pack must have an array under 'weights'")

    headers = ["move_id", "mode", "principle", "score", "n", "mean", "m2", "ci_low", "ci_high"]

    with open(args.out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for m in moves:
            row = {h: m.get(h, "") for h in headers}
            writer.writerow(row)

    print(f"[EXPORT] {len(moves)} moves written → {args.out_path}")

if __name__ == "__main__":
    main()
