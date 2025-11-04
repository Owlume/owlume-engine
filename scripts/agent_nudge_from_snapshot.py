#!/usr/bin/env python3
import argparse, json, os, re, sys
from datetime import datetime, timezone

VITALS_RE = re.compile(
    r"Vitals:\s*Δavg=(?P<delta>[-+]?\d*\.\d+|\d+)\s*\|\s*Empathy=(?P<empathy>[-+]?\d*\.\d+|\d+)%\s*\|\s*Positive=(?P<positive>[-+]?\d*\.\d+|\d+)%\s*\|\s*Drift=(?P<drift>[-+]?\d*\.\d+|\d+)\s*\|\s*Tunnel=(?P<tunnel>[-+]?\d*\.\d+|\d+)\s*\|\s*Aim=(?P<aim>\w+)",
    re.IGNORECASE
)

def parse_last_snapshot(text: str):
    # Return dict with vitals + meta if Vitals line exists
    m = VITALS_RE.search(text)
    if not m:
        return None
    d = m.groupdict()
    return {
        "delta_avg": float(d["delta"]),
        "empathy_rate": float(d["empathy"]) / 100.0,
        "positive_rate": float(d["positive"]) / 100.0,
        "drift": float(d["drift"]),
        "tunnel": float(d["tunnel"]),
        "aim": d["aim"],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_log", required=True)
    ap.add_argument("--out_jsonl", required=True)
    args = ap.parse_args()

    if not os.path.exists(args.in_log):
        print("[S6-S1] no last_snapshot.log found; nothing to nudge")
        return 0

    with open(args.in_log, "r", encoding="utf-8") as f:
        txt = f.read()

    payload = parse_last_snapshot(txt)
    if not payload:
        print("[S6-S1] no Vitals line; nothing to nudge")
        return 0

    # Simple local nudge heuristic (tune later)
    nudges = []
    if payload["delta_avg"] >= 0.10:
        nudges.append("Celebrate a clarity win. Capture what worked.")
    if payload["drift"] >= 0.12:
        nudges.append("Run a quick 'Why now?' probe to reduce drift.")
    if payload["tunnel"] >= 0.05:
        nudges.append("Add a stakeholder/impact question to widen view.")
    if payload["empathy_rate"] < 0.25:
        nudges.append("Try Empathy overlay on the next tough reflection.")

    event = {
        "type": "NUDGE_SNAPSHOT",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vitals": payload,
        "nudges": nudges or ["Keep momentum. One small check beats none."],
        "source": "agent_nudge_from_snapshot",
    }

    os.makedirs(os.path.dirname(args.out_jsonl), exist_ok=True)
    with open(args.out_jsonl, "a", encoding="utf-8") as w:
        w.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"[S6-S1] nudge emitted → {args.out_jsonl}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
