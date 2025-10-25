#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aggregates clarity logs into a single metrics snapshot expected by L1 update_weights.py.

Outputs -> data/metrics/aggregates_YYYYMMDD_HHMMSS.json with keys:
- avg_pre, avg_post, avg_delta
- empathy_activation_rate
- n_records
- top_mode_principle_counts: { "mode": {...}, "principle": {...} }

Back-compat: prints human summary similar to your previous version.
"""

import json, glob, datetime as dt
from pathlib import Path
from collections import Counter

PRINCIPLE_TO_MODE = {
    "Evidence & Validation": "Analytical",
    "Assumption": "Analytical",
    "Efficiency": "Analytical",
    "Action": "Analytical",
    "Risk": "Critical",
    "Impact": "Critical",
    "Stakeholder": "Critical",
    "Exploration": "Creative",
    "Root Cause": "Reflective",
    "Iteration": "Growth",
    # add others if you introduce more principles later
}

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "data" / "logs"
OUT_DIR = ROOT / "data" / "metrics"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _normalize_mode(name: str) -> str | None:
    """
    Normalize common mode variants to canonical labels.
    Returns None if we cannot confidently map it.
    """
    if not name:
        return None
    s = str(name).strip()
    if s == "-" or not s:
        return None

    # case-insensitive canonical map
    CANON = {
        "analytical": "Analytical",
        "critical": "Critical",
        "creative": "Creative",
        "reflective": "Reflective",
        "growth": "Growth",
    }
    # exact (case-insensitive)
    key = s.lower()
    if key in CANON:
        return CANON[key]

    # contains-based heuristics (handles "Analytical Mode", "mode: critical", etc.)
    for k, v in CANON.items():
        if k in key:
            return v

    return None  # unknown

def _as_bool(x):
    # Accepts True/False, "ON"/"OFF", "true"/"false", 1/0
    if isinstance(x, bool): return x
    if isinstance(x, (int, float)): return bool(x)
    if isinstance(x, str):
        s = x.strip().lower()
        if s in {"on", "true", "yes", "y", "1"}: return True
        if s in {"off", "false", "no", "n", "0"}: return False
    return False

def load_records():
    """Load JSONL logs from data/logs/*.jsonl; tolerant to UTF-8 BOM; print diagnostics."""
    paths = sorted(glob.glob(str(LOG_DIR / "*.jsonl")))
    recs, total_lines, skipped_empty, parse_errors = [], 0, 0, 0
    first_err = None

    for p in paths:
        # utf-8-sig auto-strips BOM if present
        with open(p, "r", encoding="utf-8-sig") as f:
            for line in f:
                total_lines += 1
                s = (line or "").strip()
                if not s:
                    skipped_empty += 1
                    continue
                try:
                    obj = json.loads(s)
                    if isinstance(obj, dict):
                        recs.append(obj)
                except Exception as e:
                    parse_errors += 1
                    if first_err is None:
                        first_err = f"{type(e).__name__}: {e}"
                    continue

    print(f"[AGG] files={len(paths)} lines={total_lines} ok={len(recs)} empty={skipped_empty} errors={parse_errors}")
    if first_err:
        print(f"[AGG] first parse error: {first_err}")
    return recs, paths

def aggregate(recs):
    n = 0
    pre_sum = post_sum = delta_sum = 0.0
    empathy_on = 0

    from collections import Counter
    mode_counts = Counter()
    prin_counts = Counter()

    ALLOWED_MODES = {"Analytical", "Critical", "Creative", "Reflective", "Growth"}
    KNOWN_PRINCIPLES = {
        "Assumption", "Evidence & Validation", "Stakeholder", "Stakeholders",
        "Exploration", "Root Cause", "Iteration", "Risk", "Impact", "Evidence"
    }

    for r in recs:
        if not isinstance(r, dict):
            continue
        # --- numeric fields (tolerant)
        pre  = r.get("cg_pre",  r.get("clarity_pre",  0.0)) or 0.0
        post = r.get("cg_post", r.get("clarity_post", 0.0)) or 0.0
        delt = r.get("cg_delta")
        if delt is None:
            try:
                delt = float(post) - float(pre)
            except Exception:
                delt = 0.0

        # --- labels
        mode = r.get("mode_detected", r.get("mode", "-")) or "-"
        prin = r.get("principle_detected", r.get("principle", "-")) or "-"

        # normalize principle aliases
        if prin == "Stakeholders": prin = "Stakeholder"
        if prin == "Clarity": prin = "Evidence & Validation"
        if prin == "Efficiency": prin = "Evidence & Validation"
        if prin == "Evidence":   prin = "Evidence & Validation"
        if prin == "Action": prin = "Evidence & Validation"

        # fix swapped fields (principle mistakenly in mode)
        if mode not in ALLOWED_MODES and mode in KNOWN_PRINCIPLES and (prin == "-" or prin not in KNOWN_PRINCIPLES):
            prin = mode
            mode = "-"

        # empathy flag
        emp = r.get("empathy_state", r.get("empathy", r.get("empathy_on", False)))
        empb = str(emp).strip().lower() in {"true","1","on","yes","y"} if isinstance(emp, str) else bool(emp)

        # accumulate metrics
        n += 1
        try:
            pre_sum  += float(pre)
            post_sum += float(post)
            delta_sum += float(delt)
        except Exception:
            pass
        if empb:
             empathy_on += 1

        # tally (normalize + infer mode from principle; skip placeholders)
        norm_mode = _normalize_mode(mode)

        # infer mode from principle when missing/unknown
        if not norm_mode and prin in PRINCIPLE_TO_MODE:
            norm_mode = PRINCIPLE_TO_MODE[prin]

        if norm_mode:
            mode_counts[norm_mode] += 1
        if prin != "-":
            prin_counts[prin] += 1

    if n == 0:
        return {
            "avg_pre": 0.0, "avg_post": 0.0, "avg_delta": 0.0,
            "empathy_activation_rate": 0.0, "n_records": 0,
            "top_mode_principle_counts": {"mode": {}, "principle": {}}
        }

    avg_pre = pre_sum / n
    avg_post = post_sum / n
    avg_delta = delta_sum / n
    empathy_rate = empathy_on / n

    top_counts = {"mode": dict(mode_counts), "principle": dict(prin_counts)}
    return {
        "avg_pre": round(avg_pre, 3),
        "avg_post": round(avg_post, 3),
        "avg_delta": round(avg_delta, 3),
        "empathy_activation_rate": round(empathy_rate, 3),
        "n_records": n,
        "top_mode_principle_counts": top_counts
    }

def save_snapshot(agg):
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d_%H%M%S")
    out_path = OUT_DIR / f"aggregates_{stamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(agg, f, ensure_ascii=False, indent=2)
        print(f"Saved to: {out_path}")
    return out_path

def print_summary(agg: dict):
    # pull counts safely
    top = agg.get("top_mode_principle_counts", {})
    mode_counts = {k: v for k, v in (top.get("mode", {}) or {}).items() if k != "-"}
    prin_counts = {k: v for k, v in (top.get("principle", {}) or {}).items() if k != "-"}

    # Top Modes
    print("Top Modes:")
    for m, mc in sorted(mode_counts.items(), key=lambda x: (-x[1], x[0]))[:3]:
        print(f"  {m:12s} {mc:>6}")

    # Top Principles
    print("Top Principles:")
    for p, pc in sorted(prin_counts.items(), key=lambda x: (-x[1], x[0]))[:5]:
        print(f"  {p:22s} {pc:>6}")

    # one line, outside loops
    print(f"\nRecords counted: {agg.get('n_records', 0)}")


def main():
    recs, paths = load_records()
    agg = aggregate(recs)
    save_snapshot(agg)
    print_summary(agg)

if __name__ == "__main__":
    main()