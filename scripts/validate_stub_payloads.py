#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Owlume SDK Stub payloads (JSON or JSONL) against /schemas/owlume_sdk_stub.schema.json.
Skips any file that declares a different $schema (eg. bridge_stub_v1.json).

Usage:
  python -u scripts/validate_stub_payloads.py
  python -u scripts/validate_stub_payloads.py --files data/contracts/mock_requests.jsonl data/contracts/mock_responses.jsonl
"""
import argparse, json, sys
from pathlib import Path
from typing import Iterable

try:
    import jsonschema
    from jsonschema import Draft7Validator
except Exception:
    print("[ERROR] jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

DEFAULT_SCHEMA = Path("schemas/owlume_sdk_stub.schema.json")
DEFAULT_DIR = Path("data/contracts")
SCHEMA_REF = "https://owlume/schemas/owlume_sdk_stub.schema.json"

def load_schema(schema_path: Path):
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)

def iter_records(path: Path) -> Iterable[tuple[int, dict]]:
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                yield i, json.loads(line)
    else:
        with path.open("r", encoding="utf-8") as f:
            yield 1, json.load(f)

def main():
    ap = argparse.ArgumentParser(description="Validate Owlume SDK Stub payloads.")
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    ap.add_argument("--files", type=Path, nargs="*", help="Specific files (.json or .jsonl)")
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR, help="Directory to scan if --files not provided")
    args = ap.parse_args()

    if not args.schema.exists():
        print(f"[ERROR] Schema not found: {args.schema}")
        sys.exit(1)

    validator = load_schema(args.schema)
    files = args.files or []
    if not files:
        if not args.dir.exists():
            print(f"[WARN] Directory not found: {args.dir}")
            sys.exit(0)
        files = sorted([p for p in args.dir.iterdir() if p.suffix.lower() in (".json", ".jsonl")])

    total = 0
    invalid = 0

    for file in files:
        count = 0
        file_invalid = 0
        for line_no, obj in iter_records(file):
            count += 1
            total += 1

            # Skip if file uses a different $schema
            if isinstance(obj, dict) and obj.get("$schema") != SCHEMA_REF:
                print(f"[SKIP] {file} #{line_no}: foreign schema {obj.get('$schema')}")
                continue

            errors = sorted(validator.iter_errors(obj), key=lambda e: e.path)
            if errors:
                invalid += 1
                file_invalid += 1
                print(f"[FAIL] {file} #{line_no}: {len(errors)} schema violation(s)")
                for e in errors[:5]:
                    path = "$" + "".join([f"[{repr(p)}]" if isinstance(p, int) else f".{p}" for p in e.path])
                    print(f"   - {path}: {e.message}")
        ok = count - file_invalid
        print(f"[FILE] {file} — records: {count}  ✓ valid: {ok}  ✗ invalid: {file_invalid}")

    if invalid == 0:
        print(f"[OK] All records valid. Total checked: {total}")
        sys.exit(0)
    else:
        print(f"[SUMMARY] Total checked: {total}  ✗ invalid: {invalid}")
        sys.exit(1)

if __name__ == "__main__":
    main()
