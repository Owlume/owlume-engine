from __future__ import annotations

import json
from pathlib import Path

from src.stage11.pipeline import run_on_samples


SAMPLES = [
    {"id": "false_dichotomy", "text": "We either cut costs or grow revenue. There are no other options."},
    {"id": "undefined_success", "text": "This project must be a success. Let's move fast."},
    {"id": "strong_claim_no_ur", "text": "This will definitely increase revenue by 30% in 6 months. It is clearly the best option."},
]


def main() -> int:
    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)

    result = run_on_samples(SAMPLES)

    # Write a deterministic eval report + candidate snapshot
    (out_dir / "stage11_eval_report.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "stage11_candidate_snapshot.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print("Wrote -> reports/stage11_eval_report.json")
    print("Wrote -> reports/stage11_candidate_snapshot.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

