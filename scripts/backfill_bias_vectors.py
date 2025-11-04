#!/usr/bin/env python
"""
BSE Backfill Script — Owlume
---------------------------------
Reads existing clarity_gain_samples.jsonl logs and retroactively
builds a bias vector trajectory for each user. Produces:
  • /data/bse/bias_vectors.jsonl   (EMA snapshots)
  • /data/logs/bias_events.jsonl   (BSE_UPDATE lines)
Use once to "warm start" the bias signature for historical data.

Usage:
    python -u scripts/backfill_bias_vectors.py --alpha 0.20
"""

# --- repo path bootstrap ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# --- end bootstrap ---

import json
import argparse
from datetime import datetime, timezone
from collections import defaultdict
from src.bse.extract_bias_signals import extract_signals
from src.bse.bias_vector import empty_vector, ema_update, snapshot, save_jsonl, cosine

LOG_CG = ROOT / "data" / "logs" / "clarity_gain_samples.jsonl"
OUT_VEC = ROOT / "data" / "bse" / "bias_vectors.jsonl"
OUT_EVT = ROOT / "data" / "logs" / "bias_events.jsonl"

def read_jsonl(path: Path):
    if not path.exists():
        print(f"[!] No file found: {path}")
        return []
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                lines.append(json.loads(line))
            except Exception:
                continue
    return lines

def backfill(alpha: float = 0.20):
    lines = read_jsonl(LOG_CG)
    if not lines:
        print("[!] No reflections found; nothing to backfill.")
        return

    # Sort by timestamp to ensure chronological EMA
    lines.sort(key=lambda x: x.get("timestamp", ""))

    user_vectors = defaultdict(empty_vector)
    count = 0
    for ref in lines:
        user = ref.get("user", "local")
        did = ref.get("did")
        prev_vec = user_vectors[user]
        signal = extract_signals(ref)
        new_vec = ema_update(prev_vec, signal, alpha)
        delta_cos = 1.0 - cosine(prev_vec, new_vec)
        user_vectors[user] = new_vec

        snap = snapshot(user, new_vec, alpha, source="backfill", did=did, delta_cosine=delta_cos)
        save_jsonl(OUT_VEC, snap)

        event = {
            "type": "BSE_UPDATE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "did": did,
            "signals": signal,
            "delta_cosine": round(delta_cos, 4),
            "meta": {"source": "backfill"}
        }
        with open(OUT_EVT, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        count += 1

    print(f"[BSE] Backfill complete — processed {count} reflections across {len(user_vectors)} user(s).")
    print(f"[BSE] Snapshots → {OUT_VEC.name}  |  Events → {OUT_EVT.name}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.20, help="EMA alpha (default 0.20)")
    args = ap.parse_args()
    (ROOT / "data" / "bse").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "logs").mkdir(parents=True, exist_ok=True)
    backfill(alpha=args.alpha)

if __name__ == "__main__":
    main()
