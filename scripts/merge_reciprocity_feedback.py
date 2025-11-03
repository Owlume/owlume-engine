#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge inbound reciprocity feedback into Owlume aggregates.

Reads JSONL events from /data/telemetry/reciprocity_feedback.jsonl,
validates against /schemas/reciprocity_feedback.schema.json,
de-dupes by reciprocity_id, and writes summary metrics to
/data/metrics/reciprocity_aggregates.json
and a tiny runtime state to /data/runtime/reciprocity_state.json.

Usage:
  python -u scripts/merge_reciprocity_feedback.py \
      --in data/telemetry/reciprocity_feedback.jsonl \
      --schema schemas/reciprocity_feedback.schema.json \
      --out data/metrics/reciprocity_aggregates.json \
      --state data/runtime/reciprocity_state.json
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict

# Optional dependency: jsonschema (nice-to-have)
try:
    import jsonschema  # type: ignore
    HAS_JSONSCHEMA = True
except Exception:
    HAS_JSONSCHEMA = False


def read_jsonl(path: Path):
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[WARN] Skipping invalid JSON at line {ln}: {e}", file=sys.stderr)
    return rows


def load_schema(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def validate_record(rec: dict, schema: dict | None) -> bool:
    # Basic structural checks first
    required = ["reciprocity_id", "usage_context", "clarity_effect", "empathy_response", "timestamp"]
    for k in required:
        if k not in rec:
            print(f"[WARN] Missing required field: {k} in record {rec.get('reciprocity_id','<no-id>')}", file=sys.stderr)
            return False

    # timestamp sanity
    try:
        datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
    except Exception:
        print(f"[WARN] Bad timestamp format in record {rec.get('reciprocity_id','<no-id>')}", file=sys.stderr)
        return False

    # Numeric fields
    try:
        float(rec["clarity_effect"])
        er = float(rec["empathy_response"])
        if not (0.0 <= er <= 1.0):
            print(f"[WARN] empathy_response out of range [0,1] in {rec.get('reciprocity_id')}", file=sys.stderr)
            return False
    except Exception:
        print(f"[WARN] Non-numeric clarity_effect/empathy_response in {rec.get('reciprocity_id')}", file=sys.stderr)
        return False

    # If jsonschema is present and schema provided, validate strictly
    if HAS_JSONSCHEMA and schema:
        try:
            jsonschema.validate(instance=rec, schema=schema)  # type: ignore
        except Exception as e:
            print(f"[WARN] Schema validation failed for {rec.get('reciprocity_id')}: {e}", file=sys.stderr)
            return False

    return True


def load_state(path: Path):
    if not path.exists():
        return {"processed_ids": []}
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {"processed_ids": []}


def save_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def aggregate(records: list[dict]):
    if not records:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "spec": {"version": "v0.1"},
            "timestamp": now,
            "total_events": 0,
            "unique_ids": 0,
            "avg_clarity_effect": 0.0,
            "avg_empathy_response": 0.0,
            "contexts": {},
            "actions": {},
            "last_event_at": None,
            "by_day_last14": {}
        }

        ids = set()
    clarity_vals = []
    empathy_vals = []
    ctx = Counter()
    act = Counter()

    by_day = defaultdict(int)

    def _parse_ts(s: str | None):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None

    for r in records:
        rid = r.get("reciprocity_id")
        if rid:
            ids.add(rid)

        ce = float(r.get("clarity_effect", 0))
        er = float(r.get("empathy_response", 0))
        clarity_vals.append(ce)
        empathy_vals.append(er)

        ctx[r.get("usage_context", "UNKNOWN")] += 1
        act[r.get("resulting_action", "UNKNOWN")] += 1

        ts = _parse_ts(r.get("timestamp"))
        if ts:
            by_day[ts.date().isoformat()] += 1

    # robust: max over all valid timestamps
    last_ts = max((t for t in (_parse_ts(r.get("timestamp")) for r in records) if t), default=None)

    # trim to last 14 days
    today = datetime.now(timezone.utc).date()
    last14 = {}
    for i in range(14):
        day = (today - timedelta(days=13 - i)).isoformat()
        last14[day] = by_day.get(day, 0)

    return {
        "spec": {"version": "v0.1"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_events": len(records),
        "unique_ids": len(ids),
        "avg_clarity_effect": sum(clarity_vals) / max(1, len(clarity_vals)),
        "avg_empathy_response": sum(empathy_vals) / max(1, len(empathy_vals)),
        "contexts": dict(ctx),
        "actions": dict(act),
        "last_event_at": last_ts.isoformat() if last_ts else None,
        "by_day_last14": last14
    }


def main():
    ap = argparse.ArgumentParser(description="Merge reciprocity feedback into aggregates.")
    ap.add_argument("--in", dest="in_path", default="data/telemetry/reciprocity_feedback.jsonl")
    ap.add_argument("--schema", dest="schema_path", default="schemas/reciprocity_feedback.schema.json")
    ap.add_argument("--out", dest="out_path", default="data/metrics/reciprocity_aggregates.json")
    ap.add_argument("--state", dest="state_path", default="data/runtime/reciprocity_state.json")
    ap.add_argument("--since", dest="since", default=None, help="ISO8601 lower bound (optional)")
    args = ap.parse_args()

    in_path = Path(args.in_path)
    schema_path = Path(args.schema_path)
    out_path = Path(args.out_path)
    state_path = Path(args.state_path)

    schema = load_schema(schema_path) if schema_path.exists() else None
    state = load_state(state_path)
    seen = set(state.get("processed_ids", []))

    raw = read_jsonl(in_path)

    # filter by since if provided
    if args.since:
        try:
            since_dt = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
            def _after(rec):
                try:
                    ts = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
                    return ts >= since_dt
                except Exception:
                    return False
            raw = [r for r in raw if _after(r)]
        except Exception:
            print("[WARN] --since not parseable; ignoring.", file=sys.stderr)

    # validate + de-dupe new ones
    new_records = []
    new_ids = []
    for r in raw:
        rid = r.get("reciprocity_id")
        if not rid or rid in seen:
            continue
        if validate_record(r, schema):
            new_records.append(r)
            new_ids.append(rid)

    if not new_records:
        print("[T7] No new valid reciprocity events to merge.")
        # Still emit aggregates for visibility (using all seen events would require storing them; we keep it simple)
        # Optional: Early exit.
        sys.exit(0)

    # Update seen state
    # Keep the state list bounded (e.g., last 50k ids)
    seen_list = list(seen) + new_ids
    if len(seen_list) > 50000:
        seen_list = seen_list[-50000:]
    state["processed_ids"] = seen_list

    # Aggregate *only* new records for a delta view; write a rolling aggregate file
    # If you want cumulative aggregates, you can keep a cumulative store; for now, we compute metrics on all events we have state for by re-reading file and filtering to seen ids
    cumulative = [r for r in raw if r.get("reciprocity_id") in set(seen_list)]
    agg = aggregate(cumulative)

    # Save outputs
    save_json(state_path, state)
    save_json(out_path, agg)

    print(f"[T7] Merged {len(new_records)} new reciprocity event(s).")
    print(f"[T7] Total unique ids: {agg['unique_ids']}")
    print(f"[T7] Averages: clarity_effect={agg['avg_clarity_effect']:.3f}  empathy_response={agg['avg_empathy_response']:.3f}")
    print(f"[T7] Last event at: {agg['last_event_at']}")


if __name__ == "__main__":
    main()
