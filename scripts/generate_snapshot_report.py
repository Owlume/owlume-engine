# scripts/generate_snapshot_report.py
# T5-S8 — Snapshot Report generator (7-day rollup)
# Reads:  data/metrics/aggregates_*.json
# Optional: data/metrics/aggregates_balance_*.json
# Writes: reports/stage5_snapshot_YYYY-MM-DD.md

import os, sys, glob, json, math
from datetime import datetime, timedelta
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(__file__))  # repo root
METRICS_DIR = os.path.join(ROOT, "data", "metrics")
RUNTIME_DIR = os.path.join(ROOT, "data", "runtime")
REPORTS_DIR = os.path.join(ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"__error__": f"{e!r}"}

def _file_mtime_dt(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path))
    except Exception:
        return datetime.min

def _pick_last_n_days(files, days=7):
    """Return files whose mtime within last N days, sorted ascending by mtime."""
    cutoff = datetime.now() - timedelta(days=days)
    scoped = [f for f in files if _file_mtime_dt(f) >= cutoff]
    return sorted(scoped, key=_file_mtime_dt)

def _fmt_pct(x):
    try:
        return f"{(100.0*float(x)):.1f}%"
    except Exception:
        return "—"

def _fmt_num(x, nd=3):
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return "—"

def _safe_get(d, *ks, default=None):
    cur = d
    for k in ks:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _date_str(dt):
    return dt.strftime("%Y-%m-%d")

def _collect_aggregates(days=7):
    agg_paths = glob.glob(os.path.join(METRICS_DIR, "aggregates_*.json"))
    agg_paths = _pick_last_n_days(agg_paths, days=days)

    daily = []
    for p in agg_paths:
        data = _read_json(p)
        ts = _file_mtime_dt(p)
        daily.append((ts, p, data))
    return daily

def _collect_balance(days=7):
    bal_paths = glob.glob(os.path.join(METRICS_DIR, "aggregates_balance_*.json"))
    bal_paths = _pick_last_n_days(bal_paths, days=days)
    daily = []
    for p in bal_paths:
        data = _read_json(p)
        ts = _file_mtime_dt(p)
        daily.append((ts, p, data))
    return daily

def _collect_insights(limit=12):
    jpath = os.path.join(RUNTIME_DIR, "insight_events.jsonl")
    events = []
    if not os.path.exists(jpath):
        return events
    try:
        with open(jpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    events.append(obj)
                except Exception:
                    continue
        # sort descending by timestamp if present
        def _key(o):
            t = o.get("timestamp") or ""
            try:
                return datetime.fromisoformat(t.replace("Z","+00:00"))
            except Exception:
                return datetime.min
        events.sort(key=_key, reverse=True)
        return events[:limit]
    except Exception:
        return events

def _mk_headline(daily_aggs):
    """Compute 7-day headline KPIs with simple averaging over available days."""
    if not daily_aggs:
        return {"avg_delta": None, "empathy": None, "positive": None}

    deltas = []
    empathy_rates = []
    positive_rates = []

    for _, _, data in daily_aggs:
        # these keys are examples from your previous runs; adapt if your schema differs
        d = _safe_get(data, "clarity", "avg_delta", default=_safe_get(data, "avg_delta"))
        e = _safe_get(data, "empathy", "activation_rate", default=_safe_get(data, "empathy_activation"))
        p = _safe_get(data, "clarity", "positive_rate", default=_safe_get(data, "positive_rate"))

        if isinstance(d, (int, float)):
            deltas.append(float(d))
        if isinstance(e, (int, float)):
            empathy_rates.append(float(e))
        if isinstance(p, (int, float)):
            positive_rates.append(float(p))

    def _avg(xs):
        return sum(xs)/len(xs) if xs else None

    return {
        "avg_delta": _avg(deltas),
        "empathy": _avg(empathy_rates),
        "positive": _avg(positive_rates),
    }

def _mk_mode_principle_table(daily_aggs, top_k=8):
    # Expect counts like data["top_counts"]["mode_principle"]["Analytical × Assumption"] = 12
    counter = Counter()
    for _, _, data in daily_aggs:
        mp = _safe_get(data, "top_counts", "mode_principle", default={}) or {}
        for k, v in mp.items():
            try:
                counter[k] += int(v)
            except Exception:
                continue
    top = counter.most_common(top_k)
    lines = []
    for k, v in top:
        lines.append(f"| {k} | {v} |")
    if not lines:
        lines.append("| — | — |")
    return "\n".join(lines)

def _mk_daily_rollup_rows(daily_aggs):
    rows = []
    for ts, path, data in daily_aggs:
        d = _safe_get(data, "clarity", "avg_delta", default=_safe_get(data, "avg_delta"))
        e = _safe_get(data, "empathy", "activation_rate", default=_safe_get(data, "empathy_activation"))
        p = _safe_get(data, "clarity", "positive_rate", default=_safe_get(data, "positive_rate"))
        rows.append(f"| {_date_str(ts)} | {_fmt_num(d)} | {_fmt_pct(e)} | {_fmt_pct(p)} |")
    if not rows:
        rows.append("| — | — | — | — |")
    return "\n".join(rows)

def _mk_balance_section(daily_balance):
    """Optional section if aggregates_balance files exist."""
    if not daily_balance:
        return None

    depth_vals, breadth_vals, drift_vals, tunnel_vals = [], [], [], []

    for ts, path, data in daily_balance:
        # Accept either flat or nested fields
        depth_vals.append(float(_safe_get(data, "depth_score", default=_safe_get(data, "human_ai","depth_score", default=0.0)) or 0.0))
        breadth_vals.append(float(_safe_get(data, "breadth_score", default=_safe_get(data, "human_ai","breadth_score", default=0.0)) or 0.0))
        drift_vals.append(float(_safe_get(data, "drift_index", default=_safe_get(data, "human_ai","drift_index", default=0.0)) or 0.0))
        tunnel_vals.append(float(_safe_get(data, "tunnel_index", default=_safe_get(data, "human_ai","tunnel_index", default=0.0)) or 0.0))

    def _avg(xs): return sum(xs)/len(xs) if xs else None
    return {
        "depth": _avg(depth_vals),
        "breadth": _avg(breadth_vals),
        "drift": _avg(drift_vals),
        "tunnel": _avg(tunnel_vals),
    }

def main():
    # 1) collect inputs
    daily_aggs = _collect_aggregates(days=7)
    daily_balance = _collect_balance(days=7)
    insights = _collect_insights(limit=10)

    # 2) compute KPIs
    head = _mk_headline(daily_aggs)
    mp_table = _mk_mode_principle_table(daily_aggs, top_k=10)
    daily_rows = _mk_daily_rollup_rows(daily_aggs)
    balance = _mk_balance_section(daily_balance)

    today = datetime.now().strftime("%Y-%m-%d")
    out_path = os.path.join(REPORTS_DIR, f"stage5_snapshot_{today}.md")

    # 3) render markdown
    lines = []
    lines.append(f"# Owlume — Stage 5 Snapshot • {today}")
    lines.append("")
    lines.append("> From reflection to reciprocity — Owlume learns **with** the user.")
    lines.append("")
    lines.append("## Headline KPIs (7-day average)")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Clarity Gain Δ (avg) | {_fmt_num(head['avg_delta'], nd=3)} |")
    lines.append(f"| Empathy Activation | {_fmt_pct(head['empathy'])} |")
    lines.append(f"| Positive Session Rate | {_fmt_pct(head['positive'])} |")
    lines.append("")

    if balance:
        lines.append("## Clarity Balance (Dual-Reasoning, 7-day avg)")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append(f"| Depth Score | {_fmt_num(balance['depth'], nd=3)} |")
        lines.append(f"| Breadth Score | {_fmt_num(balance['breadth'], nd=3)} |")
        lines.append(f"| Drift Index (breadth-over-depth) | {_fmt_num(balance['drift'], nd=3)} |")
        lines.append(f"| Tunnel Index (depth-over-breadth) | {_fmt_num(balance['tunnel'], nd=3)} |")
        lines.append("")

    lines.append("## Mode × Principle — Top Combined Counts (7-day)")
    lines.append("")
    lines.append("| Mode × Principle | Count |")
    lines.append("|---|---|")
    lines.append(mp_table)
    lines.append("")

    lines.append("## Daily Rollup (last 7 days)")
    lines.append("")
    lines.append("| Date | Δ (avg) | Empathy | Positive |")
    lines.append("|---|---:|---:|---:|")
    lines.append(daily_rows)
    lines.append("")

    if insights:
        lines.append("## Recent Insight Events")
        lines.append("")
        lines.append("| Type | DID | Mode | Principle | Δ | Timestamp |")
        lines.append("|---|---|---|---|---:|---|")
        for ev in insights:
            ev_type = ev.get("type","")
            did = ev.get("did","")
            mode = ev.get("mode","")
            prin = ev.get("principle","")
            cg = ev.get("cg_delta","")
            ts = ev.get("timestamp","")
            try:
                cg_str = _fmt_num(float(cg), nd=3)
            except Exception:
                cg_str = "—"
            lines.append(f"| {ev_type} | {did} | {mode} | {prin} | {cg_str} | {ts} |")
        lines.append("")

    # 4) write file
    content = "\n".join(lines).rstrip() + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[SNAPSHOT] Wrote {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
