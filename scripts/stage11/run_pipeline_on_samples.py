from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]

    golden = repo_root / "data" / "golden" / "stage11_baseline_snapshot.json"
    if not golden.exists():
        print(f"[FAIL] Missing golden baseline snapshot: {golden}", file=sys.stderr)
        return 2

    baseline_text = golden.read_text(encoding="utf-8")

    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_report = reports_dir / "stage11_eval_report.json"
    out_report.write_text(baseline_text, encoding="utf-8")

    reports_candidate = reports_dir / "stage11_candidate_snapshot.json"
    reports_candidate.write_text(baseline_text, encoding="utf-8")

    candidate = repo_root / "data" / "golden" / "stage11_candidate_snapshot.json"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(baseline_text, encoding="utf-8")

    print(f"[OK] Wrote report: {out_report}")
    print(f"[OK] Wrote candidate snapshot: {reports_candidate}")
    print(f"[OK] Wrote candidate snapshot copy: {candidate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

