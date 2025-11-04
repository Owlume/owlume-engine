import argparse, json, sys, pathlib
from jsonschema import Draft7Validator

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--data", required=True)  # JSONL file
    args = ap.parse_args()

    schema = json.loads(pathlib.Path(args.schema).read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)

    data_path = pathlib.Path(args.data)
    if not data_path.exists():
        print(f"[x] data file not found: {data_path}")
        sys.exit(2)

    errors = 0
    with data_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                print(f"[x] L{i}: JSON parse error: {e}")
                errors += 1
                continue

            errs = sorted(validator.iter_errors(obj), key=lambda e: e.path)
            if errs:
                for e in errs:
                    loc = ".".join(str(p) for p in e.path) or "(root)"
                    print(f"[x] L{i}: {loc}: {e.message}")
                errors += 1

    if errors == 0:
        print(f"[✓] {data_path} — all lines validate against {args.schema}")
        return 0
    else:
        print(f"[!] {errors} line(s) failed validation")
        return 1

if __name__ == "__main__":
    sys.exit(main())
