# Owlume — Metrics Data (T4-S2 → T4-S4)

This folder stores all metric aggregation outputs used by the **Owlume Learning Dashboard** and **Light HTML Reports**.

---

## 📊 Overview

Each file in this folder represents a summarized snapshot of all clarity-gain logs recorded by **DilemmaNet**.  
They provide the data foundation for Owlume’s instrumentation phase:

T4-S2 Aggregate metrics
T4-S3 Mini Dashboard + Chart Pack
T4-S4 Light HTML Report


---

## 🧩 File types

| File pattern | Description | Created by |
|---------------|-------------|-------------|
| `aggregates_YYYYMMDD_HHMMSS.json` | Main metrics snapshot (raw averages, empathy rate, top counts) | `scripts/aggregate_metrics.py` |
| `aggregates_YYYYMMDD_HHMMSS_aug.json` | Augmented version with additional insights and structure | `scripts/augment_aggregates.py` |
| `aggregates_latest.json` *(optional)* | Soft symlink or copy of the most recent aggregate | watcher or manual task |
| `*.csv` *(future)* | Optional export format for external analytics | future T4-extension |

---

## 🧮 JSON structure (simplified)

```jsonc
{
  "timestamp": "2025-10-21T02:42:02Z",
  "count": 20,
  "avg_pre": 0.128,
  "avg_post": 0.233,
  "avg_delta": 0.105,
  "empathy_activation_rate": 0.20,
  "distribution": { "+": 0.30, "0": 0.70, "-": 0.00 },
  "top_mode_principle": {
    "Assumption × Evidence": 2,
    "Perspective × Impact": 2,
    "Decision × Risk": 2
  },
  "source_files": [
    "clarity_gain_samples.jsonl",
    "clarity_gain_thresholds.json",
    ...
  ]
}
⚙️ All values are float-safe and timezone-aware (UTC).

⚗️ Generation flow

aggregate_metrics.py

Scans all clarity-gain logs under /data/logs/

Computes mean pre/post/Δ, empathy rates, and distribution

Writes → data/metrics/aggregates_*.json

augment_aggregates.py

Adds derived fields and richer breakdowns

Writes → data/metrics/aggregates_*.json → *_aug.json

mini_dashboard.py

Prints a compact console view of the latest aggregates

chart_pack.py

Generates PNG charts → /artifacts/charts/

render_report.py

Converts latest metrics → /reports/owlume_light_report_*.html

🕒 Lifespan & housekeeping

These JSONs are runtime artifacts; they don’t need to live in Git history.

Keep the latest few for reference or dashboard demos.

Recommended .gitignore entry:

/data/metrics/aggregates_*.json
/data/metrics/aggregates_*.jsonl

🧭 Tips

Run the VS Code task “Aggregate: Metrics (T4-S2)” anytime to refresh this folder.

The dashboard watcher automatically reacts when new files appear here.

To verify schema compliance, run:

python -u scripts/validate_metrics_schema.py
(optional future validator)

Owlume Metric Stack = Data → Insight → Clarity
Each aggregate you see here feeds both learning loops and human-readable reflection clarity.

---

Would you like me to generate a matching `validate_metrics_schema.py` (simple schema check against your current aggregates) so that file reference in the README actually works?
