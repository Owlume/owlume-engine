#!/usr/bin/env python3
"""
Owlume — Schema Validator (draft-07)

Validates /data JSON files against /schemas JSON Schemas.
Resolution rules (in order):
  1) If a data file has a top-level "$schema" with a relative path → use it.
  2) Else, filename pairing: data/foo.json → schemas/foo.schema.json (if exists).
  3) Otherwise, skip with NOTICE.

Exit code:
  0: all validated or skipped with notices
  1: one or more validation errors or fatal issues

Usage:
  python -u scripts/validate_schemas.py
  python -u scripts/validate_schemas.py --strict   # treat notices as errors
"""

from __future__ import annotations
import argparse, json, sys, traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    from jsonschema import Draft7Validator, RefResolver, exceptions as js_ex
except Exception as e:
    print("::error ::jsonschema is not installed. Run: pip install jsonschema")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCHEMA_DIR = ROOT / "schemas"

# --- robust file reader: try utf-8, then utf-16, then latin-1 (last resort) ---
def read_json(path: Path) -> Tuple[Optional[dict], Optional[str]]:
    encodings = ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1")
    for enc in encodings:
        try:
            text = path.read_text(encoding=enc)
            return json.loads(text), enc
        except UnicodeError:
            continue
        except json.JSONDecodeError as e:
            print(f"::error ::Invalid JSON in {path} (encoding tried: {enc}): {e}")
            return None, enc
        except Exception as e:
            # Unexpected, try next encoding for UnicodeError only
            if isinstance(e, UnicodeError):
                continue
            print(f"::error ::Failed to read {path}: {e}")
            return None, None
    print(f"::error ::Unable to decode {path} with common encodings.")
    return None, None

def find_schema_for_data(data_path: Path, data_obj: dict) -> Optional[Path]:
    # Rule 1: honor $schema if it points to local file
    sch = data_obj.get("$schema")
    if isinstance(sch, str):
        # Allow relative paths like "../schemas/foo.schema.json" or "schemas/foo.schema.json"
        candidate = (data_path.parent / sch).resolve()
        if not candidate.exists():
            # Also try relative to repo root
            candidate = (ROOT / sch.lstrip("./")).resolve()
        if candidate.exists():
            return candidate

    # Rule 2: filename pairing
    candidate = SCHEMA_DIR / (data_path.stem + ".schema.json")
    if candidate.exists():
        return candidate

    return None

def load_schema(schema_path: Path) -> Optional[dict]:
    obj, enc = read_json(schema_path)
    return obj

def validate_one(data_path: Path, strict: bool) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    data_obj, enc = read_json(data_path)
    if data_obj is None:
        errs.append(f"{data_path} — cannot parse JSON.")
        return False, errs

    schema_path = find_schema_for_data(data_path, data_obj)
    if not schema_path:
        msg = f"NOTICE: {data_path} — no schema found (skipped)."
        if strict:
            errs.append(msg.replace("NOTICE: ", ""))
            return False, errs
        else:
            print(f"::notice ::{msg}")
            return True, []

    schema_obj = load_schema(schema_path)
    if schema_obj is None:
        errs.append(f"{data_path} — schema unreadable: {schema_path}")
        return False, errs

    # Prepare resolver so that $ref inside schemas can find neighbors
    resolver = RefResolver(base_uri=schema_path.parent.as_uri() + "/", referrer=schema_obj)
    validator = Draft7Validator(schema_obj, resolver=resolver)

    error_list = sorted(validator.iter_errors(data_obj), key=lambda e: e.path)
    if error_list:
        for e in error_list:
            loc = "/".join([str(p) for p in e.path]) or "(root)"
            errs.append(f"{data_path} :: {loc} :: {e.message}")
        return False, errs

    print(f"[ok] {data_path} ✓  (schema: {schema_path.name})")
    return True, []

def collect_data_files():
    if not DATA_DIR.exists():
        print("::notice ::data/ folder not found — nothing to validate.")
        return []

    ignore_dirs = {DATA_DIR / "runtime", DATA_DIR / "metrics"}
    files = []
    for p in DATA_DIR.rglob("*.json"):
        if not p.is_file():
            continue
        # OS-agnostic: skip if the file lives under any ignored dir
        if any(ig in p.parents for ig in ignore_dirs):
            continue
        files.append(p)
    return files

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="Treat notices (no schema) as errors.")
    args = ap.parse_args()

    if not SCHEMA_DIR.exists():
        print("::notice ::schemas/ folder not found — validation limited to $schema hints in data files.")

    data_files = collect_data_files()
    if not data_files:
        print("::notice ::No JSON files under /data to validate.")
        sys.exit(0)

    all_ok = True
    all_errs: List[str] = []

    print("=== Owlume — Schema Validation (draft-07) ===")
    print(f"Root: {ROOT}")
    print(f"Data files: {len(data_files)}\n")

    for dp in sorted(data_files):
        ok, errs = validate_one(dp, strict=args.strict)
        if not ok:
            all_ok = False
            all_errs.extend(errs)

    print("\n=== Summary ===")
    if all_ok:
        print("All validations passed (or were skipped with notices).")
        sys.exit(0)
    else:
        print(f"{len(all_errs)} error(s):")
        for e in all_errs:
            print(f"- {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
            print("::error ::Unhandled exception in validator:")
            print(traceback.format_exc())
            sys.exit(1)
