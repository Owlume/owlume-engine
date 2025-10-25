# scripts/debug_parse_metrics.py
import os, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.metrics_loader import load_aggregate_records

def main():
    recs = load_aggregate_records()
    if not recs:
        print("No aggregates found in /data/metrics/")
        return
    for r in recs:
        print("—", r["source_file"])
        print("  ts:", r["ts"])
        print("  avg_delta:", r["avg_delta"])
        print("  empathy_rate:", r["empathy_rate"])
        print("  mp_counts:", list(r["mp_counts"].items())[:5], "… total:", len(r["mp_counts"]))
        print()

if __name__ == "__main__":
    main()
