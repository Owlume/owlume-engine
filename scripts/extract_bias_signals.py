#!/usr/bin/env python
# --- repo path bootstrap ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# --- end bootstrap ---

import json
from src.bse.extract_bias_signals import extract_signals

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", help="Reflection JSON file; if omitted, read from stdin")
    args = ap.parse_args()

    if args.infile:
        data = Path(args.infile).read_text(encoding="utf-8")
    else:
        data = sys.stdin.read()

    ref = json.loads(data)
    signals = extract_signals(ref)
    print(json.dumps(signals, ensure_ascii=False))

if __name__ == "__main__":
    main()

