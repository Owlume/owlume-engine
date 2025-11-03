# src/helpers/merge_feedback.py
import statistics
from datetime import datetime, timezone

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def _init(aggr: dict) -> dict:
    aggr = dict(aggr or {})
    aggr.setdefault("meta", {"updated_at": _now_iso(), "source": "runtime"})
    aggr.setdefault("counts", {"events": 0, "nudges": 0})
    aggr.setdefault("clarity", {"avg_delta": 0.0, "samples": 0})
    aggr.setdefault("empathy", {"activation_rate": 0.0, "samples": 0})
    aggr.setdefault("top_cells", {})  # e.g., "Decision × Risk": count
    return aggr

def merge_feedback_into_aggregates(aggregates: dict, events: list[dict]) -> dict:
    aggr = _init(aggregates)
    deltas = []
    empathy_on = 0
    empathy_total = 0

    for ev in events:
        aggr["counts"]["events"] += 1

        # clarity delta
        d = ev.get("cg_delta")
        if isinstance(d, (int, float)):
            deltas.append(float(d))

        # empathy activation heuristic
        emp_bias = ev.get("empathy_bias")
        if isinstance(emp_bias, (int, float)):
            empathy_total += 1
            if abs(emp_bias) > 0.0:
                empathy_on += 1

        # mode × principle tally
        cell = None
        if ev.get("mode") and ev.get("principle"):
            cell = f'{ev["mode"]} × {ev["principle"]}'
            aggr["top_cells"][cell] = aggr["top_cells"].get(cell, 0) + 1

    # rolling clarity avg (weighted incremental)
    if deltas:
        # combine previous stats with new batch
        prev_avg = float(aggr["clarity"].get("avg_delta", 0.0))
        prev_n = int(aggr["clarity"].get("samples", 0))
        batch_avg = statistics.fmean(deltas)
        batch_n = len(deltas)
        new_avg = ((prev_avg * prev_n) + (batch_avg * batch_n)) / max(prev_n + batch_n, 1)
        aggr["clarity"]["avg_delta"] = round(new_avg, 4)
        aggr["clarity"]["samples"] = prev_n + batch_n

    if empathy_total > 0:
        prev_rate = float(aggr["empathy"].get("activation_rate", 0.0))
        prev_n = int(aggr["empathy"].get("samples", 0))
        batch_rate = empathy_on / empathy_total
        new_rate = ((prev_rate * prev_n) + (batch_rate * empathy_total)) / max(prev_n + empathy_total, 1)
        aggr["empathy"]["activation_rate"] = round(new_rate, 4)
        aggr["empathy"]["samples"] = prev_n + empathy_total

    aggr["meta"]["updated_at"] = _now_iso()
    return aggr
