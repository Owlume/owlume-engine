"""
Owlume Script — validate_json.py
--------------------------------
Validates JSON or JSONL data files against a specified JSON Schema.

Usage:
    python -u scripts/validate_json.py --schemas schemas/learning_agent.schema.json --data data/reports/agent_memory_snapshot.json
    python -u scripts/validate_json.py --schemas schemas/empathy_weights.schema.json --data data/weights/empathy_weights.json
"""

import json
import os, glob
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

def expand_arg_paths(paths):
    expanded = []
    for p in paths:
        if os.path.isdir(p):
            if os.path.basename(p).lower() == "schemas":
                expanded += glob.glob(os.path.join(p, "*.schema.json"))
            else:
                expanded += glob.glob(os.path.join(p, "**", "*.json"), recursive=True)
        elif any(ch in p for ch in "*?[]"):
            expanded += glob.glob(p, recursive=True)
        else:
            expanded.append(p)
    # de-dupe + keep only files
    return [x for x in dict.fromkeys(expanded) if os.path.isfile(x)]

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
    import argparse, sys, json
    from pathlib import Path
    import jsonschema  # ensure this is installed
    # assumes expand_arg_paths(paths: List[str]) is already defined above

    parser = argparse.ArgumentParser(
        description="Validate JSON data files against JSON Schemas."
    )
    parser.add_argument(
        "--schemas", nargs="+", required=True,
        help="Schema files, globs, or directories (e.g., schemas or schemas/*.schema.json)"
    )
    parser.add_argument(
        "--data", nargs="+", required=True,
        help="Data files, globs, or directories (e.g., data or data/**/*.json)"
    )
    args = parser.parse_args()

    # Expand directories and globs into concrete file lists
    args.schemas = expand_arg_paths(args.schemas)
    args.data    = expand_arg_paths(args.data)

    if not args.schemas:
        raise SystemExit("[X] No schema files found after expansion.")
    if not args.data:
        raise SystemExit("[X] No data files found after expansion.")

    # Build a lookup for data files by basename
    data_by_name = {Path(p).name: p for p in args.data}

    any_failed = False
    total_checks = 0

    for schema_path_str in args.schemas:
        schema_path = Path(schema_path_str)
        schema_name = schema_path.name

        # Load schema
        try:
            with schema_path.open("r", encoding="utf-8") as f:
                schema = json.load(f)
        except Exception as e:
            print(f"[X] Failed to read schema {schema_name}: {e}")
            any_failed = True
            continue

        # Heuristic mapping: matrix.schema.json → matrix.json, etc.
        stem = schema_path.stem.replace(".schema", "")
        candidates = [f"{stem}.json", f"{stem}.jsonc"]  # add more if you use them

        # Select targets: matching file(s) if present; else validate *all* data JSONs
        targets = [data_by_name[n] for n in candidates if n in data_by_name]
        if not targets:
            # fall back to all .json files (skip .jsonl)
            targets = [p for p in args.data if p.lower().endswith(".json")]

        if not targets:
            print(f"[!] No data files found to validate for schema {schema_name}")
            continue

        for data_path_str in targets:
            data_path = Path(data_path_str)
            if data_path.suffix.lower() == ".jsonl":
                continue  # skip JSONL in this validator

            # Load data
            try:
                with data_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[X] Failed to read data {data_path.name}: {e}")
                any_failed = True
                continue

            # Validate
            try:
                jsonschema.validate(instance=data, schema=schema)
                print(f"[✓] {data_path.name} — valid against {schema_name}")
            except Exception as e:
                print(f"[X] {data_path.name} — INVALID against {schema_name}: {e}")
                any_failed = True
            finally:
                total_checks += 1

    if total_checks == 0:
        print("[!] No validations were performed (no matching data files).")
        raise SystemExit(1 if any_failed else 0)

    if any_failed:
        raise SystemExit(1)

    print("All validations completed.")


if __name__ == "__main__":
    main()
