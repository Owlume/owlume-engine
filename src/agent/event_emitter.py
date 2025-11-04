import argparse, json, os, sys, uuid
from datetime import datetime, timezone

RUNTIME_DIR = "data/runtime"
EVENTS_PATH = os.path.join(RUNTIME_DIR, "insight_events.jsonl")

def _ensure_dirs():
    os.makedirs(RUNTIME_DIR, exist_ok=True)

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def emit_reflection(text: str, did: str = None, user: str = None, cg_pre: float | None = None):
    _ensure_dirs()
    if not text or not text.strip():
        raise ValueError("Reflection text is empty.")

    record = {
        "type": "NEW_REFLECTION",
        "timestamp": _now_iso(),
        "did": did or f"DID-{uuid.uuid4().hex[:8]}",
        "user": user or "local",
        "text": text.strip(),
    }
    if cg_pre is not None:
        record["cg_pre"] = float(cg_pre)

    with open(EVENTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record

def main():
    p = argparse.ArgumentParser(description="Emit a NEW_REFLECTION runtime event")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", type=str)
    src.add_argument("--file", type=str)
    p.add_argument("--did", type=str, default=None)
    p.add_argument("--user", type=str, default=None)
    p.add_argument("--cg-pre", type=float, default=None)
    args = p.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"[emitter] No such file: {args.file}", file=sys.stderr); sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text

    rec = emit_reflection(text=text, did=args.did, user=args.user, cg_pre=args.cg_pre)
    print(f"[emitter] NEW_REFLECTION emitted did={rec['did']} -> {EVENTS_PATH}")

if __name__ == "__main__":
    main()
