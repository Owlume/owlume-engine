#!/usr/bin/env python3
"""
Owlume — L3-S1 Data Prep

Prepare a clean, analysis-ready dataset for the Clarity Gain Analytics Dashboard v2.

Inputs
- /data/logs/clarity_gain_samples.jsonl           (session-level logs; newline-delimited JSON)
- /data/metrics/aggregates_*.json                 (aggregate snapshots produced by T4 pipeline)

Outputs
- /data/metrics/clarity_gain_dashboard.json       (row-per-session JSON for interactive charts)
- /data/metrics/clarity_gain_dashboard.csv        (same as CSV for quick inspection)
- /data/metrics/clarity_gain_dashboard.schema.json (JSON Schema describing the output rows)

Notes
- Lightweight, standard-library + pandas only.
- Robust to missing fields and older log formats.
- Adds convenience fields: cg_tier, empathy_on (bool), mode_principle key.

Usage
  python -u scripts/prepare_dashboard_data.py \
    --logs data/logs/clarity_gain_samples.jsonl \
    --aggregates_glob "data/metrics/aggregates_*.json" \
    --out_json data/metrics/clarity_gain_dashboard.json \
    --out_csv data/metrics/clarity_gain_dashboard.csv
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import sys
import datetime as dt
from typing import Any, Dict, List

import pandas as pd

REQUIRED_LOG_FIELDS = [
    "timestamp",          # ISO 8601
    "did",                # session/dilemma id
    "mode_detected",
    "principle_detected",
    "cg_pre",
    "cg_post",
    "cg_delta",
]

OPTIONAL_LOG_FIELDS = [
    "empathy_state",      # on|off|auto|-
    "empathy_ratio",
    "notes",
]


def _iso_to_dt(s: str) -> pd.Timestamp:
    try:
        return pd.to_datetime(s, utc=True, errors="coerce")
    except Exception:
        return pd.NaT


def load_logs_jsonl(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        print(f"[L3-S1] WARN: logs file not found: {path}")
        return pd.DataFrame(columns=REQUIRED_LOG_FIELDS + OPTIONAL_LOG_FIELDS)

    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                records.append(obj)
            except json.JSONDecodeError as e:
                print(f"[L3-S1] WARN: skip bad JSON line {i}: {e}")

    df = pd.DataFrame.from_records(records)

    # Fill missing columns to be resilient to older logs
    for col in REQUIRED_LOG_FIELDS + OPTIONAL_LOG_FIELDS:
        if col not in df.columns:
            df[col] = pd.NA

    # Coerce types
    df["timestamp"] = df["timestamp"].apply(_iso_to_dt)
    for c in ["cg_pre", "cg_post", "cg_delta", "empathy_ratio"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Normalize empathy_state
    def norm_emp(s: Any) -> str:
        if pd.isna(s):
            return "-"
        s = str(s).strip().lower()
        if s in {"on", "off", "auto", "-"}:
            return s
        return "-"

    df["empathy_state"] = df["empathy_state"].map(norm_emp)

    # Convenience fields
    df["empathy_on"] = df["empathy_state"].isin(["on", "auto"])  # treat auto as on for ratios
    df["mode"] = df.get("mode_detected", pd.Series([pd.NA]*len(df)))
    df["principle"] = df.get("principle_detected", pd.Series([pd.NA]*len(df)))
    df["mode_principle"] = df["mode"].fillna("-") + " × " + df["principle"].fillna("-")

    # Clarity gain tiering for quick filtering
    def cg_tier(v: Any) -> str:
        try:
            x = float(v)
        except (TypeError, ValueError):
            return "unknown"
        if x <= 0.0:
            return "≤0"
        if x < 0.1:
            return "+0–0.1"
        if x < 0.2:
            return "+0.1–0.2"
        if x < 0.3:
            return "+0.2–0.3"
        return ">=+0.3"

    df["cg_tier"] = df["cg_delta"].map(cg_tier)

    # Final sort
    df = df.sort_values("timestamp", ascending=True, na_position="last").reset_index(drop=True)
    return df


def load_aggregates(glob_pattern: str) -> pd.DataFrame:
    paths = sorted(glob.glob(glob_pattern))
    if not paths:
        print(f"[L3-S1] INFO: No aggregates found for pattern: {glob_pattern}")
        return pd.DataFrame(columns=["stamp", "avg_pre", "avg_post", "avg_delta", "empathy_rate"])  # minimal

    frames = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            # Heuristic: accept our T4 aggregate shape
            stamp = d.get("timestamp") or d.get("generated_at") or d.get("stamp")
            avg_pre = d.get("avg_pre") or d.get("pre_avg") or d.get("AVG_pre") or d.get("AVG_pre")
            avg_post = d.get("avg_post") or d.get("post_avg")
            avg_delta = d.get("avg_delta") or d.get("delta_avg") or d.get("AVG_delta")
            empathy_rate = d.get("empathy_activation_rate") or d.get("empathy_rate")
            frames.append({
                "stamp": stamp,
                "avg_pre": avg_pre,
                "avg_post": avg_post,
                "avg_delta": avg_delta,
                "empathy_rate": empathy_rate,
                "_source": os.path.basename(p),
            })
        except Exception as e:
            print(f"[L3-S1] WARN: failed reading aggregate {p}: {e}")
    ag = pd.DataFrame(frames)
    if not ag.empty:
        ag["stamp"] = ag["stamp"].apply(_iso_to_dt)
        ag = ag.sort_values("stamp").reset_index(drop=True)
    return ag


def write_outputs(df: pd.DataFrame, out_json: str, out_csv: str, out_schema: str) -> None:
    # Ensure directory exists
    for path in [out_json, out_csv, out_schema]:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    # Minimal column selection for dashboard
    cols = [
        "timestamp", "did", "mode", "principle", "mode_principle",
        "cg_pre", "cg_post", "cg_delta", "cg_tier",
        "empathy_state", "empathy_on", "empathy_ratio",
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA

    # Convert timestamps to ISO strings for JSON/CSV
    df_out = df.copy()
    df_out["timestamp"] = df_out["timestamp"].apply(
        lambda x: x.isoformat().replace("+00:00", "Z") if isinstance(x, pd.Timestamp) and not pd.isna(x) else ""
    )

    # Write JSON (list of objects)
    records = df_out[cols].to_dict(orient="records")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # Write CSV
    df_out[cols].to_csv(out_csv, index=False)

    # Emit a simple JSON Schema alongside for validation in VS Code
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "clarity_gain_dashboard.schema.json",
        "title": "Owlume Clarity Gain Dashboard — Row Schema",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "timestamp": {"type": "string"},
                "did": {"type": "string"},
                "mode": {"type": ["string", "null"]},
                "principle": {"type": ["string", "null"]},
                "mode_principle": {"type": "string"},
                "cg_pre": {"type": ["number", "null"]},
                "cg_post": {"type": ["number", "null"]},
                "cg_delta": {"type": ["number", "null"]},
                "cg_tier": {"type": "string"},
                "empathy_state": {"type": "string"},
                "empathy_on": {"type": ["boolean", "null"]},
                "empathy_ratio": {"type": ["number", "null"]}
            },
            "required": ["timestamp", "did", "mode_principle", "cg_delta"],
            "additionalProperties": True
        }
    }
    with open(out_schema, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare dashboard dataset for L3.")
    parser.add_argument("--logs", default="data/logs/clarity_gain_samples.jsonl")
    parser.add_argument("--aggregates_glob", default="data/metrics/aggregates_*.json")
    parser.add_argument("--out_json", default="data/metrics/clarity_gain_dashboard.json")
    parser.add_argument("--out_csv", default="data/metrics/clarity_gain_dashboard.csv")
    parser.add_argument("--out_schema", default="data/metrics/clarity_gain_dashboard.schema.json")
    args = parser.parse_args()

    print("[L3-S1] Loading logs…", args.logs)
    df_logs = load_logs_jsonl(args.logs)
    print(f"[L3-S1] Logs loaded: {len(df_logs)} rows")

    print("[L3-S1] Loading aggregates…", args.aggregates_glob)
    df_ag = load_aggregates(args.aggregates_glob)
    if not df_ag.empty:
        # Join aggregate info at nearest timestamp window if needed later
        # For now, we keep aggregates separate (S2/S3 can reference df_ag as needed)
        print(f"[L3-S1] Aggregates loaded: {len(df_ag)} snapshots (kept separate)")
    else:
        print("[L3-S1] No aggregates loaded (ok).")

    if df_logs.empty:
        print("[L3-S1] No session logs found — emitting empty outputs.")

    write_outputs(df_logs, args.out_json, args.out_csv, args.out_schema)

    # Quick summary to console
    if not df_logs.empty:
        n = len(df_logs)
        cg_mean = pd.to_numeric(df_logs["cg_delta"], errors="coerce").dropna().mean()
        emp_rate = float(df_logs["empathy_on"].mean()) if "empathy_on" in df_logs else 0.0
        print(f"[L3-S1] Sessions: {n}  |  avg Δ={cg_mean:.3f}  |  empathy_on rate={emp_rate:.3f}")

    print("[L3-S1] Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
