# scripts/mini_dashboard.py
# ASCII summary of latest aggregates + top-5 Mode x Principle table

import os, sys
if hasattr(sys.stdout, "reconfigure"):
    # Ensure UTF-8 on Windows terminals; safe no-op elsewhere
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")

# Make repo root importable when running from scripts/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import List, Dict, Any, Tuple
from datetime import datetime
from src.metrics_loader import load_aggregate_records

def fmt_pct(x: float) -> str:
    try:
        return f"{(x*100):.1f}%"
    except Exception:
        return "0.0%"

def top5_mp(records: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
    # collapse all runs, filter noise labels, then take top-5
    counts: Dict[str, int] = {}
    for r in records:
        for k, v in r["mp_counts"].items():
            label = (k or "").strip()
            if not label or label in {"- × -", "-x-"}:
                continue
            counts[label] = counts.get(label, 0) + int(v)
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:5]

def delta(a: float, b: float) -> float:
    return (a - b) if (a is not None and b is not None) else 0.0

def main():
    records = load_aggregate_records()
    if not records:
        print("No aggregate metric files found in /data/metrics/. Run T4-S2 first.")
        return

    latest = records[-1]
    prev = records[-2] if len(records) >= 2 else None

    ts_str = latest["ts"].strftime("%Y-%m-%d %H:%M:%S")
    avg_delta_latest = float(latest["avg_delta"])
    empathy_latest = float(latest["empathy_rate"])

    avg_delta_prev = float(prev["avg_delta"]) if prev else None
    empathy_prev = float(prev["empathy_rate"]) if prev else None

    print("\n=== OWLUME — MINI DASHBOARD (T4-S3) ===")
    print(f"Latest run: {ts_str}")
    print(f"Source file: {latest.get('source_file','-')}")
    print("----------------------------------------")
    print(f"Average Clarity Gain Δ: {avg_delta_latest:.3f}" + (f"  (Δ vs prev: {delta(avg_delta_latest, avg_delta_prev):+.3f})" if prev else ""))
    print(f"Empathy activation rate: {fmt_pct(empathy_latest)}" + (f"  (Δ vs prev: {fmt_pct(delta(empathy_latest, empathy_prev))})" if prev else ""))
    print("\nTop-5 Mode x Principle (cumulative counts)")
    print("----------------------------------------")
    top5 = top5_mp(records)
    if not top5:
        print("(no Mode x Principle counts yet)")
    else:
        # simple table
        col1 = max(24, max(len(k) for k, _ in top5))
        print(f"{'Label'.ljust(col1)} | Count")
        print(f"{'-'*col1}-+------")
        for k, v in top5:
            label = k.replace("×", "x")  # keep ASCII safe
            print(f"{label.ljust(col1)} | {v}")

    print("\nHints:")
    print(" - Run 'Run: Chart Pack (T4-S3)' to regenerate PNG charts.")
    print(" - Add more aggregates_* files by running T4-S2 again.")
    print("")

if __name__ == "__main__":
    main()
