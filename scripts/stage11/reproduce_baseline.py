from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(".")
REPORTS = ROOT / "reports"
GOLDEN = ROOT / "data" / "golden" / "stage11_baseline_snapshot.json"
OUT = REPORTS / "stage12_repro_snapshot.json"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _run(cmd: list[str]) -> None:
    print("[RUN]", " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not GOLDEN.exists():
        raise FileNotFoundError(f"Missing golden baseline: {GOLDEN}")

    # Re-run pipeline to regenerate candidate snapshot deterministically
    _run([sys.executable, "scripts/stage11/run_pipeline_on_samples.py"])

    cand = REPORTS / "stage11_candidate_snapshot.json"
    if not cand.exists():
        raise FileNotFoundError(f"Pipeline did not write: {cand}")

    # Normalize JSON formatting to ensure stable bytes across runs
    obj = json.loads(cand.read_text(encoding="utf-8"))
    OUT.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    g = _sha256(GOLDEN)
    o = _sha256(OUT)

    if g != o:
        raise SystemExit(
            "Baseline mismatch.\n"
            f"golden: {GOLDEN} sha={g}\n"
            f"out   : {OUT} sha={o}\n"
        )

    print("[OK] Reproduced Stage 11 baseline snapshot exactly.")
    print(f"     Wrote: {OUT}  (byte-identical to {GOLDEN})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
