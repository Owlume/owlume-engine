#!/usr/bin/env python3
"""
Owlume — L3-S3 Drilldown & Trend Reports

Generates static, drillable HTML reports from the L3-S1 dashboard dataset.
- A master "Session Explorer" (sortable/filterable table) with quick filters.
- Per Mode × Principle drilldowns showing session rows and mini trend.
- Date-range slices (optional) via CLI.

Inputs
- /data/metrics/clarity_gain_dashboard.json

Outputs
- /reports/clarity_dashboard.html                 (Session Explorer + links)
- /reports/drilldown_<Mode>__<Principle>.html     (sanitized names)

Usage
  python -u scripts/drilldown_reports.py \
    --in_json data/metrics/clarity_gain_dashboard.json \
    --out_dir reports

Notes
- Pure static HTML with Plotly + tiny JS for table filtering.
- Designed to be browsed locally or hosted as static files.
"""
from __future__ import annotations
import argparse
import html
import json
import os
import re
from typing import Dict, List

import pandas as pd
import plotly.express as px


SAFE = re.compile(r"[^A-Za-z0-9_-]+")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def sanitize(s: str) -> str:
    return SAFE.sub("_", s.strip())


def load_df(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame.from_records(data)
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for c in ["cg_pre", "cg_post", "cg_delta", "empathy_ratio"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["mode"] = df.get("mode", pd.Series([None]*len(df))).fillna("-")
    df["principle"] = df.get("principle", pd.Series([None]*len(df))).fillna("-")
    df["mode_principle"] = df["mode_principle"].fillna(df["mode"] + " × " + df["principle"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def build_session_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p>No sessions found.</p>"
    # Minimal plain HTML table with client-side filtering script.
    # (For larger tables, consider DataTables, but we keep it dependency-light.)
    headers = ["timestamp", "did", "mode", "principle", "cg_delta", "empathy_state"]
    rows = []
    for _, r in df.iterrows():
        ts = r["timestamp"].isoformat() if pd.notna(r["timestamp"]) else ""
        row = [
            html.escape(ts),
            html.escape(str(r.get("did", ""))),
            html.escape(str(r.get("mode", ""))),
            html.escape(str(r.get("principle", ""))),
            f"{float(r.get('cg_delta', 0) or 0):.3f}",
            html.escape(str(r.get("empathy_state", ""))),
        ]
        rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")

    thead = "".join(f"<th>{h}</th>" for h in headers)
    tbody = "".join(rows)
    return f"""
<input id=\"filter\" placeholder=\"Filter (mode, principle, did, empathy, etc.)\" style=\"margin:12px 0;padding:8px;width:100%\" />
<table id=\"t\" border=\"1\" cellspacing=\"0\" cellpadding=\"6\" style=\"border-collapse:collapse;width:100%\">
  <thead><tr>{thead}</tr></thead>
  <tbody>{tbody}</tbody>
</table>
<script>
const f = document.getElementById('filter');
const t = document.getElementById('t').getElementsByTagName('tbody')[0];
f.addEventListener('input', function(){{
  const q = this.value.toLowerCase();
  for (const tr of t.rows) {{
    const show = tr.innerText.toLowerCase().includes(q);
    tr.style.display = show ? '' : 'none';
  }}
}});
</script>
"""


def mini_trend(df: pd.DataFrame, title: str) -> str:
    if df.empty:
        return "<p>No data.</p>"
    d = df.copy()
    fig = px.scatter(
        d,
        x="timestamp",
        y="cg_delta",
        color=d.get("empathy_state"),
        hover_data=["did", "mode", "principle"],
        title=title,
    )
    return fig.to_html(include_plotlyjs="cdn", full_html=False)


def write_master(df: pd.DataFrame, out_path: str, links: List[str]) -> None:
    links_html = "".join(f"<li><a href=\"{html.escape(os.path.basename(p))}\">{html.escape(os.path.splitext(os.path.basename(p))[0])}</a></li>" for p in links)
    content = f"""
<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"/>
<title>Owlume — Session Explorer</title>
<style>body{{font-family:ui-sans-serif,system-ui,Segoe UI,Roboto;max-width:1100px;margin:40px auto;padding:0 16px;}}</style>
</head><body>
<h1>🦉 Owlume — Session Explorer</h1>
<p>This page lists all sessions with quick filter. Use the Drilldowns for Mode × Principle deep dives.</p>
<h2>Quick Links — Drilldowns</h2>
<ul>{links_html}</ul>
<h2>All Sessions</h2>
{build_session_table(df)}
</body></html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)


def write_drilldown(df: pd.DataFrame, mode: str, principle: str, out_path: str) -> None:
    title = f"Drilldown — {mode} × {principle}"
    subset = df[(df["mode"] == mode) & (df["principle"] == principle)]
    chart = mini_trend(subset, title)
    table = build_session_table(subset)
    content = f"""
<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"/>
<title>{html.escape(title)}</title>
<style>body{{font-family:ui-sans-serif,system-ui,Segoe UI,Roboto;max-width:1100px;margin:40px auto;padding:0 16px;}}</style>
</head><body>
<h1>{html.escape(title)}</h1>
{chart}
<h2>Sessions</h2>
{table}
<p><a href=\"clarity_dashboard.html\">← Back to Session Explorer</a></p>
</body></html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate drilldown & trend reports for Owlume L3-S3.")
    ap.add_argument("--in_json", default="data/metrics/clarity_gain_dashboard.json")
    ap.add_argument("--out_dir", default="reports")
    args = ap.parse_args()

    df = load_df(args.in_json)
    _ensure_dir(args.out_dir)

    # Build list of unique Mode × Principle combos
    links: List[str] = []
    if not df.empty:
        combos = (df[["mode", "principle"]]
                  .dropna()
                  .drop_duplicates()
                  .sort_values(["mode", "principle"]))
        for _, r in combos.iterrows():
            m = str(r["mode"]) or "-"
            p = str(r["principle"]) or "-"
            fname = f"drilldown_{sanitize(m)}__{sanitize(p)}.html"
            outp = os.path.join(args.out_dir, fname)
            write_drilldown(df, m, p, outp)
            links.append(outp)

    # Write master explorer
    master = os.path.join(args.out_dir, "clarity_dashboard.html")
    write_master(df, master, links)

    print(f"[L3-S3] Wrote: {master}")
    for p in links:
        print(f"[L3-S3] Wrote: {p}")
    print("[L3-S3] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
