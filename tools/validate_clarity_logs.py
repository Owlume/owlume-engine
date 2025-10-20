# tools/validate_clarity_logs.py
import sys, json, glob, os
from datetime import datetime

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("Missing dependency: jsonschema\nInstall with: pip install jsonschema")
    sys.exit(1)

SCHEMA_PATH = os.path.join("schemas", "clarity_gain_record.schema.json")
DATA_GLOB   = os.path.join("data", "logs", "*.jsonl")

# Load schema
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    schema = json.load(f)
validator = Draft7Validator(schema)

failures = 0
checked  = 0

for fp in glob.glob(DATA_GLOB):
    with open(fp, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[ERROR] {fp}:{i} invalid JSON: {e}")
                failures += 1
                continue

            errors = sorted(validator.iter_errors(obj), key=lambda e: e.path)
            if errors:
                failures += 1
                print(f"[FAIL]  {fp}:{i}")
                for e in errors:
                    loc = "/".join(map(str, e.path)) or "(root)"
                    print(f"       ↳ {loc}: {e.message}")
            else:
                checked += 1

stamp = datetime.now().isoformat(timespec="seconds")
if failures:
    print(f"\nSummary @ {stamp}: {checked} valid, {failures} failed.")
    sys.exit(1)
else:
    print(f"All good @ {stamp}: {checked} valid, 0 failed.")
