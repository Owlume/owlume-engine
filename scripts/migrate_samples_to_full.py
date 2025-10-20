import json, sys, uuid, datetime
from pathlib import Path

SRC = Path("data/logs/clarity_gain_samples.jsonl")
DST = Path("data/logs/clarity_gain_samples_full.jsonl")

def as_iso_utc(ts: str | None) -> str:
    if not ts:
        return datetime.datetime.now(datetime.timezone.utc)\
               .replace(microsecond=0).isoformat().replace("+00:00", "Z")
    # normalize common formats
    ts = ts.replace(" ", "T")
    if ts.endswith("+00:00"):
        ts = ts.replace("+00:00", "Z")
    return ts

def migrate_one(obj: dict) -> dict:
    # Source (lean) fields
    mode = obj.get("mode_detected", "-")
    principle = obj.get("principle_detected", "-")
    empathy_on = bool(obj.get("empathy_state", False))
    cg_pre = float(obj.get("cg_pre", 0.0))
    cg_post = float(obj.get("cg_post", 0.0))
    cg_delta = round(cg_post - cg_pre, 2)
    ts = as_iso_utc(obj.get("timestamp"))
    did = obj.get("did") or f"DID-{uuid.uuid4().hex[:8]}"
    share = obj.get("share") or {"status": "skipped"}

    # Build schema-compliant record
    full = {
        "session_id": f"SES-{did}",
        "user_text": obj.get("user_text") or "(demo sample)",
        "detected": {
            "mode": mode,
            "principle": principle,
            "drivers": [],                 # required list
            "empathy": empathy_on,         # required bool
            "confidence": 0.65,            # required number (stub)
            "alt": {                       # required object (stub)
                "mode": None,
                "principle": None,
                "confidence": 0.35
            }
        },
        # voices must be non-empty; use a minimal stub (string id)
        "voices": ["thiel"],
        "clarity_gain": {
            "CG_pre": round(cg_pre, 2),
            "CG_post": round(cg_post, 2),
            "CG_delta": round(cg_delta, 2)
        },
        "share": share,
        "timestamp": ts,
        # proof_signals required; structure stubbed to common pattern
         "proof_signals": []
       
    }

    # IMPORTANT: schema forbids additional root fields; do NOT keep 'did' or 'top3'
    return full

def main():
    if not SRC.exists():
        print(f"[ERR] missing {SRC}")
        sys.exit(1)
    lines = [l.strip() for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    n = 0
    with DST.open("w", encoding="utf-8") as out:
        for line in lines:
            obj = json.loads(line)
            full = migrate_one(obj)
            out.write(json.dumps(full, ensure_ascii=False) + "\n")
            n += 1
    print(f"[OK] wrote {n} migrated records → {DST}")

if __name__ == "__main__":
    main()

