#!/usr/bin/env python3
"""
Run all structural validations for the Owlume/Elenx repo.

Checks:
1) JSON schemas & config JSONs load + basic invariants
2) Python syntax/indent (tabnanny) for src/
3) Clarity logs JSONL validate against clarity_gain_record.schema.json (if present)
4) Critical module imports succeed

Exit codes:
- 0 = all good
- 1 = failure
"""

import os, sys, json, glob, traceback, importlib.util, subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
SCHEMAS = os.path.join(ROOT, "schemas")
DATA = os.path.join(ROOT, "data")
LOGS = os.path.join(DATA, "logs")
THRESH = os.path.join(DATA, "clarity_gain_thresholds.json")
CG_SCHEMA = os.path.join(SCHEMAS, "clarity_gain_record.schema.json")

def fail(msg, exc=None):
    print(f"❌ {msg}")
    if exc:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        print(tb)
    sys.exit(1)

def ok(msg):
    print(f"✅ {msg}")

def warn(msg):
    print(f"⚠️  {msg}")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_python_tabnanny(path):
    # Use tabnanny to detect indentation issues
    try:
        subprocess.check_call([sys.executable, "-m", "tabnanny", path])
    except subprocess.CalledProcessError as e:
        fail(f"tabnanny reported indentation/syntax problems in {path}.", e)

def check_import(module_name, extra_path=None):
    if extra_path and extra_path not in sys.path:
        sys.path.append(extra_path)
    try:
        __import__(module_name)
    except Exception as e:
        fail(f"Import failed for '{module_name}'.", e)

def validate_thresholds(path):
    obj = load_json(path)
    # Must have numeric low/medium/high, 0<=low<=medium<=high<=1
    for key in ("low", "medium", "high"):
        if key not in obj:
            fail(f"{path}: missing '{key}' key.")
        if not isinstance(obj[key], (int, float)):
            fail(f"{path}: '{key}' must be number.")
    low, med, high = obj["low"], obj["medium"], obj["high"]
    if not (0 <= low <= med <= high <= 1.0):
        fail(f"{path}: low/medium/high must satisfy 0 <= low <= medium <= high <= 1.0 (got {low}, {med}, {high}).")
    # meaningful_delta
    md = obj.get("meaningful_delta")
    if md is None or not isinstance(md, (int, float)) or not (0 <= md <= 1.0):
        fail(f"{path}: 'meaningful_delta' must be a number in [0,1].")
    ok("clarity_gain_thresholds.json structure looks good.")

def validate_logs_against_schema(schema_path, logs_dir):
    from jsonschema import Draft7Validator
    schema = load_json(schema_path)
    validator = Draft7Validator(schema)
    # Look for clarity_gain_*.jsonl
    files = sorted(glob.glob(os.path.join(logs_dir, "clarity_gain_*.jsonl")))
    if not files:
        warn("No clarity_gain_*.jsonl files found — skipping log validation.")
        return
    invalid = 0
    checked = 0
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                s = line.strip().lstrip("\ufeff")
                if not s or s.startswith("#") or s.startswith("//"):
                    continue
                try:
                    obj = json.loads(s)
                except json.JSONDecodeError as e:
                    print(f"❌ {fp}:{i} — JSON parse error: {e.msg}")
                    invalid += 1
                    continue
                errs = list(validator.iter_errors(obj))
                if errs:
                    print(f"❌ {fp}:{i} — {len(errs)} schema error(s):")
                    for e in errs:
                        path = "/".join([str(p) for p in e.path]) or "(root)"
                        print(f"   - {path} → {e.message}")
                    invalid += 1
                checked += 1
    if invalid:
        fail(f"Log validation found {invalid} invalid record(s) across {len(files)} file(s).")
    ok(f"Log validation passed ({checked} record(s) across {len(files)} file(s)).")

def main():
    print("🔎 Owlume / Elenx — validate_all\n")

    # 0) Ensure essential paths
    for p in [SRC, SCHEMAS, DATA]:
        if not os.path.isdir(p):
            fail(f"Required directory missing: {p}")

    # 1) Schema & thresholds JSON load + invariants
    if not os.path.isfile(CG_SCHEMA):
        fail(f"Missing clarity gain schema: {CG_SCHEMA}")
    load_json(CG_SCHEMA)
    ok("clarity_gain_record.schema.json loads.")

    if not os.path.isfile(THRESH):
        fail(f"Missing thresholds: {THRESH}")
    validate_thresholds(THRESH)

    # 2) Python syntax/indent checks (src/)
    check_python_tabnanny(SRC)
    ok("Python indentation/syntax (tabnanny) passed for src/.")

    # 3) Critical imports (src must be on sys.path)
    if SRC not in sys.path:
        sys.path.append(SRC)
    for mod in ("elenx_engine", "clarity_logger"):
        check_import(mod)
    ok("Critical imports passed (elenx_engine, clarity_logger).")

    # 4) Validate any logs against schema (optional but enforced if present)
    validate_logs_against_schema(CG_SCHEMA, LOGS)

    print("\n✅ All validations passed.")
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        fail("Unexpected error in validate_all.py", e)
