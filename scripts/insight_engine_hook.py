#!/usr/bin/env python3
"""
Owlume — L3-S5 Insight Engine Hook

Scans the L3-S1 dashboard dataset + optional aggregates to detect notable patterns
and appends compact events to DilemmaNet runtime logs for later tuning.

Detections (baseline set)
- HIGH_CG_SESSION: any session with cg_delta >= HI_CG_THRESHOLD (default 0.30)
- NEGATIVE_REGRESSION: any session with cg_delta <= NEG_CG_THRESHOLD (default -0.05)
- DAILY_SHIFT: latest day activation vs 7-day mean differs by >= EMP_SHIFT (default 0.20)
- MODE_PRINCIPLE_SPIKE: combo count on latest day >= MP_MIN and >= Pct change vs 7-day mean (default +200%)

Inputs
- --in_json data/metrics/clarity_gain_dashboard.json        (L3-S1 output)
- --aggregates_glob "data/metrics/aggregates_*.json"        (optional)

Outputs
- --out_jsonl data/runtime/insight_events.jsonl             (append-only)

Usage
  python -u scripts/insight_engine_hook.py \
    --in_json data/metrics/clarity_gain_dashboard.json \
    --aggregates_glob "data/metrics/aggregates_*.json" \
    --out_jsonl data/runtime/insight_events.jsonl

Event shape (one line JSON):
{
  "timestamp": "2025-10-26T04:10:00Z",
  "type": "pattern_detected",
  "pattern": "HIGH_CG_SESSION",
  "detail": {"did": "did_...", "cg_delta": 0.34, "mode": "Assumption", "principle": "Impact"}
}

Notes
- Idempotent by design if you pass --dedupe_window_days (default 7): events with the same
  key within the window are not re-emitted.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

UTC = dt.timezone.utc


@dataclass
class Thresholds:
    HI_CG_THRESHOLD: float = 0.30
    NEG_CG_THRESHOLD: float = -0.05
    EMP_SHIFT: float = 0.20
    MP_MIN: int = 2
    MP_SPIKE_FACTOR: float = 2.0  # >= 200% of 7d mean


def iso_now() -> str:
    return dt.datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load_dashboard(path: str) -> pd.DataFrame:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame.from_records(data)
    if df.empty:
        return df
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
    for c in ['cg_pre','cg_post','cg_delta','empathy_ratio']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df['mode'] = df.get('mode', pd.Series([None]*len(df))).fillna('-')
    df['principle'] = df.get('principle', pd.Series([None]*len(df))).fillna('-')
    df['date'] = df['timestamp'].dt.date
    return df.sort_values('timestamp').reset_index(drop=True)


def safe_read_existing(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return []
    out: List[Dict[str, Any]] = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # skip bad lines
                pass
    return out


def write_append_jsonl(path: str, events: Iterable[Dict[str, Any]]) -> None:
    if not events:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def dedupe_recent(events: List[Dict[str, Any]], new_events: List[Dict[str, Any]], window_days: int) -> List[Dict[str, Any]]:
    if not new_events:
        return []
    # Build recent key set
    cutoff = dt.datetime.now(UTC) - dt.timedelta(days=window_days)
    existing_keys = set()
    for ev in events:
        ts = ev.get('timestamp')
        try:
            t = dt.datetime.fromisoformat(ts.replace('Z','+00:00')) if ts else None
        except Exception:
            t = None
        if t and t >= cutoff:
            k = (ev.get('type'), ev.get('pattern'), json.dumps(ev.get('detail', {}), sort_keys=True))
            existing_keys.add(k)
    out: List[Dict[str, Any]] = []
    for ev in new_events:
        k = (ev.get('type'), ev.get('pattern'), json.dumps(ev.get('detail', {}), sort_keys=True))
        if k not in existing_keys:
            out.append(ev)
    return out


def detect_events(df: pd.DataFrame, th: Thresholds) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    now = iso_now()
    if df.empty:
        return events

    # 1) High CG sessions
    highs = df[df['cg_delta'] >= th.HI_CG_THRESHOLD]
    for _, r in highs.iterrows():
        events.append({
            'timestamp': now,
            'type': 'pattern_detected',
            'pattern': 'HIGH_CG_SESSION',
            'detail': {
                'did': r.get('did'),
                'cg_delta': float(r.get('cg_delta', 0) or 0),
                'mode': r.get('mode'),
                'principle': r.get('principle'),
            }
        })

    # 2) Negative regressions
    lows = df[df['cg_delta'] <= th.NEG_CG_THRESHOLD]
    for _, r in lows.iterrows():
        events.append({
            'timestamp': now,
            'type': 'pattern_detected',
            'pattern': 'NEGATIVE_REGRESSION',
            'detail': {
                'did': r.get('did'),
                'cg_delta': float(r.get('cg_delta', 0) or 0),
                'mode': r.get('mode'),
                'principle': r.get('principle'),
            }
        })

    # Build daily frame
    dfd = df.copy()
    dfd['date'] = dfd['timestamp'].dt.date
    daily_emp = dfd.groupby('date')['empathy_on'].mean(numeric_only=True).reset_index(name='activation_rate')
    daily_cnt = dfd.groupby('date')['did'].count().reset_index(name='sessions')

    if len(daily_emp) >= 2:
        latest_date = daily_emp['date'].max()
        prev7 = daily_emp[daily_emp['date'] < latest_date].tail(7)
        if not prev7.empty:
            latest_rate = float(daily_emp[daily_emp['date'] == latest_date]['activation_rate'].iloc[0])
            mean_prev = float(prev7['activation_rate'].mean())
            if abs(latest_rate - mean_prev) >= th.EMP_SHIFT:
                events.append({
                    'timestamp': now,
                    'type': 'pattern_detected',
                    'pattern': 'DAILY_SHIFT',
                    'detail': {
                        'metric': 'empathy_activation',
                        'latest_date': str(latest_date),
                        'latest_rate': round(latest_rate, 3),
                        'prev7_mean': round(mean_prev, 3),
                        'delta': round(latest_rate - mean_prev, 3),
                    }
                })

    # 4) Mode×Principle spike on latest day
    dfg = dfd.groupby(['date','mode','principle']).size().reset_index(name='count')
    if not dfg.empty:
        latest_date = dfd['date'].max()
        today = dfg[dfg['date'] == latest_date]
        prev = dfg[dfg['date'] < latest_date]
        if not today.empty and not prev.empty:
            prev7 = prev[prev['date'] >= (latest_date - dt.timedelta(days=7))]
            if not prev7.empty:
                base = (prev7.groupby(['mode','principle'])['count'].mean()).rename('prev7_mean').reset_index()
                merged = today.merge(base, on=['mode','principle'], how='left')
                for _, r in merged.iterrows():
                    c = int(r['count'])
                    mean_prev = float(r.get('prev7_mean') or 0)
                    if c >= th.MP_MIN and (mean_prev == 0 and c >= th.MP_MIN or (mean_prev > 0 and c >= th.MP_SPIKE_FACTOR * mean_prev)):
                        events.append({
                            'timestamp': now,
                            'type': 'pattern_detected',
                            'pattern': 'MODE_PRINCIPLE_SPIKE',
                            'detail': {
                                'date': str(latest_date),
                                'mode': r['mode'],
                                'principle': r['principle'],
                                'count_today': c,
                                'prev7_mean': round(mean_prev, 3),
                                'factor_vs_prev7': round((c / mean_prev) if mean_prev > 0 else float('inf'), 2),
                            }
                        })

    return events


def main() -> int:
    ap = argparse.ArgumentParser(description='Emit insight events from dashboard data (L3-S5).')
    ap.add_argument('--in_json', default='data/metrics/clarity_gain_dashboard.json')
    ap.add_argument('--aggregates_glob', default='data/metrics/aggregates_*.json')
    ap.add_argument('--out_jsonl', default='data/runtime/insight_events.jsonl')
    ap.add_argument('--dedupe_window_days', type=int, default=7)
    ap.add_argument('--hi', type=float, default=0.30, help='High CG threshold')
    ap.add_argument('--neg', type=float, default=-0.05, help='Negative CG threshold')
    ap.add_argument('--emp', type=float, default=0.20, help='Empathy shift threshold')
    ap.add_argument('--mpmin', type=int, default=2, help='Min count for a Mode×Principle spike')
    ap.add_argument('--mpfactor', type=float, default=2.0, help='Spike factor vs 7d mean')
    args = ap.parse_args()

    th = Thresholds(
        HI_CG_THRESHOLD=args.hi,
        NEG_CG_THRESHOLD=args.neg,
        EMP_SHIFT=args.emp,
        MP_MIN=args.mpmin,
        MP_SPIKE_FACTOR=args.mpfactor,
    )

    df = load_dashboard(args.in_json)
    existing = safe_read_existing(args.out_jsonl)

    new_events = detect_events(df, th)
    if args.dedupe_window_days > 0:
        new_events = dedupe_recent(existing, new_events, args.dedupe_window_days)

    write_append_jsonl(args.out_jsonl, new_events)

    print(f"[L3-S5] events_emitted={len(new_events)}  → {args.out_jsonl}")
    # Quick preview
    for ev in new_events[:5]:
        typ = ev.get('pattern'); det = ev.get('detail', {})
        print(f" - {typ}: {json.dumps(det, ensure_ascii=False)}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
