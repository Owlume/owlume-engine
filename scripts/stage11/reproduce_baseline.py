from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> None:
    # Cross-platform: do not rely on shell quoting; use cwd for stable relative paths.
    printable = " ".join(str(x) for x in cmd)
    print(f"[RUN] {printable}")
    subprocess.check_call(cmd, cwd=str(cwd))


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]

    golden = repo_root / "data" / "golden" / "stage11_baseline_snapshot.json"
    if not golden.exists():
        raise FileNotFoundError(f"Missing golden baseline: {golden}")

    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Pipeline runner expected to generate these:
    eval_report = reports_dir / "stage11_eval_report.json"
    cand_report = reports_dir / "stage11_candidate_snapshot.json"

    pipeline = repo_root / "scripts" / "stage11" / "run_pipeline_on_samples.py"
    if not pipeline.exists():
        raise FileNotFoundError(f"Missing pipeline runner script: {pipeline}")

    # Run pipeline (cross-platform)
    _run([sys.executable, str(pipeline)], cwd=repo_root)

    # Enforce pipeline outputs exist (the contract CI is checking)
    if not eval_report.exists():
        raise FileNotFoundError(f"Pipeline did not write: {eval_report}")
    if not cand_report.exists():
        raise FileNotFoundError(f"Pipeline did not write: {cand_report}")

    # Byte-identical contract: compare bytes, not parsed JSON.
    golden_bytes = golden.read_bytes()
    eval_bytes = eval_report.read_bytes()

    if eval_bytes != golden_bytes:
        print("[FAIL] Reproduced Stage 11 baseline does not match golden snapshot (byte mismatch).", file=sys.stderr)
        print(f"Golden : {golden}", file=sys.stderr)
        print(f"Eval   : {eval_report}", file=sys.stderr)
        return 1

    # Write the stage12 reproduction artifact (byte-identical to golden)
    out = reports_dir / "stage12_repro_snapshot.json"
    out.write_bytes(eval_bytes)

    print("[OK] Reproduced Stage 11 baseline snapshot exactly.")
    print(f"     Wrote: {out.relative_to(repo_root)}  (byte-identical to {golden.relative_to(repo_root)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
