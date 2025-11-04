# scripts/emit_ui_feedback.py
import argparse, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default="reports/runtime_feedback.log")
    ap.add_argument("--json", required=True, help="Feedback event JSON string or file path")
    args = ap.parse_args()

    raw = args.json
    if Path(raw).exists():
        data = json.loads(Path(raw).read_text(encoding="utf-8"))
    else:
        data = json.loads(raw)

    line = f"[UI_FEEDBACK] {data.get('type','EVENT')} • DID={data.get('did','?')} • Δ={data.get('cg_delta')} • {data.get('mode')} × {data.get('principle')}"
    Path(args.log).parent.mkdir(parents=True, exist_ok=True)
    with open(args.log, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)

if __name__ == "__main__":
    main()
