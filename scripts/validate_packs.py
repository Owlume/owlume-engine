import sys, json, pathlib, traceback
from jsonschema import Draft7Validator, RefResolver, exceptions
from xml.sax.saxutils import escape as xesc

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCHEMAS = ROOT / "schemas"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True, parents=True)


def load_json(p: pathlib.Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def schema_for(data_path: pathlib.Path):
    # Prefer explicit $schema in file; else try name-matching
    data = load_json(data_path)
    sch_ref = data.get("$schema")
    if sch_ref:
        # allow relative paths like ./schemas/foo.schema.json
        sp = (ROOT / sch_ref).resolve() if "schemas" in sch_ref else (SCHEMAS / pathlib.Path(sch_ref).name)
        if sp.exists():
            return load_json(sp), sp
    # fallback by filename heuristic: voices.json -> voices.schema.json
    guess = SCHEMAS / (data_path.stem + ".schema.json")
    if guess.exists():
        return load_json(guess), guess
    raise FileNotFoundError(f"No schema found for {data_path}")


def validate_file(dp: pathlib.Path):
    sch, sch_path = schema_for(dp)
    resolver = RefResolver.from_schema(sch, store={})
    validator = Draft7Validator(sch, resolver=resolver)
    errors = sorted(validator.iter_errors(load_json(dp)), key=lambda e: e.path)
    return errors, sch_path

def main():
    cases = []
    failures = 0

    # Skip folders that contain generated or temporary JSONs
    SKIP_DIRS = {"runtime", "metrics", "artifacts", "reports"}

    # Skip specific files that are indices, stubs, or backups (not core packs)
    SKIP_FILES = {
        DATA / "contracts" / "bridge_stub_v1.json",
        DATA / "indices" / "fallacy_alias_index.json",
        DATA / "nudges" / "nudge_templates.json",
        DATA / "weights" / "bias_signal_weights.json",
        DATA / "weights" / "empathy_weights_backup.json",
        DATA / "weights" / "runtime_clarity_weights.json",
    }

    for p in sorted(DATA.rglob("*.json")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p in SKIP_FILES:
            continue

        try:
            errs, sch_path = validate_file(p)
            if errs:
                failures += 1
                msg = "\n".join(f"- {list(e.path)}: {e.message}" for e in errs)
                cases.append((p, sch_path, False, msg))
            else:
                cases.append((p, sch_path, True, "OK"))
        except Exception as ex:
            failures += 1
            cases.append(
                (
                    p,
                    None,
                    False,
                    f"{type(ex).__name__}: {ex}\n{traceback.format_exc()}",
                )
            )

    # Emit JUnit XML for CI annotations / Test tab
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<testsuite name="json-validate">']
    for p, sch, ok, msg in cases:
        name = xesc(str(p.relative_to(ROOT)))
        xml.append(f'  <testcase name="{name}">')
        if not ok:
            xml.append(f'    <failure message="validation failed">{xesc(msg)}</failure>')
        xml.append("  </testcase>")
    xml.append("</testsuite>")
    (REPORTS / "json_validation.junit.xml").write_text(
        "\n".join(xml), encoding="utf-8"
    )

    # 🔧 NEW: print failing files + messages to stdout
    if failures:
        print("\n[L2] Detailed validation errors:")
        for p, sch, ok, msg in cases:
            if not ok:
                sch_str = str(sch.relative_to(ROOT)) if sch else "<?>"
                print(f"\n--- File: {p.relative_to(ROOT)}")
                print(f"    Schema: {sch_str}")
                print(msg)

        print(f"\n[L2] ❌ Validation failed — {failures} file(s) with errors.")
        sys.exit(1)

    print("[L2] ✅ All JSON validated OK.")


if __name__ == "__main__":
    main()

