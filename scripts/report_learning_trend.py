"""
Owlume — Stage 4 · L5 · T4
File: scripts/report_learning_trend.py

Reads:
  - data/reports/agent_memory_snapshot.json
  - data/runtime/agent_policy.json  (optional)

Outputs:
  - reports/learning_trend.html

Usage:
  python -u scripts/report_learning_trend.py
"""
import json, math
from pathlib import Path
from datetime import datetime, timezone

SNAPSHOT = Path("data/reports/agent_memory_snapshot.json")
POLICY = Path("data/runtime/agent_policy.json")
OUT = Path("reports/learning_trend.html")

def _week_key(ts: str) -> str:
    # Accepts Z or +00:00
    if ts.endswith("Z"):
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    else:
        dt = datetime.fromisoformat(ts)
    y, w, _ = dt.isocalendar()
    return f"{y}-W{int(w):02d}"

def load_snapshot():
    if not SNAPSHOT.exists():
        print("[X] Snapshot not found:", SNAPSHOT)
        return {"records": []}
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))

def load_policy():
    if POLICY.exists():
        try:
            return json.loads(POLICY.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def agg_by_week(records):
    weeks = {}
    for r in records:
        ts = r.get("timestamp")
        if not ts:
            continue
        wk = _week_key(ts)
        cg = r.get("meta_eval", {}).get("actual_cg_delta")
        ms = r.get("meta_eval", {}).get("meta_score")
        if cg is None or ms is None:
            cla = r.get("inputs", {}).get("clarity", {})
            cg = cla.get("cg_delta", 0.0)
            ms = 0.5
        bucket = weeks.setdefault(wk, {"count":0, "cg_sum":0.0, "ms_sum":0.0})
        bucket["count"] += 1
        bucket["cg_sum"] += float(cg)
        bucket["ms_sum"] += float(ms)
    # finalize
    rows = []
    for wk in sorted(weeks.keys()):
        b = weeks[wk]
        rows.append({
            "week": wk,
            "n": b["count"],
            "avg_cg": (b["cg_sum"]/b["count"]) if b["count"] else 0.0,
            "avg_meta": (b["ms_sum"]/b["count"]) if b["count"] else 0.0
        })
    return rows

def _sparkline(values, width=220, height=40, pad=4):
    if not values:
        return ""
    lo = min(values); hi = max(values)
    rng = (hi - lo) if (hi - lo) > 1e-9 else 1.0
    pts = []
    n = len(values)
    for i, v in enumerate(values):
        x = pad + (width - 2*pad) * (i/(max(1,n-1)))
        y = pad + (height - 2*pad) * (1 - (v - lo)/rng)
        pts.append(f"{x:.1f},{y:.1f}")
    poly = " ".join(pts)
    return f'<svg width="{width}" height="{height}"><polyline fill="none" stroke="black" stroke-width="1" points="{poly}" /></svg>'

def build_html(weeks, policy):
    weeks = weeks[-16:]  # last ~16 weeks
    avg_cg = [round(w["avg_cg"], 4) for w in weeks]
    avg_ms = [round(w["avg_meta"], 4) for w in weeks]

    cg_svg = _sparkline(avg_cg) if weeks else ""
    ms_svg = _sparkline(avg_ms) if weeks else ""

    pol_rows = ""
    for k in ["risk_probe","assumption_challenge","empathy_weight","tone_warmth"]:
        if k in policy:
            pol_rows += f"<tr><td>{k}</td><td>{policy[k]:.3f}</td></tr>"

    wk_rows = ""
    for w in weeks:
        wk_rows += f"<tr><td>{w['week']}</td><td>{w['n']}</td><td>{w['avg_cg']:.3f}</td><td>{w['avg_meta']:.3f}</td></tr>"

    html = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Owlume — Learning Trend</title>
<style>
body{{font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;padding:24px;color:#111}}
h1{{font-size:22px;margin:0 0 8px}}
h2{{font-size:16px;margin:18px 0 8px}}
table{{border-collapse:collapse;margin:12px 0;width:520px;max-width:100%}}
td,th{{border:1px solid #ddd;padding:6px 8px;text-align:left;font-size:13px}}
.small{{font-size:12px;color:#555}}
.card{{padding:12px;border:1px solid #eee;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,0.04);max-width:900px}}
.kpi{{display:flex;gap:18px;align-items:center}}
.kpi div{{display:flex;flex-direction:column}}
.kpi .label{{font-size:12px;color:#666}}
.kpi .value{{font-size:18px;font-weight:600}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
</style>
<div class="card">
  <h1>🦉 Owlume — Learning Trend</h1>
  <div class="small">Generated: {datetime.now(timezone.utc).isoformat().replace("+00:00","Z")}</div>

  <div class="grid">
    <div>
      <h2>Average CGΔ by Week</h2>
      {cg_svg}
    </div>
    <div>
      <h2>Average Meta Score by Week</h2>
      {ms_svg}
    </div>
  </div>

  <h2>Current Policy</h2>
  <table><tr><th>Key</th><th>Value</th></tr>
    {pol_rows or "<tr><td colspan='2'>No policy file found</td></tr>"}
  </table>

  <h2>Weekly Aggregates</h2>
  <table>
    <tr><th>Week</th><th>n</th><th>avg CGΔ</th><th>avg meta</th></tr>
    {wk_rows or "<tr><td colspan='4'>No records</td></tr>"}
  </table>

  <div class="small">Source: data/reports/agent_memory_snapshot.json</div>
</div>
</html>"""
    return html

def main():
    snap = load_snapshot()
    recs = snap.get("records", [])
    weeks = agg_by_week(recs)
    policy = load_policy()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_html(weeks, policy), encoding="utf-8")
    print("[OK] Report written →", OUT)

if __name__ == "__main__":
    main()
