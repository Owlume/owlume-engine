# scripts/validate_aggregates.py
import os, sys, json, glob
from jsonschema import validate, Draft7Validator

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    schema_path = os.path.join(repo_root, "schemas", "aggregated_metrics.schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    metrics_dir = os.path.join(repo_root, "data", "metrics")
    files = sorted(glob.glob(os.path.join(metrics_dir, "aggregates_*.json")))
    if not files:
        print("No aggregate files to validate.")
        return

    ok = 0
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            doc = json.load(f)
        errors = sorted(Draft7Validator(schema).iter_errors(doc), key=lambda e: e.path)
        if errors:
            print(f"\n❌ {fp}")
            for e in errors:
                print(f" - {list(e.path)} → {e.message}")
        else:
            print(f"✅ {fp}")
            ok += 1
    print(f"\nValidation complete. {ok}/{len(files)} passed.")

if __name__ == "__main__":
    main()
