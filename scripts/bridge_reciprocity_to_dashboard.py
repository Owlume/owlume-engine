#!/usr/bin/env python3
"""
S7-S4 — Learning Bridge & Dashboard Hook

Purpose:
- Watch /data/logs/reciprocity_events.jsonl for new events.
- Convert ecosystem reciprocity signals into live aggregates.
- Update /data/metrics/aggregates_runtime.json.
- Append a short cycle summary to /reports/S7-S4_learning_bridge_log.json.
- Nudge dashboard regeneration via dashboard watcher (best-effort).

Design notes:
- Stateless input (append-only JSONL); state tracked by last seen reciprocity_id(s).
- Conservative merges: we only touch the `reciprocity` section under aggregates_runtime.json
  and add a `vitals` section if missing.
- Safe to run repeatedly (idempotent for already-seen events).

Usage:
  python -u scripts/bridge_reciprocity_to_dashboard.py --once
  python -u scripts/bridge_reciprocity_to_dashboard.py --watch   # poll every N seconds

Requires Python 3.9+.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import subprocess

# ---- Paths (relative to repo root) -----------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
P_EVENTS = REPO_ROOT / "data" / "logs" / "reciprocity_events.jsonl"
P_STATE = REPO_ROOT / "data" / "metrics" / "bridge_state.json"
P_AGGR = REPO_ROOT / "data" / "metrics" / "aggregates_runtime.json"
P_LOG = REPO_ROOT / "reports" / "S7-S4_learning_bridge_log.json"
P_DASH_WATCH = REPO_ROOT / "scripts" / "dashboard_watch_runtime.py"

P_EVENTS.parent.mkdir(parents=True, exist_ok=True)
P_STATE.parent.mkdir(parents=True, exist_ok=True)
P_AGGR.parent.mkdir(parents=True, exist_ok=True)
P_LOG.parent.mkdir(parents=True, exist_ok=True)

# ---- Data models -----------------------------------------------------------
@dataclass
class ReciprocityEvent:
    reciprocity_id: str
    timestamp: str  # ISO8601
    clarity_effect: Optional[float] = None
    empathy_response: Optional[float] = None
    usage_context: str = "UNKNOWN"
    resulting_action: str = "UNKNOWN"
    did: Optional[str] = None
    user: Optional[str] = None

    @staticmethod
    def from_json(obj: Dict[str, Any]) -> Optional["ReciprocityEvent"]:
        # Accept variants where event payload nests under "learning" etc.
        rid = obj.get("reciprocity_id")
        ts = obj.get("timestamp") or obj.get("ts") or obj.get("ts_ingested")
        learning = obj.get("learning", {}) if isinstance(obj.get("learning"), dict) else {}

        # Map flexible fields
        ce = obj.get("clarity_effect")
        if ce is None:
            ce = learning.get("clarity_effect")
        if ce is None:
            # Fallback: use cg_post_ext - cg_pre_ext if available
            pre = obj.get("cg_pre_ext") or learning.get("cg_pre_ext")
            post = obj.get("cg_post_ext") or learning.get("cg_post_ext")
            try:
                if pre is not None and post is not None:
                    ce = float(post) - float(pre)
            except Exception:
                ce = None

        er = obj.get("empathy_response")
        if er is None:
            er = learning.get("empathy_response")
        if er is None:
            # Fallback: map from a 1–5 helpfulness scale if present
            helpfulness = obj.get("helpfulness") or learning.get("helpfulness")
            try:
                if helpfulness is not None:
                    # normalize 1..5 → 0..1
                    er = (float(helpfulness) - 1.0) / 4.0
            except Exception:
                er = None

        ctx = obj.get("usage_context") or learning.get("usage_context") or "UNKNOWN"
        act = obj.get("resulting_action") or learning.get("resulting_action") or "UNKNOWN"

        if not rid or not ts:
            return None
        return ReciprocityEvent(
            reciprocity_id=str(rid),
            timestamp=str(ts),
            clarity_effect=float(ce) if ce is not None else None,
            empathy_response=float(er) if er is not None else None,
            usage_context=str(ctx),
            resulting_action=str(act),
            did=obj.get("did"),
            user=obj.get("user"),
        )

# ---- Helpers ---------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # Skip malformed lines; do not crash the bridge
                continue

def read_state() -> Dict[str, Any]:
    if P_STATE.exists():
        try:
            return json.loads(P_STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"seen_ids": [], "last_run": None}

def write_state(state: Dict[str, Any]) -> None:
    P_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def read_aggregates() -> Dict[str, Any]:
    if P_AGGR.exists():
        try:
            return json.loads(P_AGGR.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def write_aggregates(obj: Dict[str, Any]) -> None:
    P_AGGR.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def append_cycle_log(payload: Dict[str, Any]) -> None:
    # We keep a compact JSON (not JSONL) with latest cycle at the end.
    try:
        if P_LOG.exists():
            existing = json.loads(P_LOG.read_text(encoding="utf-8"))
            if isinstance(existing, list):
                existing.append(payload)
            else:
                existing = [existing, payload]
        else:
            existing = [payload]
        P_LOG.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # Non-fatal
        pass

# ---- Core aggregation ------------------------------------------------------
@dataclass
class BridgeSummary:
    processed: int
    new_ids: List[str]
    last_event_ts: Optional[str]
    clarity_avg: Optional[float]
    empathy_avg: Optional[float]
    by_day: Dict[str, int]
    by_context: Dict[str, int]
    by_action: Dict[str, int]


def aggregate_new_events(state: Dict[str, Any]) -> BridgeSummary:
    seen_ids = set(state.get("seen_ids", []))

    new_events: List[ReciprocityEvent] = []
    for obj in load_jsonl(P_EVENTS):
        ev = ReciprocityEvent.from_json(obj)
        if not ev:
            continue
        if ev.reciprocity_id in seen_ids:
            continue
        new_events.append(ev)

    if not new_events:
        return BridgeSummary(
            processed=0,
            new_ids=[],
            last_event_ts=None,
            clarity_avg=None,
            empathy_avg=None,
            by_day={},
            by_context={},
            by_action={},
        )

    ids = []
    clarity_vals: List[float] = []
    empathy_vals: List[float] = []
    by_day: Dict[str, int] = defaultdict(int)
    ctx = Counter()
    act = Counter()
    last_ts_dt: Optional[datetime] = None

    for ev in new_events:
        ids.append(ev.reciprocity_id)
        if ev.clarity_effect is not None:
            clarity_vals.append(ev.clarity_effect)
        if ev.empathy_response is not None:
            empathy_vals.append(ev.empathy_response)
        # Normalize timestamp to date
        try:
            ts = datetime.fromisoformat(ev.timestamp.replace("Z", "+00:00"))
        except Exception:
            ts = datetime.now(timezone.utc)
        by_day[ts.date().isoformat()] += 1
        if last_ts_dt is None or ts > last_ts_dt:
            last_ts_dt = ts
        ctx[ev.usage_context] += 1
        act[ev.resulting_action] += 1

    clarity_avg = (sum(clarity_vals) / len(clarity_vals)) if clarity_vals else None
    empathy_avg = (sum(empathy_vals) / len(empathy_vals)) if empathy_vals else None

    last_event_ts = last_ts_dt.isoformat() if last_ts_dt else None

    return BridgeSummary(
        processed=len(new_events),
        new_ids=ids,
        last_event_ts=last_event_ts,
        clarity_avg=clarity_avg,
        empathy_avg=empathy_avg,
        by_day=dict(by_day),
        by_context=dict(ctx),
        by_action=dict(act),
    )


def merge_into_aggregates(summary: BridgeSummary) -> Dict[str, Any]:
    aggr = read_aggregates()

    # Ensure sections exist
    recip = aggr.setdefault("reciprocity", {
        "total_events": 0,
        "last_event_ts": None,
        "clarity_avg": None,
        "empathy_avg": None,
        "by_day": {},
        "by_context": {},
        "by_action": {},
    })

    # Roll-up counts
    recip["total_events"] = int(recip.get("total_events", 0)) + summary.processed
    recip["last_event_ts"] = summary.last_event_ts or recip.get("last_event_ts")

    # Update moving averages (simple incremental blend)
    def _blend(old: Optional[float], new: Optional[float]) -> Optional[float]:
        if new is None:
            return old
        if old is None:
            return new
        return round((old * 0.8) + (new * 0.2), 6)

    recip["clarity_avg"] = _blend(recip.get("clarity_avg"), summary.clarity_avg)
    recip["empathy_avg"] = _blend(recip.get("empathy_avg"), summary.empathy_avg)

    # Merge maps
    for d_key, inc in [("by_day", summary.by_day), ("by_context", summary.by_context), ("by_action", summary.by_action)]:
        base = recip.get(d_key, {})
        for k, v in inc.items():
            base[k] = int(base.get(k, 0)) + int(v)
        recip[d_key] = base

    # Provide a lightweight vitals surface for the dashboard to read
    vitals = aggr.setdefault("vitals", {})
    if recip.get("clarity_avg") is not None:
        vitals["Reciprocity ClarityΔ"] = round(float(recip["clarity_avg"]), 3)
    if recip.get("empathy_avg") is not None:
        vitals["Reciprocity Empathy"] = round(float(recip["empathy_avg"]) * 100.0, 1)  # percentage
    vitals["Reciprocity Events"] = int(recip.get("total_events", 0))

    write_aggregates(aggr)
    return aggr


def update_state(state: Dict[str, Any], summary: BridgeSummary) -> Dict[str, Any]:
    if summary.processed:
        seen = set(state.get("seen_ids", []))
        seen.update(summary.new_ids)
        state["seen_ids"] = sorted(seen)
    state["last_run"] = _now_iso()
    write_state(state)
    return state


def log_cycle(summary: BridgeSummary, aggr_after: Dict[str, Any]) -> None:
    payload = {
        "ts": _now_iso(),
        "processed": summary.processed,
        "new_ids": summary.new_ids,
        "last_event_ts": summary.last_event_ts,
        "clarity_avg_batch": summary.clarity_avg,
        "empathy_avg_batch": summary.empathy_avg,
        "snapshot_vitals": aggr_after.get("vitals", {}),
    }
    append_cycle_log(payload)


def nudge_dashboard_regen() -> None:
    """Attempt to trigger a one-off dashboard refresh. Best-effort, non-fatal."""
    if not P_DASH_WATCH.exists():
        return
    try:
        # Run watcher with --once so it updates reports/* if any changes are pending
        subprocess.run([sys.executable, str(P_DASH_WATCH), "--once"], check=False)
    except Exception:
        pass


# ---- CLI -------------------------------------------------------------------

def run_once(verbose: bool = False) -> int:
    state = read_state()
    summary = aggregate_new_events(state)
    if verbose:
        print(f"[S7-S4] new events: {summary.processed}")

    if summary.processed == 0:
        # Nothing to do, but still update last run timestamp
        update_state(state, summary)
        return 0

    aggr_after = merge_into_aggregates(summary)
    update_state(state, summary)
    log_cycle(summary, aggr_after)
    nudge_dashboard_regen()

    if verbose:
        print("[S7-S4] aggregates updated; vitals:")
        print(json.dumps(aggr_after.get("vitals", {}), ensure_ascii=False))
    return summary.processed


def run_watch(poll_seconds: int = 10, verbose: bool = True) -> None:
    print(f"[S7-S4] watch mode — polling every {poll_seconds}s (Ctrl+C to stop)…")
    try:
        while True:
            processed = run_once(verbose=verbose)
            # Light backoff if nothing was processed
            time.sleep(poll_seconds if processed == 0 else max(2, poll_seconds // 2))
    except KeyboardInterrupt:
        print("\n[S7-S4] watch stopped.")


def main():
    ap = argparse.ArgumentParser(description="S7-S4 Learning Bridge & Dashboard Hook")
    ap.add_argument("--once", action="store_true", help="Run a single ingestion cycle and exit")
    ap.add_argument("--watch", action="store_true", help="Run in watch mode (poll)")
    ap.add_argument("--poll", type=int, default=10, help="Polling seconds for --watch (default 10)")
    ap.add_argument("--quiet", action="store_true", help="Reduce stdout logs")
    args = ap.parse_args()

    if args.once and args.watch:
        print("Use either --once or --watch, not both.", file=sys.stderr)
        sys.exit(2)

    if args.watch:
        run_watch(poll_seconds=max(2, args.poll), verbose=not args.quiet)
    else:
        # Default to one-shot
        run_once(verbose=not args.quiet)


if __name__ == "__main__":
    main()
