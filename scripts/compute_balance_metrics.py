import json, glob, statistics as stats
from pathlib import Path
from datetime import datetime, timedelta, timezone

AGG_DIR = Path("data/metrics")
OUT = AGG_DIR / f"aggregates_balance_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

def z(x): 
    m = sum(x)/len(x); s = (sum((v-m)**2 for v in x)/max(1,len(x)-1))**0.5 or 1.0
    return [(v-m)/s for v in x]

def main():
    files = sorted(AGG_DIR.glob("aggregates_*.json"))
    if not files: 
        raise SystemExit("no aggregates found")
    with open(files[-1], "r", encoding="utf-8") as f:
        agg = json.load(f)

    # Heuristic placeholders; replace with your real signals when ready
    depth = agg.get("avg_causal_density", 0.6)
    breadth = agg.get("avg_semantic_dispersion", 0.6)

    # Normalize to [0,1] guardrails if needed
    depth_score = max(0,min(1, depth))
    breadth_score = max(0,min(1, breadth))

    # Imbalance: higher drift when breadth >> depth; higher tunnel when depth >> breadth
    diff = breadth_score - depth_score
    drift_index  = max(0.0,  diff)      # over-breadth
    tunnel_index = max(0.0, -diff)      # over-depth

    # Balance near 0.5 is ideal; compress toward mid
    balance_index = 0.5 + (diff * 0.5)  # maps [-1,1] → [0,1] around 0.5

    out = {
        "depth_score": depth_score,
        "breadth_score": breadth_score,
        "drift_index": drift_index,
        "tunnel_index": tunnel_index,
        "balance_index": balance_index,
        "source": files[-1].name,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    with open(OUT, "w", encoding="utf-8") as w: json.dump(out, w, indent=2)
    print(f"[Balance] wrote → {OUT}")

if __name__ == "__main__":
    main()
