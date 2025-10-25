# scripts/validate_clarity_metrics.py
# Validates data/clarity_metrics_summary.json against schemas/clarity_metrics.schema.json

import json, os, sys
from datetime import datetime

# UTF-8 safety for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    from jsonschema import Draft7Validator, validate
except ImportError:
    print("Please install jsonschema: pip install jsonschema")
    sys.exit(1)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SUMMARY_PATH = os.path.join(ROOT, "data", "clarity_metrics_summary.json")
SCHEMA_PATH  = os.path.join(ROOT, "schemas", "clarity_metrics.schema.json")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    if not os.path.exists(SUMMARY_PATH):
        print(f"❌ Summary not found: {SUMMARY_PATH}")
        print("Hint: run your aggregator to produce data/clarity_metrics_summary.json first.")
        sys.exit(2)
    if not os.path.exists(SCHEMA_PATH):
        print(f"❌ Schema not found: {SCHEMA_PATH}")
        sys.exit(2)

    schema = load_json(SCHEMA_PATH)
    data   = load_json(SUMMARY_PATH)

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if errors:
        print("❌ Validation failed with the following issues:")
        for e in errors:
            loc = ".".join([str(x) for x in e.path]) or "(root)"
            print(f" - {loc}: {e.message}")
        sys.exit(3)
    else:
        print("✅ clarity_metrics_summary.json conforms to clarity_metrics.schema.json")
        # Light sanity ping
        ps, pe = data.get("period_start"), data.get("period_end")
        cg = data.get("cg_avg")
        print(f"Period: {ps} → {pe} | cg_avg={cg}")

if __name__ == "__main__":
    main()
