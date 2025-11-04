# scripts/emit_dummy_event.py
import json, sys
from datetime import datetime, timezone
from pathlib import Path
from random import randint

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "data" / "runtime"
RUNTIME.mkdir(parents=True, exist_ok=True)
LOG = RUNTIME / "insight_events.jsonl"

text = " ".join(sys.argv[1:]) or "Quick reflection to test the live loop."
ev = {
    "type": "NEW_REFLECTION",
    "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "did": f"DID-{randint(100000,999999)}",
    "text": text,
    "cg_pre": 0.45
}
with LOG.open("a", encoding="utf-8") as f:
    f.write(json.dumps(ev, ensure_ascii=False) + "\n")

print(f"[EMIT] wrote NEW_REFLECTION → {LOG.name} did={ev['did']}")
