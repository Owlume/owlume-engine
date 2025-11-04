#!/usr/bin/env python3
"""
S7-S6 — Ecosystem Learning Summary
Aggregates reciprocity feedback, computes rolling clarity/empathy, estimates bias-vector drift,
writes /reports/S7-S6_ecosystem_learning_summary.md, and can emit an ecosystem_insight nudge.

Usage:
  python -u scripts/aggregate_reciprocity_learning.py --once
  python -u scripts/aggregate_reciprocity_learning.py --days 14 --alpha 0.30 --emit-nudge --debug
"""

from __future__ import annotations
import argparse, glob, io, json, math, os, statistics
from datetime import datetime, timezone
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PATH_EVENTS_A   = os.path.join(ROOT, "data", "logs", "reciprocity_events.jsonl")
PATH_EVENTS_B   = os.path.join(ROOT, "data", "logs", "reciprocity_feedback.jsonl")   # optional
PATH_BALANCE_G  = os.path.join(ROOT, "data", "metrics", "aggregates_balance_*.json")
PATH_BSE        = os.path.join(ROOT, "data", "bse", "bias_vectors.jsonl")
PATH_REPORTS    = os.path.join(ROOT, "reports")
PATH_REPORT_OUT = os.path.join(ROOT, "reports", "S7-S6_ecosystem_learning_summary.md")
PATH_NUDGES     = os.path.join(ROOT, "data", "runtime", "nudge_events.jsonl")

def _read_jsonl(path: str) -> list[dict]:
    out = []
    if not os.path.exists(path): return out
    with io.open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out

def _read_json(path: str) -> dict | list | None:
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _ema(values: list[float], alpha: float) -> list[float]:
    if not values: return []
    ema = []
    s = values[0]
    for v in values:
        s = alpha * v + (1 - alpha) * s
        ema.append(s)
    return ema

def _slope(values: list[float]) -> float:
    """Simple least-squares slope against index (0..n-1)."""
    n = len(values)
    if n < 2: return 0.0
    x_mean = (n - 1) / 2
    y_mean = statistics.fmean(values)
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return 0.0 if den == 0 else num / den

def _euclidean(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a.keys()) & set(b.keys())
    if not keys: return 0.0
    return math.sqrt(sum((a[k] - b[k]) ** 2 for k in keys))

def _ensure_dirs():
    os.makedirs(PATH_REPORTS, exist_ok=True)
    os.makedirs(os.path.dirname(PATH_NUDGES), exist_ok=True)

def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=14, help="rolling window (days) for trends")
    p.add_argument("--alpha", type=float, default=0.25, help="EMA alpha (0..1)")
    p.add_argument("--emit-nudge", action="store_true", help="append ECOSYSTEM_INSIGHT to runtime nudges if patterns found")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--once", action="store_true", help="just run a single aggregation")
    return p.parse_args()

def _collect_events() -> list[dict]:
    evts = _read_jsonl(PATH_EVENTS_A)
    evts += _read_jsonl(PATH_EVENTS_B)
    # normalize a few likely field names
    norm = []
    for e in evts:
        ts = e.get("timestamp") or e.get("ts") or e.get("created_at")
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            dt = None
        ce = e.get("clarity_effect") or e.get("avg_clarity_effect") or e.get("ClarityΔ")
        er = e.get("empathy_response") or e.get("Empathy") or e.get("avg_empathy_response")
        try:
            ce = float(ce) if ce is not None else None
        except Exception:
            ce = None
        try:
            er = float(er) if er is not None else None
        except Exception:
            er = None
        if dt is None: continue
        norm.append({
            "timestamp": dt,
            "clarity_effect": ce,
            "empathy_response": er,
            "usage_context": e.get("usage_context") or e.get("source") or "UNKNOWN",
            "resulting_action": e.get("resulting_action") or "UNKNOWN",
        })
    norm.sort(key=lambda r: r["timestamp"])
    return norm

def _collect_balance_window(days:int) -> list[dict]:
    # read aggregates for context (optional)
    paths = sorted(glob.glob(PATH_BALANCE_G))
    out = []
    for p in paths[-min(len(paths), 50):]:
        j = _read_json(p)
        if isinstance(j, dict): out.append(j)
    return out

def _collect_bias_vectors() -> list[dict]:
    return _read_jsonl(PATH_BSE)

def _series_last_days(records: list[dict], key: str, days: int) -> list[float]:
    if not records: return []
    cutoff = (records[-1]["timestamp"] - timedelta_days(days))
    vals = [r[key] for r in records if r[key] is not None and r["timestamp"] >= cutoff]
    return vals

def timedelta_days(d: int):
    from datetime import timedelta
    return timedelta(days=d)

def format_pct(x: float | None) -> str:
    if x is None: return "—"
    return f"{x*100:.1f}%"

def format_spark(values: list[float], width: int = 18) -> str:
    """Tiny ascii sparkline (no extra deps)."""
    if not values: return "·" * max(3, min(width, 18))
    lo, hi = min(values), max(values)
    if hi - lo == 0:
        return "▁" * min(width, len(values))
    glyphs = "▁▂▃▄▅▆▇█"
    out = []
    for v in values[-width:]:
        idx = int((v - lo) / (hi - lo) * (len(glyphs)-1))
        out.append(glyphs[idx])
    return "".join(out)

def compute_bias_drift(bse_rows: list[dict]) -> float:
    """Distance between the last two bias vectors."""
    if len(bse_rows) < 2: return 0.0
    a = bse_rows[-2].get("vector", {})
    b = bse_rows[-1].get("vector", {})
    return _euclidean(a, b)

def main():
    args = _parse_args()
    _ensure_dirs()

    if args.debug:
        print("[S7-S6] start… days=", args.days, "alpha=", args.alpha)

    events = _collect_events()
    balances = _collect_balance_window(args.days)
    bse = _collect_bias_vectors()

    # build timeseries (last N days)
    ce_series = _series_last_days(events, "clarity_effect", args.days)
    er_series = _series_last_days(events, "empathy_response", args.days)

    if args.debug:
        print(f"[S7-S6] events={len(events)} ce_series={len(ce_series)} er_series={len(er_series)}")

    no_data = (len(events) == 0)

    # --- Clarity stats ---
    if ce_series:
        ce_ema = _ema(ce_series, args.alpha)
        ce_slope = _slope(ce_ema)
        clarity_avg = statistics.fmean(ce_series)
        ce_last = ce_ema[-1]
    else:
        ce_ema = []
        ce_slope = 0.0
        clarity_avg = 0.0
        ce_last = 0.0

    # --- Empathy stats ---
    if er_series:
        er_ema = _ema(er_series, args.alpha)
        er_slope = _slope(er_ema)
        empathy_avg = statistics.fmean(er_series)
        er_last = er_ema[-1]
    else:
        er_ema = []
        er_slope = 0.0
        empathy_avg = 0.0
        er_last = 0.0

    # Reciprocity Return Ratio (>0)
    return_ratio = 0.0
    if ce_series:
        return_ratio = sum(1 for v in ce_series if v and v > 0) / len(ce_series)

    # bias drift
    bias_drift = compute_bias_drift(bse)

    # context distribution (by bridge/source)
    by_ctx = defaultdict(int)
    for r in events:
        by_ctx[r["usage_context"]] += 1
    top_ctx = sorted(by_ctx.items(), key=lambda kv: kv[1], reverse=True)[:5]

    # Suggested nudge conditions (tune as needed)
    should_nudge = (er_slope > 0.002 and return_ratio >= 0.50) or (bias_drift > 0.25 and ce_slope > 0)

    now = datetime.now(timezone.utc).isoformat()

    # Message if there is no data in the window
    if no_data:
        learning_note = (
            "No reciprocity events were found in the last "
            f"{args.days} days. Vitals are shown as 0.000 by design; "
            "this summary is a structural heartbeat, not a learning update."
        )
    else:
        learning_note = (
            f"Clarity is "
            f"{'rising' if ce_slope > 0 else 'flattening' if abs(ce_slope) < 1e-4 else 'declining'} "
            f"with an EMA of {ce_last:.3f}. "
            f"Empathy is "
            f"{'rising' if er_slope > 0 else 'flattening' if abs(er_slope) < 1e-4 else 'declining'} "
            f"with an EMA of {er_last:.3f}. "
            f"Bias signature "
            f"{'shifted' if bias_drift > 0.0 else 'held steady'} with drift {bias_drift:.3f}."
        )

    # Compose report
    report = f"""# S7-S6 — Ecosystem Learning Summary

**Generated:** {now} (UTC)  
**Window:** Last {args.days} days • **EMA α = {args.alpha:.2f}**

## Vitals
- Rolling Clarity Δ (EMA last): {ce_last:.3f}  • trend slope: {ce_slope:+.4f}
- Rolling Empathy (EMA last):  {er_last:.3f}  • trend slope: {er_slope:+.4f}
- Reciprocity Return Ratio (>0): {format_pct(return_ratio)}
- Bias-Vector Drift (last→now, L2): {bias_drift:.3f}

**Clarity Δ spark:** `{format_spark(ce_ema)}`  
**Empathy spark:** `{format_spark(er_ema)}`

## What the System Is Learning
{learning_note}

## Bridge / Source Mix (last {args.days}d)
""" + "\n".join([f"- {k}: {v}" for k, v in top_ctx]) + """

## Balance Aggregates (context)
(Showing recent aggregate files; values summarized elsewhere)
""" + "\n".join([f"- {os.path.basename(p)}" for p in sorted(glob.glob(PATH_BALANCE_G))[-5:]]) + """

## Suggested Actions
- If empathy trend is positive and return ratio ≥ 50%, reinforce **empathy-aligned** questions in high-yield bridges.
- If bias drift rises while clarity trends up, surface **Bias Insight Cards** to make learning visible without friction.
- If clarity stalls and empathy falls, emit **recovery nudges** focusing on Evidence × Perspective.

## Overlay Notes
This report feeds the Dashboard v3 overlay:
- **Clarity Flow Map:** update nodes/edges with EMA clarity and source mix.
- **Reciprocity Insight Panel:** show empathy slope and return ratio badges.

"""

    if args.debug:
        print("[S7-S6] writing report →", PATH_REPORT_OUT)
    if not args.dry_run:
        with io.open(PATH_REPORT_OUT, "w", encoding="utf-8") as f:
            f.write(report)

    if args.emit_nudge and should_nudge and not args.dry_run and not no_data:
        evt = {
            "type": "ECOSYSTEM_INSIGHT",
            "reason": ("high_empathy_trend+return_ratio" if er_slope > 0 else "bias_drift+clarity_up"),
            "triggered_by": "S7-S6",
            "timestamp": now,
            "metrics": {
                "clarity_ema": ce_last if ce_series else None,
                "empathy_ema": er_last if er_series else None,
                "return_ratio": return_ratio,
                "bias_drift": bias_drift
            }
        }
        if args.debug:
            print("[S7-S6] emit nudge →", PATH_NUDGES, "|", evt)
        with io.open(PATH_NUDGES, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    if args.debug:
        print("[S7-S6] done.")

if __name__ == "__main__":
    main()