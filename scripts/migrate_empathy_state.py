import json, pathlib, sys

IN_PATH  = pathlib.Path("data/logs/clarity_gain_samples.jsonl")
OUT_PATH = pathlib.Path("data/logs/clarity_gain_samples_migrated.jsonl")

def convert(val):
    if isinstance(val, str):
        if val.upper() == "ON":  return {"active": True}
        if val.upper() == "OFF": return {"active": False}
    return val  # already object or something else; leave untouched

def main():
    if not IN_PATH.exists():
        print(f"[x] not found: {IN_PATH}")
        return 1
    out_lines = []
    for i, line in enumerate(IN_PATH.read_text(encoding="utf-8-sig").splitlines(), 1):
        s = line.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
        except Exception:
            # keep non-JSON lines (headers) as-is
            out_lines.append(line)
            continue
        if "empathy_state" in obj:
            obj["empathy_state"] = convert(obj["empathy_state"])
        out_lines.append(json.dumps(obj, ensure_ascii=False))
    OUT_PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"[T-4] migrated → {OUT_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
