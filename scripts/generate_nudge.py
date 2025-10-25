#!/usr/bin/env python3
"""
Owlume — T5-S2 Nudge Generator (dev‑ready)

Selects the next-best nudge from /data/nudge_templates.json using simple, explainable
rules that match /schemas/nudge_templates.schema.json.

Usage (from repo root):
  python -u scripts/generate_nudge.py \
    --templates data/nudge_templates.json \
    --history data/runtime/nudge_history.json \
    --context data/runtime/nudge_context.json \
    --now "2025-10-21T13:40:00+11:00"

Output: JSON blob with the chosen nudge (id, message, reason, cooldowns, etc.)

Context file shape (example):
{
  "user_name": "Brian",
  "last_mode": "Assumption",
  "last_principle": "Evidence",
  "last_session_minutes_ago": 5,
  "last_cg_delta": 0.12,
  "streak_days": 4,
  "idle_days": 0,
  "reflections_count": 12,
  "empathy_ratio_window": 0.20,
  "avg_cg_delta_window": 0.03,               # 7-day window average Δ
  "sessions_in_window": 4,                    # sessions counted in that window
  "now_utc": "2025-10-21T02:40:00Z",        # optional; else use --now or system time
  "next_event": {                             # optional calendar hint for pre_meeting
    "title": "Stakeholder review",
    "minutes_until": 18
  }
}

History file shape (managed by this script):
{
  "gentle_morning_ping": "2025-10-20T22:00:00Z",
  "post_session_boost": "2025-10-21T02:10:00Z"
}

Notes:
- No external deps; uses stdlib only.
- Quiet-hours guardrail: suppress 22:00–07:59 local for *gentle* nudges.
- Honors template cooldowns and prioritizes moment-based nudges.
- Renders tokens like {{user_name}}, {{cg_delta}}, etc.
"""

from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 stdout/stderr on Windows terminals (fixes Δ/emoji)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ----------------------------- Config -----------------------------
QUIET_START = 22  # 22:00 local
QUIET_END = 8     # until 07:59 local (hour < 8)

# ----------------------------- IO helpers -----------------------------

def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ----------------------------- Time helpers -----------------------------

def parse_iso_now(now_arg: Optional[str]) -> dt.datetime:
    """Parse an ISO8601 string including offset (e.g., 2025-10-21T13:40:00+11:00).
    Falls back to local time if missing/invalid.
    """
    if not now_arg:
        return dt.datetime.now().astimezone()
    try:
        return dt.datetime.fromisoformat(now_arg)
    except Exception:
        return dt.datetime.now().astimezone()


def iso_utc(dt_obj: dt.datetime) -> str:
    return (
        dt_obj.astimezone(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def to_local_with_pack_tz(now_local: dt.datetime, pack: Dict[str, Any]) -> dt.datetime:
    """Best-effort: if pack defines default_timezone (IANA), we *assume* current system
    tz already matches user locale; Python stdlib lacks tzdb mapping without zoneinfo
    on older Pythons. If running on 3.9+, zoneinfo can be used. Here we simply return
    the provided now_local (already local by parse_iso_now)."""
    # You can upgrade this to zoneinfo if available in your environment.
    return now_local


# ----------------------------- Template Evaluation -----------------------------

def in_cooldown(last_fired_iso: Optional[str], cooldown_hours: int, now_utc: dt.datetime) -> bool:
    if not last_fired_iso:
        return False
    try:
        last = dt.datetime.fromisoformat(last_fired_iso.replace("Z", "+00:00"))
    except Exception:
        return False
    return (now_utc - last).total_seconds() < cooldown_hours * 3600


def is_quiet_hours(local_now: dt.datetime) -> bool:
    h = local_now.hour
    return bool(QUIET_START <= h or h < QUIET_END)


def day_name(local_now: dt.datetime) -> str:
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][local_now.weekday()]


def cond_days_of_week_ok(cond: Dict[str, Any], local_now: dt.datetime) -> bool:
    dlist = cond.get("days_of_week")
    return True if not dlist else day_name(local_now) in dlist


def cond_hour_ok(cond: Dict[str, Any], local_now: dt.datetime) -> bool:
    hours = cond.get("by_hour")
    return True if not hours else local_now.hour in hours


# --- Specific trigger checks ---

def qualifies_daily_time(tpl: Dict[str, Any], local_now: dt.datetime) -> Tuple[bool, str]:
    c = tpl.get("conditions", {})
    if not (cond_days_of_week_ok(c, local_now) and cond_hour_ok(c, local_now)):
        return False, "day/hour window not matched"
    return True, "in scheduled window"


def qualifies_end_of_day(tpl: Dict[str, Any], local_now: dt.datetime) -> Tuple[bool, str]:
    return qualifies_daily_time(tpl, local_now)


def qualifies_weekend(tpl: Dict[str, Any], local_now: dt.datetime) -> Tuple[bool, str]:
    return qualifies_daily_time(tpl, local_now)


def qualifies_after_session(tpl: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, str]:
    mins = ctx.get("last_session_minutes_ago")
    if mins is None:
        return False, "no session recency"
    if mins > 30:
        return False, "session too far in past"
    min_delta = tpl.get("conditions", {}).get("min_cg_delta")
    if isinstance(min_delta, (int, float)) and ctx.get("last_cg_delta", 0) < float(min_delta):
        return False, "CG delta below threshold"
    return True, "recent session and CG ok"


def qualifies_cg_trend_low(tpl: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, str]:
    c = tpl.get("conditions", {})
    threshold = c.get("threshold_delta")
    min_sessions = c.get("min_sessions", 1)
    avg_delta = ctx.get("avg_cg_delta_window")
    sessions = ctx.get("sessions_in_window", min_sessions)
    if avg_delta is None:
        return False, "no avg CG in context"
    if sessions < min_sessions:
        return False, "not enough sessions"
    if threshold is None:
        return False, "no threshold configured"
    if avg_delta >= float(threshold):
        return False, f"avg Δ {avg_delta} >= threshold {threshold}"
    return True, f"avg Δ {avg_delta} below {threshold}"


def qualifies_streak_break(tpl: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, str]:
    idle_req = tpl.get("conditions", {}).get("idle_days", 1)
    idle = ctx.get("idle_days")
    if idle is None:
        return False, "no idle_days in context"
    return (idle >= idle_req, f"idle {idle}d >= {idle_req}d")


def qualifies_empathy_off(tpl: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, str]:
    min_sessions = tpl.get("conditions", {}).get("min_sessions", 1)
    ratio = ctx.get("empathy_ratio_window")
    sessions = ctx.get("sessions_in_window", min_sessions)
    if ratio is None:
        return False, "no empathy ratio"
    if sessions < min_sessions:
        return False, "not enough sessions"
    if ratio > 0.0:
        return False, "empathy already used recently"
    return True, "empathy OFF in window"


def qualifies_reactivation_idle(tpl: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, str]:
    return qualifies_streak_break(tpl, ctx)


def qualifies_milestone(tpl: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, str]:
    c = tpl.get("conditions", {})
    rc_min = c.get("reflections_count_min")
    cg_total_min = c.get("cg_total_min")
    er_ge = c.get("empathy_ratio_ge")
    rc = ctx.get("reflections_count")
    cg_total = ctx.get("cg_total")
    er = ctx.get("empathy_ratio_all_time")
    reasons: List[str] = []
    ok = False
    if rc_min is not None and rc is not None and rc >= rc_min:
        ok = True; reasons.append(f"reflections ≥ {rc_min}")
    if cg_total_min is not None and cg_total is not None and cg_total >= cg_total_min:
        ok = True; reasons.append(f"CG total ≥ {cg_total_min}")
    if er_ge is not None and er is not None and er >= er_ge:
        ok = True; reasons.append(f"empathy ratio ≥ {er_ge}")
    return ok, ", ".join(reasons) if reasons else "no milestone met"


def qualifies_pre_meeting(tpl: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, str]:
    c = tpl.get("conditions", {})
    win = c.get("window_minutes", 15)
    kw = c.get("calendar_keywords", [])
    evt = ctx.get("next_event") or {}
    mins = evt.get("minutes_until")
    title = (evt.get("title") or "").lower()
    if mins is None:
        return False, "no next_event"
    if mins < 0 or mins > win:
        return False, f"event in {mins}m not within {win}m"
    if kw and title:
        if not any(k.lower() in title for k in kw):
            return False, "no keyword match"
    elif kw and not title:
        return False, "no title to match keywords"
    return True, f"event in {mins}m matches keywords"


TRIGGER_CHECKS = {
    "daily_time": lambda tpl, ctx, lnow: qualifies_daily_time(tpl, lnow),
    "end_of_day": lambda tpl, ctx, lnow: qualifies_end_of_day(tpl, lnow),
    "weekend":   lambda tpl, ctx, lnow: qualifies_weekend(tpl, lnow),
    "after_session": lambda tpl, ctx, lnow: qualifies_after_session(tpl, ctx),
    "cg_trend_low":  lambda tpl, ctx, lnow: qualifies_cg_trend_low(tpl, ctx),
    "streak_break":  lambda tpl, ctx, lnow: qualifies_streak_break(tpl, ctx),
    "empathy_off":   lambda tpl, ctx, lnow: qualifies_empathy_off(tpl, ctx),
    "reactivation_idle": lambda tpl, ctx, lnow: qualifies_reactivation_idle(tpl, ctx),
    "milestone":     lambda tpl, ctx, lnow: qualifies_milestone(tpl, ctx),
    "pre_meeting":   lambda tpl, ctx, lnow: qualifies_pre_meeting(tpl, ctx),
}


# ----------------------------- Selection logic -----------------------------

def pick_nudge(templates_pack: Dict[str, Any], history: Dict[str, str], ctx: Dict[str, Any], now_local: dt.datetime) -> Dict[str, Any]:
    templates = templates_pack.get("templates", [])
    now_utc_dt = now_local.astimezone(dt.timezone.utc)

    candidates: List[Tuple[Dict[str, Any], int, int, str]] = []  # (tpl, priority, cooldown, reason)

    for tpl in templates:
        trig = tpl.get("trigger_type")
        tone = tpl.get("tone")
        cooldown = int(tpl.get("cooldown_hours", 0))
        priority = int(tpl.get("priority", 0))
        last_iso = history.get(tpl.get("id"))

        # Cooldown check first (unless ignore_cooldown testing flag is set in context)
        if not ctx.get("ignore_cooldown", False) and in_cooldown(last_iso, cooldown, now_utc_dt):
            continue

        # Quiet hours guardrail (gentle only)
        if tone == "gentle" and is_quiet_hours(now_local):
            continue

        check = TRIGGER_CHECKS.get(trig)
        if not check:
            continue
        ok, reason = check(tpl, ctx, now_local)
        if ok:
            candidates.append((tpl, priority, cooldown, reason))

    if not candidates:
        return {"selected": None, "reason": "no candidates after cooldown/quiet-hours/conditions"}

    # Optional debug dump of candidates
    if ctx.get("_debug"):
        dbg = [
            {
                "id": t.get("id"),
                "tone": t.get("tone"),
                "trigger": t.get("trigger_type"),
                "priority": pr,
                "cooldown_hours": cd,
                "reason": rsn
            }
            for (t, pr, cd, rsn) in candidates
        ]
        print(json.dumps({"_debug_candidates": dbg}, ensure_ascii=False, indent=2))

    # Prefer moment-based first (implicit via tone), then priority desc, then shorter cooldown
    def sort_key(item: Tuple[Dict[str, Any], int, int, str]):
        tpl, prio, cd, _ = item
        is_moment = 1 if tpl.get("tone") == "moment" else 0
        return (-is_moment, -prio, cd)

    candidates.sort(key=sort_key)
    chosen_tpl, _, _, reason = candidates[0]

    # Render message with context
    msg = render_message(chosen_tpl.get("message", ""), ctx)

    return {
        "selected": {
            "id": chosen_tpl.get("id"),
            "tone": chosen_tpl.get("tone"),
            "trigger_type": chosen_tpl.get("trigger_type"),
            "message": msg,
            "raw_message": chosen_tpl.get("message"),
            "channels": chosen_tpl.get("channels", ["in_app"]),
            "cooldown_hours": chosen_tpl.get("cooldown_hours", 0),
            "priority": chosen_tpl.get("priority", 0),
            "conditions": chosen_tpl.get("conditions", {}),
        },
        "reason": reason,
        "timestamp_utc": iso_utc(now_local),
    }


# ----------------------------- Message rendering -----------------------------

def render_message(template: str, ctx: Dict[str, Any]) -> str:
    msg = template
    repl = {
        "{{user_name}}": ctx.get("user_name", ""),
        "{{last_mode}}": ctx.get("last_mode", ""),
        "{{last_principle}}": ctx.get("last_principle", ""),
        "{{cg_delta}}": fmt_num(ctx.get("last_cg_delta")),
        "{{streak_days}}": str(ctx.get("streak_days")) if ctx.get("streak_days") is not None else "",
        "{{reflections_count}}": str(ctx.get("reflections_count")) if ctx.get("reflections_count") is not None else "",
        "{{next_event_in}}": fmt_minutes((ctx.get("next_event") or {}).get("minutes_until")),
    }
    for k, v in repl.items():
        msg = msg.replace(k, v)
    return msg


def fmt_num(x: Any) -> str:
    try:
        return f"{float(x):.2f}"
    except Exception:
        return ""


def fmt_minutes(x: Any) -> str:
    try:
        m = int(x)
        if m < 0:
            return "now"
        return f"{m} min"
    except Exception:
        return ""


# ----------------------------- CLI -----------------------------

def main():
    p = argparse.ArgumentParser(description="Owlume Nudge Generator")
    p.add_argument("--templates", default="data/nudge_templates.json", help="Path to templates pack")
    p.add_argument("--history", default="data/runtime/nudge_history.json", help="Path to nudge history")
    p.add_argument("--context", default="data/runtime/nudge_context.json", help="Path to context JSON")
    p.add_argument("--now", default=None, help="ISO time with offset, e.g., 2025-10-21T13:40:00+11:00")
    p.add_argument("--debug", action="store_true", help="Print all qualifying candidates and reasons")
    p.add_argument("--ignore_cooldown", action="store_true", help="Ignore per-template cooldowns (testing)")
    args = p.parse_args()

    templates_path = Path(args.templates)
    history_path = Path(args.history)
    context_path = Path(args.context)

    templates = load_json(templates_path)
    history = load_json(history_path) if history_path.exists() else {}
    ctx = load_json(context_path) if context_path.exists() else {}

    # Resolve time (prefer explicit --now, then ctx.now_utc, else local)
    if args.now:
        now_local = parse_iso_now(args.now)
    elif ctx.get("now_utc"):
        try:
            now_local = dt.datetime.fromisoformat(ctx["now_utc"].replace("Z", "+00:00")).astimezone()
        except Exception:
            now_local = dt.datetime.now().astimezone()
    else:
        now_local = dt.datetime.now().astimezone()

    # Pipe CLI flags into context for internal logic
    ctx["_debug"] = bool(getattr(args, "debug", False))
    ctx["ignore_cooldown"] = bool(getattr(args, "ignore_cooldown", False))

    # Respect pack timezone hint (no-op in stdlib fallback)
    now_local = to_local_with_pack_tz(now_local, templates)

    result = pick_nudge(templates, history, ctx, now_local)

    # Update history if a nudge was selected
    selected = result.get("selected")
    if selected:
        history[selected["id"]] = iso_utc(now_local)
        save_json(history_path, history)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


