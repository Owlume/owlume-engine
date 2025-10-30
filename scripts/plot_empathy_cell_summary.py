#!/usr/bin/env python3
"""
Owlume — Plot Empathy Cell Summary (bar chart)

Input:  reports/empathy_cell_summary.csv  (from summarize_empathy_weights_by_cell.py)
Output: reports/empathy_cell_summary.png  (bar chart of avg_score per cell)

Usage:
  python -u scripts/plot_empathy_cell_summary.py \
    --in reports/empathy_cell_summary.csv \
    --out reports/empathy_cell_summary.png
"""

import argparse, csv, os
import matplotlib.pyplot as plt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True, help="Path to empathy_cell_summary.csv")
    ap.add_argument("--out", dest="out_path", required=True, help="Path to write PNG")
    ap.add_argument("--top", type=int, default=20, help="Show top-N cells by avg_score")
    args = ap.parse_args()

    cells, scores = [], []
    with open(args.in_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Sort by avg_score desc, keep top-N
    rows.sort(key=lambda r: float(r.get("avg_score", 0.0)), reverse=True)
    rows = rows[: args.top]

    for r in rows:
        cells.append(r.get("cell", ""))
        scores.append(float(r.get("avg_score", 0.0)))

    os.makedirs(os.path.dirname(args.out_path), exist_ok=True)

    # Single-plot bar chart (no specific colors or styles)
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(scores)), scores)
    plt.xticks(range(len(cells)), cells, rotation=30, ha="right")
    plt.ylabel("Average Empathy Weight (avg_score)")
    plt.title("Empathy Effectiveness by Cell (Top {})".format(args.top))
    plt.tight_layout()
    plt.savefig(args.out_path, dpi=200)
    plt.close()

    print(f"[PLOT] Saved → {args.out_path}")

if __name__ == "__main__":
    main()
