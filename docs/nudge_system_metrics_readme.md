# Owlume — Nudge System (T5-S5)

This doc explains how Owlume’s nudge system selects, renders, and measures nudges. It covers nudge types, trigger signals, ethical guardrails, and the metrics we log into DilemmaNet.

## Nudge Types
- **Gentle** — light, daily invite to reflect (e.g., “A 60-second check-in”).
- **Moment** — timely prompt after an interaction or signal (e.g., “Nice work — keep the clarity momentum”).
- **Recovery** — supportive nudge when streaks lapse (e.g., “Let’s get your clarity streak back”).

## Trigger Signals (inputs from context/history)
- **Time**: `local_tz`, `local_hour` (quiet hours avoided)
- **Engagement**: `last_seen_hours`, `streak_days`
- **Recent session**: `last_session_hours`, `cg_delta_recent`
- **Empathy ratio**: `empathy_ratio`
- **Backlog**: `pending_decisions`
- **Cool-downs**: per-nudge minimum hours between sends

## Selection Flow (high-level)
1. **Load templates** → filter by conditions (time window, quiet hours, feature flags).
2. **Apply cooldowns/history** → remove recently sent candidates unless `--ignore_cooldown`.
3. **Score** by moment fit (e.g., recent clarity gain, time-of-day suitability).
4. **Pick top 1–3** → write to `data/runtime/next_nudges.json`.
5. **Render** via `scripts/demo_render_nudges.py` (plain/emoji modes; encoding-tolerant; normalizes fields).

## Ethical Guardrails
- **Respect quiet hours** (default: 22:00–05:59 local)
- **Frequency caps**: per-nudge cooldowns (e.g., `post_session_boost: 6h`, `gentle_daily_invite: 1/day`)
- **Easy opt-out**: global nudge off switch (UX TBD)
- **Tone safety**: “firm” only for Recovery; no shame language; always actionable next step
- **Data minimalism**: log only what’s needed for learning (see Metrics)

## Metrics Logged to DilemmaNet
For each nudge (event schema suggestion):

```json
{
  "event": "nudge_sent",
  "id": "NUDGE-2025-0012",
  "nudge_id": "post_session_boost",
  "type": "moment",
  "tone": "encouraging",
  "reason": "recent session and CG ok",
  "contexts": ["moment", "after_reflection"],
  "timestamp": "2025-10-22T09:00:00+11:00",
  "user_tz": "Australia/Sydney",
  "source": "generator|watcher|manual",
  "cooldown_ok": true,
  "quiet_hours_ok": true
}

Downstream interaction metrics (captured by UX or CLI):
{ "event": "nudge_viewed",  "id": "NUDGE-2025-0012", "timestamp": "..." }
{ "event": "nudge_actioned", "id": "NUDGE-2025-0012", "action": "Open a quick reflection", "timestamp": "..." }
{ "event": "nudge_dismissed", "id": "NUDGE-2025-0012", "timestamp": "..." }

Aggregate metrics (T4 dashboard inputs):

send_count (per type/id)

open_rate / view_rate

action_rate

resume_rate (started a reflection within X minutes)

time_to_action (median/avg)

CG_uplift_after_nudge (mean Δ within 24h of action)

File/Script Map

Templates: /data/nudge_templates.json (schema: /schemas/nudge_templates.schema.json)

Context: /data/runtime/nudge_context.json

History/Cooldowns: /data/runtime/nudge_history.json

Generator: /scripts/generate_nudge.py

Renderer: /scripts/demo_render_nudges.py

Output (runtime): /data/runtime/next_nudges.json

Common Commands

# Generate (respecting quiet hours/cooldowns)
python -u scripts/generate_nudge.py --templates data/nudge_templates.json --history data/runtime/nudge_history.json --context data/runtime/nudge_context.json > data/runtime/next_nudges.json

# Force a morning run and ignore cooldowns (demo)
python -u scripts/generate_nudge.py --templates data/nudge_templates.json --history data/runtime/nudge_history.json --context data/runtime/nudge_context.json --now "2025-10-22T09:00:00+11:00" --ignore_cooldown > data/runtime/next_nudges.json

# Render
python -u scripts/demo_render_nudges.py --input data/runtime/next_nudges.json
python -u scripts/demo_render_nudges.py --input data/runtime/next_nudges.json --plain

#Future Enhancements

Add --out to generate_nudge.py (native file write)

Add per-user global nudge switch and per-type frequency budgets

Track moment fit score and correlate with action/CG uplift

HTML/PNG render of Nudge Cards for reports