#!/usr/bin/env python3
"""
Validate the Owlume Golden Set CSV against simple structural rules.

Usage:
  python tools/validate_golden_set.py data/owlume_golden_dilemmas_v1.csv

Checks:
- Required headers exist and in the expected order.
- id matches ^GD\d{2}$ and unique.
- dilemma length between 40 and 600 characters.
- expected_mode and expected_principle are non-empty strings.
- Optional: warn if trailing spaces or suspicious punctuation density.
- Emits a results CSV to data/qa_results/ with per-row pass/fail + notes.
"""

import sys, os, re, csv, datetime

EXPECTED_HEADERS = ["id", "dilemma", "expected_mode", "expected_principle"]
ID_PATTERN = re.compile(r"^GD[0-9]{2}$")

def soft_warns(text: str) -> list:
    warns = []
    if text.strip() != text:
        warns.append("leading/trailing spaces")
    if text.count("  ") > 2:
        warns.append("multiple double-spaces")
    # very high punctuation ratio might indicate pasted bullet soup
    letters = sum(ch.isalpha() for ch in text)
    punct = sum(ch in ",.;:!?-" for ch in text)
    if letters > 0 and (punct / max(letters,1)) > 0.25:
        warns.append("high punctuation ratio")
    return warns

def validate(csv_path: str) -> int:
    # Prepare output
    out_dir = os.path.join(os.path.dirname(csv_path), "qa_results")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    out_csv = os.path.join(out_dir, f"golden_set_validation_{stamp}.csv")

    errors = []
    seen_ids = set()
    rows_out = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        if headers != EXPECTED_HEADERS:
            errors.append(f"Header mismatch. Got {headers}, expected {EXPECTED_HEADERS}.")
        for i, row in enumerate(reader, start=2):  # row numbers counting header as line 1
            row_errors = []
            rid = row.get("id","")
            dilemma = row.get("dilemma","")
            mode = row.get("expected_mode","")
            principle = row.get("expected_principle","")

            if not ID_PATTERN.match(rid):
                row_errors.append("id format")
            if rid in seen_ids:
                row_errors.append("duplicate id")
            seen_ids.add(rid)

            dlen = len(dilemma or "")
            if dlen < 40 or dlen > 600:
                row_errors.append("dilemma length")
            if not (isinstance(mode, str) and mode.strip()):
                row_errors.append("empty expected_mode")
            if not (isinstance(principle, str) and principle.strip()):
                row_errors.append("empty expected_principle")

            warns = soft_warns(dilemma or "")
            status = "PASS" if not row_errors else "FAIL"
            rows_out.append({
                "row_num": i,
                "id": rid,
                "status": status,
                "errors": "; ".join(row_errors),
                "warnings": "; ".join(warns)
            })

    # write results
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["row_num","id","status","errors","warnings"])
        writer.writeheader()
        writer.writerows(rows_out)

    # summary
    total = len(rows_out)
    failed = sum(1 for r in rows_out if r["status"] == "FAIL")
    print(f"Validated {total} rows. Failures: {failed}. Results written to {out_csv}")
    if errors:
        print("Global errors:")
        for e in errors:
            print(" -", e)
        return 2
    return 1 if failed else 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/validate_golden_set.py data/owlume_golden_dilemmas_v1.csv")
        sys.exit(2)
    sys.exit(validate(sys.argv[1]))
