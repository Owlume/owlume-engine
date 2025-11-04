🛠️ Retrofit Checklist — Stage 5 Dual-Reasoning Alignment

Purpose: add light, non-breaking upgrades so Stage 5 reflects the Dual-Reasoning model (human-bias vs AI-drift), without redoing prior work.

0) Scope & Safety

 No breaking changes; all additions are optional fields or minor UI.

 CI/validation stays green after edits.

 Backwards compatible with existing logs and dashboards.

1) Runtime Events — Tag reasoning mode & balance

Files:

scripts/insight_engine_hook.py

data/runtime/insight_events.jsonl (output)

schemas/insight_event.schema.json (if you keep one; optional)

Changes:

 Emit two optional fields on each event:

reasoning_mode: "sequential" | "associative" | "mixed" (fallback)

balance_score: float 0.0–1.0 (1 = well-balanced)

Snippet (emit site):

event["reasoning_mode"] = event.get("reasoning_mode", "mixed")
event["balance_score"] = event.get("balance_score", None)

Example JSONL (new lines at tail):

{"type":"HIGH_CG_SESSION","did":"DID-2025-0201","mode":"Decision","principle":"Risk","cg_delta":0.42,"reasoning_mode":"sequential","balance_score":0.66}
{"type":"LOW_CG_SESSION","did":"DID-2025-0202","mode":"Perspective","principle":"Impact","cg_delta":0.05,"reasoning_mode":"associative","balance_score":0.31}

(Optional) Schema add:

"reasoning_mode": { "type":"string", "enum":["sequential","associative","mixed"] },
"balance_score":  { "type":["number","null"], "minimum":0.0, "maximum":1.0 }

2) Feedback Bridge — Aggregate new fields

Files:

src/helpers/merge_feedback.py (or equivalent)

scripts/dashboard_watch_runtime.py

Changes:

 Track counts of reasoning_mode values.

 Track rolling mean of balance_score when present.

Pseudocode:

agg["mode_counts"] = agg.get("mode_counts", {"sequential":0,"associative":0,"mixed":0})
m = ev.get("reasoning_mode","mixed")
agg["mode_counts"][m] = agg["mode_counts"].get(m,0) + 1

bs = ev.get("balance_score")
if isinstance(bs, (int,float)):
    arr = agg.get("_balance_samples", [])
    arr.append(bs)
    agg["_balance_samples"] = arr
    agg["balance_avg"] = round(sum(arr)/len(arr), 3)

3) Dashboard v2.1 — Show Balance Indices

Files:

scripts/build_dashboard_ui.py (or wherever you render)

reports/dashboard_v2.html (output)

Changes:

 Add small card/table for:

clarity_balance_ratio (mean of human-bias reduction & AI-drift reduction once available)

mode_counts breakdown

balance_avg (provisional; from event samples)

HTML (minimal add):

<section id="balance">
  <h2>Reasoning Balance</h2>
  <ul>
    <li>balance_avg: [[BALANCE_AVG]]</li>
    <li>mode_counts: sequential [[MC_SEQ]], associative [[MC_ASSOC]], mixed [[MC_MIX]]</li>
  </ul>
</section>

(Replace placeholders during template render.)

4) Empathy Lens — Make it default ON

Files:

config/runtime.json (or your cfg)

src/elenx_engine.py (if default is coded there)

Change:

 Set:

"empathy": { "enabled": true }

5) Snapshot Report (T5-S8) — Include balance info

Files:

scripts/generate_snapshot_report.py (the new one we outlined)

reports/snapshots/snapshot_YYYY-MM-DD.md (output)

Changes:

 Read mode_counts, balance_avg, and (when present) clarity_balance_ratio.

 Add a “Reasoning Balance” section.

MD render (add block):

## Reasoning Balance
- balance_avg: **{{balance_avg}}**
- mode_counts: sequential={{mc_seq}}, associative={{mc_assoc}}, mixed={{mc_mix}}
- clarity_balance_ratio: **{{cbr}}**  _(if available)_

6) Docs — Adjustment note insert

Files:

README.md (public, 2-paragraph insert)

/reports/stage5_dual_reasoning_alignment_note.md (already drafted)

Changes:

 Paste the short public insert near top of README (after tagline).

 Link to the full note in /reports/.

7) CI / Validation – Keep green

Files:

.github/workflows/validate.yml

scripts/validate_json.py

Checks:

 If you added schemas, include them in validation targets.

 Ensure optional fields don’t cause old data to fail.

Command (PowerShell):

python -u scripts/validate_json.py --schemas schemas --data data

8) Quick QA Runbook (PowerShell)

 Emit 2–3 new events:

python -u scripts/insight_engine_hook.py --in_json data/metrics/clarity_gain_dashboard.json --aggregates_glob "data/metrics/aggregates_*.json" --out_jsonl data/runtime/insight_events.jsonl


 Watcher picks them up:

python -u scripts/dashboard_watch_runtime.py


 Rebuild dashboard & open:

python -u scripts/build_dashboard_ui.py
start reports/dashboard_v2.html


 Generate today’s snapshot:

python -u scripts/generate_snapshot_report.py --html


 Sanity check tail:

Get-Content data\runtime\insight_events.jsonl -Tail 5

9) Acceptance Criteria

 Existing pipelines run unchanged (no crashes with legacy data).

 Events show new optional fields when present.

 Dashboard v2.1 displays a Balance block (no layout break).

 Snapshot includes “Reasoning Balance” section.

 Empathy defaults to ON in runtime (and is reflected in config).

 CI still passes; validators accept old & new records.

Notes

All additions are append-only: you can roll them back by ignoring the new fields.

When Stage 6 introduces formal H_bias_reduction and A_drift_reduction, wire them into clarity_balance_ratio and expose in the dashboard card you just added.


