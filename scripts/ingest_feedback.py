import argparse, json, uuid
from datetime import datetime, timezone

OUT = "data/runtime/feedback_events.jsonl"

def now(): return datetime.now(timezone.utc).isoformat()

parser = argparse.ArgumentParser()
parser.add_argument("--did", required=True)
parser.add_argument("--type", required=True)
parser.add_argument("--payload", default="{}")
args = parser.parse_args()

event = {
    "event_id": str(uuid.uuid4()),
    "did": args.did,
    "type": args.type,
    "ts": now(),
    "payload": json.loads(args.payload),
    "meta": {"agent_version": "T5-S6"}
}

with open(OUT, "a", encoding="utf-8") as f:
    f.write(json.dumps(event, ensure_ascii=False) + "\n")

print(f"[FEEDBACK] wrote {args.type} for {args.did}")
