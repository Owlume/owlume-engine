"""
Owlume Script — aggregate_agent_memory.py
-----------------------------------------
Reads line-by-line runtime logs from:
    /data/runtime/agent_memory.jsonl
and produces a validated batch JSON snapshot at:
    /data/reports/agent_memory_snapshot.json

Usage:
    # aggregate only
    python -u scripts/aggregate_agent_memory.py

    # aggregate + auto-validate with your existing validator script
    python -u scripts/aggregate_agent_memory.py --validate
"""

import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# ----------------------------------------------------
# Config
# ----------------------------------------------------
RUNTIME_PATH = Path("data/runtime/agent_memory.jsonl")
REPORT_PATH = Path("data/reports/agent_memory_snapshot.json")
SCHEMA_PATH = "https://owlume-engine/schemas/learning_agent.schema.json"

VALIDATOR_SCRIPT = Path("scripts/validate_json.py")  # your existing validator
SCHEMA_FILE = Path("schemas/learning_agent.schema.json")  # local schema path for validator


def read_jsonl(path: Path):
    """Reads .jsonl file into a list of JSON objects."""
    records = []
    if not path.exists():
        print(f"[!] Runtime file not found: {path}")
        return records
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            try:
                records.append(json.loads(s))
            except json.JSONDecodeError as e:
                print(f"[x] Skipping malformed line {i}: {e}")
    return records


def write_snapshot(records):
    """Writes aggregated snapshot JSON with $schema + spec header."""
    snapshot = {
        "$schema": SCHEMA_PATH,
        "spec": {
            "name": "learning_agent",
            "version": "0.1.0",
            "stage": "Stage 4",
            "track": "L5",
            "created_with": "scripts/aggregate_agent_memory.py",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "notes": f"Aggregated {len(records)} learning records"
        },
        "records": records
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    print(f"[AGGREGATE] {len(records)} records → {REPORT_PATH}")


def run_validation():
    """Runs your existing validator on the snapshot (optional)."""
    if not VALIDATOR_SCRIPT.exists():
        print("[!] Skipping validation — validator script not found:", VALIDATOR_SCRIPT)
        return

    if not SCHEMA_FILE.exists():
        print("[!] Skipping validation — schema file not found:", SCHEMA_FILE)
        return

    cmd = [
        "python",
        str(VALIDATOR_SCRIPT),
        "--schemas",
        str(SCHEMA_FILE),
        "--data",
        str(REPORT_PATH)
    ]
    try:
        print("[VALIDATE] Running:", " ".join(cmd))
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.stdout:
            print(res.stdout.strip())
        if res.stderr:
            print(res.stderr.strip())
        if res.returncode == 0:
            print("✅ Validation passed.")
        else:
            print("❌ Validation failed (see messages above).")
    except Exception as e:
        print("[!] Validation error:", e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true", help="run schema validation after aggregating")
    args = parser.parse_args()

    records = read_jsonl(RUNTIME_PATH)
    if not records:
        print("[!] No records found to aggregate.")
        return

    write_snapshot(records)

    if args.validate:
        run_validation()


if __name__ == "__main__":
    main()
