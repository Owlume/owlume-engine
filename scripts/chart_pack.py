# scripts/chart_pack.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import os
from typing import Dict
import matplotlib.pyplot as plt

from datetime import datetime
from src.metrics_loader import load_aggregate_records

def _ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def plot_clarity_trend(records, outdir) -> str:
    x = [r["ts"] for r in records]
    y = [r["avg_delta"] for r in records]
    plt.figure()
    plt.plot(x, y, marker="o")
    plt.title("Clarity Gain Trend (Δ over time)")
    plt.xlabel("Run timestamp")
    plt.ylabel("Average Δ")
    plt.tight_layout()
    path = os.path.join(outdir, "clarity_trend.png")
    plt.savefig(path, dpi=144)
    plt.close()
    return path

def plot_empathy_curve(records, outdir) -> str:
    x = [r["ts"] for r in records]
    y = [r["empathy_rate"] for r in records]
    plt.figure()
    plt.plot(x, y, marker="o")
    plt.title("Empathy Activation Rate (over time)")
    plt.xlabel("Run timestamp")
    plt.ylabel("Empathy rate")
    plt.tight_layout()
    path = os.path.join(outdir, "empathy_curve.png")
    plt.savefig(path, dpi=144)
    plt.close()
    return path

def plot_mode_principle_heatmap(records, outdir) -> str:
    """
    Builds a Mode×Principle heatmap from cumulative counts found in aggregates.
    Assumes labels look like 'Mode × Principle' (with a literal ×). Tolerant to 'x' as well.
    """
    # Collect counts
    mp_map: Dict[str, Dict[str, int]] = {}
    for r in records:
        for label, count in r["mp_counts"].items():
            if not label or label == "- × -":
                continue
            if "×" in label:
                mode, principle = [s.strip() for s in label.split("×", 1)]
            elif "x" in label:
                mode, principle = [s.strip() for s in label.split("x", 1)]
            else:
                # Skip if not parseable
                continue
            mp_map.setdefault(mode, {})
            mp_map[mode][principle] = mp_map[mode].get(principle, 0) + int(count)

    if not mp_map:
        # nothing to plot; create a placeholder
        plt.figure()
        plt.text(0.5, 0.5, "No Mode × Principle data yet", ha="center", va="center")
        plt.axis("off")
        path = os.path.join(outdir, "mode_principle_heatmap.png")
        plt.savefig(path, dpi=144, bbox_inches="tight")
        plt.close()
        return path

    # Ordered axes
    modes = sorted(mp_map.keys())
    principles = sorted({p for d in mp_map.values() for p in d.keys()})
    # Build matrix
    import numpy as np
    mat = np.zeros((len(modes), len(principles)), dtype=int)
    for i, m in enumerate(modes):
        for j, p in enumerate(principles):
            mat[i, j] = mp_map.get(m, {}).get(p, 0)

    # Plot
    plt.figure()
    plt.imshow(mat, aspect="auto")
    plt.title("Mode × Principle Heatmap (counts)")
    plt.xticks(range(len(principles)), principles, rotation=45, ha="right")
    plt.yticks(range(len(modes)), modes)
    plt.tight_layout()
    path = os.path.join(outdir, "mode_principle_heatmap.png")
    plt.savefig(path, dpi=144)
    plt.close()
    return path

def main():
    root = os.path.dirname(os.path.dirname(__file__))
    outdir = os.path.join(root, "artifacts", "charts")
    _ensure_dir(outdir)

    records = load_aggregate_records()
    if not records:
        print("No aggregate metric files found in /data/metrics/. Run T4-S2 first.")
        return

    p1 = plot_clarity_trend(records, outdir)
    p2 = plot_empathy_curve(records, outdir)
    p3 = plot_mode_principle_heatmap(records, outdir)

    print("Saved charts →")
    print(" -", p1)
    print(" -", p2)
    print(" -", p3)

if __name__ == "__main__":
    main()
