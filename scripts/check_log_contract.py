# scripts/check_log_contract.py
from __future__ import annotations

import glob
import json
import os
import sys
import re
from typing import Any, Dict


def fail(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"✅ {msg}")


def load_jsonl(path: str):
    with open(path, "r", encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            try:
                yield i, json.loads(s)
            except Exception as e:
                fail(f"{path}:{i} invalid JSON: {e}")


def main() -> None:
    logs_dir = os.path.join("data", "logs")
    files = sorted(
        f for f in glob.glob(os.path.join(logs_dir, "clarity_gain_*.jsonl"))
        if os.path.basename(f)[-11:-5] >= "202601"
    )
    LOG_PATTERN = re.compile(r"^clarity_gain_(\d{6})\.jsonl$")

    files = sorted(
        f for f in glob.glob(os.path.join(logs_dir, "clarity_gain_*.jsonl"))
        if (m := LOG_PATTERN.match(os.path.basename(f)))
        and m.group(1) >= "202601"
    )

    if not files:
        ok("No clarity_gain_*.jsonl files found — nothing to check.")
        return

    bad = 0
    checked = 0

    for fp in files:
        for lineno, rec in load_jsonl(fp):
            checked += 1

            # 1) Root JTS is forbidden
            if "judgment_terminal_state" in rec:
                bad += 1
                print(f"❌ {fp}:{lineno} — root judgment_terminal_state is forbidden")

            # 2) judgment_landing is mandatory
            jl = rec.get("judgment_landing")
            if not isinstance(jl, dict):
                bad += 1
                print(f"❌ {fp}:{lineno} — missing judgment_landing")

            # 3) detected.judgment_terminal_state is mandatory
            det = rec.get("detected")
            if not isinstance(det, dict):
                bad += 1
                print(f"❌ {fp}:{lineno} — missing detected")
            else:
                jts = det.get("judgment_terminal_state")
                if not isinstance(jts, dict):
                    bad += 1
                    print(f"❌ {fp}:{lineno} — missing detected.judgment_terminal_state")

    if bad:
        fail(f"Contract check failed: {bad} issue(s) across {checked} record(s).")

    ok(f"Contract check passed: {checked} record(s) across {len(files)} file(s).")


if __name__ == "__main__":
    main()
