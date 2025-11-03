import argparse
import csv
import datetime
import glob
import json
import os
from collections import defaultdict
from pathlib import Path


def latest_json(pattern: str):
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def load_json(path: str):
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_bse_vectors(path: str):
    """
    Load bias_signature entries from data/bse/bias_vectors.jsonl.
    Returns a list of (user, vector_dict).
    """
    results = []
    if not os.path.exists(path):
        return results

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            user = obj.get("user")
            vec = obj.get("vector") or {}
            if isinstance(vec, dict):
                results.append((user, vec))
    return results


def summarize_bse(vectors):
    """
    Given a list of (user, vector_dict),
    return mean per dimension and count.
    """
    if not vectors:
        return {"dimensions": {}, "n_vectors": 0}

    dim_sums = defaultdict(float)
    dim_counts = defaultdict(int)

    for _user, vec in vectors:
        for dim, val in vec.items():
            try:
                v = float(val)
            except (TypeError, ValueError):
                continue
            dim_sums[dim] += v
            dim_counts[dim] += 1

    means = {}
    for dim, total in dim_sums.items():
        if dim_counts[dim]:
            means[dim] = total / dim_counts[dim]

    return {"dimensions": means, "n_vectors": len(vectors)}


def build_export(partner: bool = False,
                 partner_id: str | None = None,
                 label: str | None = None):
    out_dir = Path("exports")
    out_dir.mkdir(exist_ok=True)

    # 1. Load latest aggregates
    latest_balance = latest_json("data/metrics/aggregates_balance_*.json")
    reciprocity_path = "data/metrics/reciprocity_aggregates.json"

    balance_data = load_json(latest_balance) if latest_balance else {}
    reciprocity_data = load_json(reciprocity_path)

    # 2. Core metrics summary (keys based on existing vitals)
    summary = {
        "clarity_delta_avg": round(float(balance_data.get("Δavg", 0.0)), 3),
        "empathy_activation_rate": round(float(balance_data.get("Empathy", 0.0)), 3),
        "bias_drift_index": round(float(balance_data.get("Drift", 0.0)), 3),
        "positive_outcome_rate": round(float(balance_data.get("Positive", 0.0)), 3),
    }

    export = {
        "export_spec": {
            "version": "v1.0",
            "generated": datetime.datetime.utcnow().isoformat() + "Z",
            "source_stage": "S8-S3",
            "mode": "partner" if partner else "internal",
        },
        "metrics_summary": summary,
    }

    # 3. Attach reciprocity summary if present (already aggregate / safe)
    if reciprocity_data:
        export["reciprocity_summary"] = reciprocity_data

    # 4. BSE handling — internal vs partner
    bse_path = "data/bse/bias_vectors.jsonl"
    bse_vectors = load_bse_vectors(bse_path)

    if partner:
        # Partner mode: no user IDs; only aggregated bias dimensions
        export["bse_summary"] = summarize_bse(bse_vectors)
    else:
        # Internal mode: include a small sample to debug / inspect
        max_samples = 10
        samples = []
        for user, vec in bse_vectors[:max_samples]:
            samples.append(
                {
                    "user": user,
                    "vector": vec,
                }
            )
        export["bse_samples"] = samples
        export["bse_summary"] = summarize_bse(bse_vectors)

    # 5. Optional partner metadata
    if partner:
        export["partner"] = {
            "partner_id": partner_id or "external",
            "label": label or "partner_export",
            "export_scope": "aggregates_only",  # no raw user IDs or events
        }

    return export


def write_outputs(export: dict):
    out_dir = Path("exports")
    out_dir.mkdir(exist_ok=True)

    # JSON
    json_path = out_dir / "owlume_insights.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2)

    # CSV summary
    csv_path = out_dir / "owlume_insights.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for k, v in export.get("metrics_summary", {}).items():
            w.writerow([k, v])

    print(f"[S8-S3] Exported → {json_path} and {csv_path}")


def main():
    parser = argparse.ArgumentParser(
        description="S8-S3 — Insight Export Bridge (JSON + CSV)"
    )
    parser.add_argument(
        "--partner",
        action="store_true",
        help="Partner-safe export (aggregates only, no user IDs).",
    )
    parser.add_argument(
        "--partner-id",
        type=str,
        help="Optional partner identifier to include in the export.",
    )
    parser.add_argument(
        "--label",
        type=str,
        help="Optional human-friendly label for this export run.",
    )
    args = parser.parse_args()

    export = build_export(
        partner=args.partner,
        partner_id=args.partner_id,
        label=args.label,
    )
    write_outputs(export)


if __name__ == "__main__":
    main()
