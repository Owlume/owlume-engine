#!/usr/bin/env python3
"""
Owlume — Summarize Empathy Weights by Cell (v0.1 pack)

Reads your empathy_weights.json (array of moves)
and outputs a CSV summarizing one row per Mode × Principle.

Each summary includes:
- cell (Mode × Principle)
- n_moves
- avg_score
- total_n
- avg_mean
- avg_ci_low
- avg_ci_high

Usage:
  python -u scripts/summarize_empathy_weights_by_cell.py \
    --in data/weights/empathy_weights.json \
    --out reports/empathy_cell_summary.csv
"""

import argparse, json, csv, os
from collections import defaultdict

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
        raise ValueError("weights pack must be an array under 'weights'")

    # Aggregate by Mode × Principle
    agg = defaultdict(lambda: {"n_moves": 0, "sum_score": 0.0, "sum_n": 0, "sum_mean": 0.0, "sum_ci_low": 0.0, "sum_ci_high": 0.0})

    for m in moves:
        mode = str(m.get("mode", ""))
        principle = str(m.get("principle", ""))
        cell = f"{mode} × {principle}"
        agg[cell]["n_moves"] += 1
        agg[cell]["sum_score"] += float(m.get("score", 0.0))
        agg[cell]["sum_n"] += int(m.get("n", 0))
        agg[cell]["sum_mean"] += float(m.get("mean", 0.0))
        agg[cell]["sum_ci_low"] += float(m.get("ci_low", 0.0))
        agg[cell]["sum_ci_high"] += float(m.get("ci_high", 0.0))

    # Write summary CSV
    headers = ["cell", "n_moves", "avg_score", "total_n", "avg_mean", "avg_ci_low", "avg_ci_high"]
    with open(args.out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for cell, v in sorted(agg.items()):
            n = v["n_moves"]
            row = [
                cell,
                n,
                v["sum_score"]/n if n else 0.0,
                v["sum_n"],
                v["sum_mean"]/n if n else 0.0,
                v["sum_ci_low"]/n if n else 0.0,
                v["sum_ci_high"]/n if n else 0.0
            ]
            writer.writerow(row)

    print(f"[SUMMARY] {len(agg)} cells written → {args.out_path}")

if __name__ == "__main__":
    main()
