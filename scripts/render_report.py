# scripts/render_report.py
import json, os, glob, datetime as dt
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Ensure UTF-8 console on Windows if possible
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "data" / "metrics"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def pick_latest_aggregate() -> Path:
    files = sorted(METRICS_DIR.glob("aggregates_*.json"))
    if files:
        return files[-1]
    all_json = sorted(METRICS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not all_json:
        raise FileNotFoundError("No metrics JSON files found in data/metrics/")
    return all_json[-1]

def load_json(p: Path) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def get_val(d: Dict[str, Any], *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(k, tuple):
            found = False
            for kk in k:
                if isinstance(cur, dict) and kk in cur:
                    cur = cur[kk]
                    found = True
                    break
            if not found:
                return default
        else:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                return default
    return cur

def format_pct(x: float) -> str:
    try:
        return f"{float(x)*100:.1f}%"
    except Exception:
        return "-"

def infer_top_counts(data: Dict[str, Any]) -> List[Tuple[str,int]]:
    cand = (
        get_val(data, ("top_mode_principle","top_mode×principle","top_counts")) or
        get_val(data, "top", "mode_principle")
    )
    if isinstance(cand, dict):
        return sorted(cand.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))[:10]
    if isinstance(cand, list):
        rows = []
        for item in cand:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                rows.append((str(item[0]), int(item[1])))
            elif isinstance(item, dict) and "label" in item and "count" in item:
                rows.append((str(item["label"]), int(item["count"])))
        return rows[:10]
    return []

def bar(w: float) -> str:
    w = max(0.0, min(100.0, float(w)))
    return f'<div style="height:10px;background:#e5e7eb;border-radius:6px;"><div style="height:10px;width:{w}%;background:#4b5563;border-radius:6px;"></div></div>'

def escape_html(s: str) -> str:
    return (str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

def build_top_rows_html(top: List[Tuple[str,int]]) -> str:
    if not top:
        return '<tr><td colspan="3" class="small">No top counts available.</td></tr>'
    total = max(1, sum(c for _, c in top))
    rows = []
    for label, count in top:
        share = (count / total) * 100.0
        rows.append(f"""
<tr>
  <td>{escape_html(label)}</td>
  <td class="mono">{count}</td>
  <td>{bar(share)}</td>
</tr>
""")
    return "\n".join(rows)

def render_html(latest_path: Path, data: Dict[str, Any]) -> str:
    # flexible key handling
    n_records = (
        get_val(data, ("count","n_records","records"), default=None)
        or get_val(data, "meta", ("count","n_records","records"), default="-")
        or "-"
    )

    avg_pre   = get_val(data, ("avg_pre",), default=None)
    avg_post  = get_val(data, ("avg_post",), default=None)
    avg_delta = get_val(data, ("avg_delta","delta"), default=None)

    if avg_pre is None:
        avg_pre = get_val(data, "avg", "pre", default=None)
    if avg_post is None:
        avg_post = get_val(data, "avg", "post", default=None)
    if avg_delta is None:
        avg_delta = get_val(data, "avg", "delta", default=None)

    empathy_rate = get_val(data, ("empathy_activation_rate","empathy_rate","empathy"), default=None)
    pos = get_val(data, "distribution", ("positive","+","pos"), default=None) or get_val(data, ("positive_rate",), default=None)
    zero = get_val(data, "distribution", ("zero","flat","neutral","0"), default=None)
    neg = get_val(data, "distribution", ("negative","-","neg","regress"), default=None)

    top = infer_top_counts(data)

    ts = get_val(data, ("timestamp","generated_at","stamp"), default=None)
    if not ts:
        try:
            stem = latest_path.stem  # aggregates_YYYYMMDD_HHMMSS
            _, stamp = stem.split("_", 1)
            dt_obj = dt.datetime.strptime(stamp, "%Y%m%d_%H%M%S")
            ts = dt_obj.strftime("%Y-%m-%d %H:%M:%SZ")
        except Exception:
            ts = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M:%SZ")

    def pct_or_zero(x):
        try: 
            return float(x)*100.0
        except: 
            return 0.0

    pos_w = pct_or_zero(pos)
    zero_w = pct_or_zero(zero)
    neg_w = pct_or_zero(neg)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Owlume — Light Metrics Report</title>
<style>
  :root {{ --bg:#0b0f19; --fg:#f3f4f6; --muted:#9ca3af; --card:#111827; --accent:#6366f1; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu; background: var(--bg); color: var(--fg); }}
  .wrap {{ max-width: 940px; margin: 40px auto; padding: 0 20px; }}
  .title {{ font-size: 28px; font-weight: 700; letter-spacing: .2px; }}
  .sub  {{ margin-top: 6px; color: var(--muted); font-size: 14px; }}
  .grid {{ display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; margin-top: 20px; }}
  .card {{ background: var(--card); border: 1px solid #1f2937; border-radius: 14px; padding: 16px; }}
  .span6 {{ grid-column: span 6; }}
  .span12 {{ grid-column: span 12; }}
  .kpi {{ display:flex; justify-content: space-between; align-items: baseline; margin: 6px 0; }}
  .kpi .label {{ color: var(--muted); font-size: 12px; }}
  .kpi .value {{ font-size: 20px; font-weight: 700; }}
  table {{ width:100%; border-collapse: collapse; }}
  th, td {{ text-align:left; padding: 8px 6px; border-bottom: 1px solid #1f2937; font-size:14px; }}
  th {{ color: var(--muted); font-weight: 600; }}
  .small {{ color: var(--muted); font-size:12px; }}
  .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
  .pill {{ display:inline-block; padding:2px 8px; border-radius:999px; background:#1f2937; border:1px solid #374151; font-size:12px; }}
  .footer {{ margin: 24px 0; color: var(--muted); font-size: 12px; }}
  a {{ color: var(--fg); text-decoration: underline; text-decoration-color: #374151; }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="title">Owlume — Light Metrics Report</div>
    <div class="sub">Generated: <span class="mono">{ts}</span> • Source: <span class="mono">{latest_path.relative_to(ROOT).as_posix()}</span></div>

    <div class="grid">
      <div class="card span6">
        <div class="kpi"><div class="label">Records</div><div class="value">{n_records}</div></div>
        <div class="kpi"><div class="label">Avg Clarity (pre)</div><div class="value">{avg_pre if avg_pre is not None else "-"}</div></div>
        <div class="kpi"><div class="label">Avg Clarity (post)</div><div class="value">{avg_post if avg_post is not None else "-"}</div></div>
        <div class="kpi"><div class="label">Avg Δ</div><div class="value">{avg_delta if avg_delta is not None else "-"}</div></div>
        <div class="small">Δ = post − pre</div>
      </div>

      <div class="card span6">
        <div class="kpi"><div class="label">Empathy Activation</div><div class="value">{format_pct(empathy_rate) if empathy_rate is not None else "-"}</div></div>
        <div class="kpi"><div class="label">Distribution</div><div class="value small">positive / zero / negative</div></div>
        <div style="display:flex; gap:10px; align-items:center; margin-top:6px;">
          <div style="flex:1">{bar(pos_w)}</div>
          <div style="flex:1">{bar(zero_w)}</div>
          <div style="flex:1">{bar(neg_w)}</div>
        </div>
        <div class="small" style="margin-top:6px;">
          +{format_pct(pos) if pos is not None else "-"} • 0={format_pct(zero) if zero is not None else "-"} • –{format_pct(neg) if neg is not None else "-"}
        </div>
      </div>

      <div class="card span12">
        <div style="font-weight:700; margin-bottom:6px;">Top Mode × Principle</div>
        <table>
          <thead><tr><th style="width:60%">Label</th><th>Count</th><th style="width:40%">Share</th></tr></thead>
          <tbody>
            {build_top_rows_html(top)}
          </tbody>
        </table>
        <div class="small" style="margin-top:6px;">Showing up to 10 rows.</div>
      </div>
    </div>

    <div class="footer">
      This is a lightweight, static HTML snapshot. For auto-refresh charts, continue using your T4 dashboard watcher.
    </div>
  </div>
</body>
</html>
"""

def main():
    latest = pick_latest_aggregate()
    data = load_json(latest)
    html = render_html(latest, data)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d_%H%M%S")
    out_path = REPORTS_DIR / f"owlume_light_report_{stamp}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Rendered → {out_path}")

if __name__ == "__main__":
    main()
