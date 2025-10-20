#!/usr/bin/env python3
import json, sys
from pathlib import Path

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    repo_root = Path(".")
    schema_dir = repo_root / "schemas"
    data_dir = repo_root / "data"

    checks = [
        ("proof_of_clarity_delta_signals.schema.json", "proof_of_clarity_signals.json"),
        ("proof_of_clarity_insight_signals.schema.json", "proof_of_clarity_insight_signals.json"),
    ]

    try:
        import jsonschema
        from jsonschema import Draft7Validator
    except Exception:
        print("ERROR: Python package `jsonschema` is required. Install with:  pip install jsonschema", file=sys.stderr)
        sys.exit(2)

    ok = True
    for schema_name, data_name in checks:
        schema_path = schema_dir / schema_name
        data_path = data_dir / data_name

        if not schema_path.exists():
            print(f"[SKIP] Missing schema: {schema_path}")
            ok = False
            continue
        if not data_path.exists():
            print(f"[SKIP] Missing data: {data_path}")
            ok = False
            continue

        schema = load_json(schema_path)
        data = load_json(data_path)

        try:
            validator = Draft7Validator(schema)
            errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
            if errors:
                print(f"[FAIL] {data_name} ❌")
                for err in errors:
                    loc = " / ".join([str(x) for x in err.absolute_path]) or "<root>"
                    print(f"  - {loc}: {err.message}")
                ok = False
            else:
                print(f"[OK] {data_name} ✅")
        except Exception as e:
            print(f"[ERROR] {data_name}: {e}")
            ok = False

    if ok:
        print("All validations passed.")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
