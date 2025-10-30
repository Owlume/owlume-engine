"""
Owlume Script — validate_json.py
--------------------------------
Validates JSON or JSONL data files against a specified JSON Schema.

Usage:
    python -u scripts/validate_json.py --schemas schemas/learning_agent.schema.json --data data/reports/agent_memory_snapshot.json
    python -u scripts/validate_json.py --schemas schemas/empathy_weights.schema.json --data data/weights/empathy_weights.json
"""

import json
import sys
import argparse
from pathlib import Path
from jsonschema import validate, ValidationError

# ----------------------------------------------------
# Safe output markers (no emojis for Windows consoles)
# ----------------------------------------------------
OK = "[OK]"
ERR = "[X]"
WARN = "[!]"

# ----------------------------------------------------
# Helper functions
# ----------------------------------------------------
def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            try:
                records.append(json.loads(s))
            except json.JSONDecodeError as e:
                print(f"{WARN} Skipping malformed line {i}: {e}")
    return records


def validate_file(schema_path, data_path):
    """Validate JSON or JSONL data against a schema. Returns True if all good."""
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # JSONL mode
    if data_path.suffix == ".jsonl":
        failed = False
        with open(data_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                s = line.strip()
                if not s:
                    continue
                try:
                    obj = json.loads(s)
                    validate(instance=obj, schema=schema)
                except ValidationError as err:
                    print(f"{ERR} L{i}: {err.message}")
                    failed = True
        if failed:
            return False
        print(f"{OK} JSONL validation finished → {data_path}")
        return True

    # JSON mode
    data = load_json(data_path)
    try:
        validate(instance=data, schema=schema)
        print(f"{OK} {data_path.name} validated successfully against {schema_path.name}")
        return True
    except ValidationError as err:
        print(f"{ERR} Validation error in {data_path}: {err.message}")
        return False


# ----------------------------------------------------
# CLI entry point
# ----------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schemas", required=True, help="Path to schema file")
    parser.add_argument("--data", required=True, help="Path to data file (.json or .jsonl)")
    args = parser.parse_args()

    schema_path = Path(args.schemas)
    data_path = Path(args.data)

    if not schema_path.exists():
        print(f"{ERR} Schema not found: {schema_path}")
        sys.exit(1)

    if not data_path.exists():
        print(f"{ERR} Data file not found: {data_path}")
        sys.exit(1)

    ok = False
    try:
        ok = validate_file(schema_path, data_path)
    except Exception as err:
        print(f"{ERR} Unexpected validation error: {err}")
        sys.exit(1)

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
