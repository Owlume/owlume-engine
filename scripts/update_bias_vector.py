#!/usr/bin/env python
# --- repo path bootstrap ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# --- end bootstrap ---

import json
from datetime import datetime, timezone
import argparse

from src.bse.extract_bias_signals import extract_signals
from src.bse.bias_vector import empty_vector, ema_update, snapshot, save_jsonl, cosine
from src.bse.cards import render_bias_insight

DATA_BSE = ROOT / "data" / "bse" / "bias_vectors.jsonl"
LOG_BSE  = ROOT / "data" / "logs" / "bias_events.jsonl"

def load_latest_vector(user: str) -> dict:
    if not DATA_BSE.exists():
        return empty_vector()
    last = None
    with open(DATA_BSE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                if rec.get("user") == user:
                    last = rec
            except Exception:
                continue
    return last["vector"] if last else empty_vector()

def main():
    ap = argparse.ArgumentParser(description="Apply BSE EMA update for a single reflection payload.")
    ap.add_argument("--in", dest="infile", help="Reflection JSON file; omit to read from stdin")
    ap.add_argument("--user", default="local", help="User id (default: local)")
    ap.add_argument("--alpha", type=float, default=0.20, help="EMA alpha (0..1, default 0.20)")
    args = ap.parse_args()

    # Read reflection payload
    if args.infile:
        ref = json.loads(Path(args.infile).read_text(encoding="utf-8"))
    else:
        ref = json.loads(sys.stdin.read())

    # Ensure output dirs
    (ROOT / "data" / "bse").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "logs").mkdir(parents=True, exist_ok=True)

    # 1) Extract signals
    signals = extract_signals(ref)

    # 2) Update vector
    prev_vec = load_latest_vector(args.user)
    new_vec  = ema_update(prev_vec, signals, args.alpha)

    # 3) Save snapshot
    did = ref.get("did")
    delta_cos = 1.0 - cosine(prev_vec, new_vec)
    snap = snapshot(args.user, new_vec, args.alpha, source="runtime", did=did, delta_cosine=delta_cos)
    save_jsonl(DATA_BSE, snap)

    # 4) Log event
    event = {
        "type": "BSE_UPDATE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": args.user,
        "did": did,
        "signals": signals,
        "delta_cosine": round(delta_cos, 4)
    }
    with open(LOG_BSE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # 5) Optional insight card to STDOUT (so watcher can print it)
    card = render_bias_insight(prev_vec, new_vec, did=did, threshold=0.15)
    if card:
        print(json.dumps({"card": card}, ensure_ascii=False))

if __name__ == "__main__":
    main()

