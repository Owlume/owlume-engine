import json, sys
from jsonschema import Draft7Validator

SCHEMA_PATH = "schemas/clarity_gain_record.schema.json"

def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/validate_clarity_jsonl.py <jsonl_path>")
        sys.exit(1)
    jsonl = sys.argv[1]
    schema = json.load(open(SCHEMA_PATH, "r", encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    v = Draft7Validator(schema)

    errs = n = 0
    with open(jsonl, "r", encoding="utf-8-sig") as f:  # tolerate BOM if present
        for i, raw in enumerate(f, 1):
            s = raw.strip().lstrip("\ufeff")            # extra safety
            if not s:
                continue
            obj = json.loads(s); n += 1
            e = list(v.iter_errors(obj))
            if e:
                errs += 1
                print(f"[INVALID] line {i}:")
                for ee in e:
                    path = "/".join(map(str, ee.path)) or "<root>"
                    print(f"  → {path} - {ee.message}")

    if errs == 0:
        print(f"[OK] {jsonl}: all {n} records valid")
    else:
        print(f"[FAIL] {jsonl}: {errs} invalid of {n}")
        sys.exit(2)

if __name__ == "__main__":
    main()
