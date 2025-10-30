#!/usr/bin/env python3
"""
Owlume — L3-S4 Dashboard UI v2 (Static Bundle)

Builds a clean, single entry-point dashboard that stitches together:
- Interactive charts (from L3-S2) in /artifacts/interactive
- Session Explorer + Drilldowns (from L3-S3) in /reports

Outputs
- /reports/clarity_dashboard_v2.html  (tabs + embedded iframes)
- /reports/_assets/                   (optional CSS assets)

Usage
  python -u scripts/build_dashboard_ui.py \
    --charts_dir artifacts/interactive \
    --reports_dir reports \
    --out_html reports/clarity_dashboard_v2.html

Notes
- Pure static HTML — open locally or host on GitHub Pages.
- Uses iframes for isolation; files must exist before running (L3-S2, L3-S3).
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path


HTML_TEMPLATE = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Owlume — Clarity Gain Dashboard v2</title>
  <style>
    :root { --bg: #0b1020; --fg: #e8ecf1; --muted:#9aa7b3; --card:#121a33; --accent:#7aa2ff; }
    *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);font-family:ui-sans-serif,system-ui,Segoe UI,Roboto}
    header{padding:24px 20px;border-bottom:1px solid #1c274d}
    .wrap{max-width:1200px;margin:0 auto}
    h1{margin:0 0 6px 0;font-size:24px}
    p.subtitle{margin:0;color:var(--muted)}
    nav.tabs{display:flex;gap:8px;padding:16px 20px;border-bottom:1px solid #1c274d;background:#0e1630;position:sticky;top:0;z-index:10}
    nav.tabs button{background:transparent;border:1px solid #2a3870;color:var(--fg);padding:8px 12px;border-radius:10px;cursor:pointer}
    nav.tabs button.active{background:var(--accent);border-color:var(--accent);color:#0b1020;font-weight:700}
    .panel{display:none;padding:16px}
    .panel.active{display:block}
    .card{background:var(--card);border:1px solid #1c274d;border-radius:16px;padding:8px}
    .grid{display:grid;grid-template-columns:1fr;gap:16px}
    @media (min-width: 900px){ .grid.two{grid-template-columns:1fr 1fr} }
    iframe{width:100%;height:72vh;border:0;background:#0b1020;border-radius:12px}
    .small{height:64vh}
    .cta{display:inline-block;margin-top:12px;color:var(--accent);text-decoration:none}
    .meta{color:var(--muted);font-size:12px;margin-top:8px}
  </style>
</head>
<body>
  <header>
    <div class=\"wrap\">
      <h1>🦉 Owlume — Clarity Gain Dashboard v2</h1>
      <p class=\"subtitle\">Interactive charts • Drilldowns • Session explorer</p>
    </div>
  </header>
  <nav class=\"tabs wrap\">
    <button data-tab=\"overview\" class=\"active\">Overview</button>
    <button data-tab=\"charts\">Charts</button>
    <button data-tab=\"explorer\">Session Explorer</button>
    <button data-tab=\"heatmap\">Mode × Principle</button>
  </nav>

  <main class=\"wrap\">
    <section id=\"overview\" class=\"panel active\">
      <div class=\"grid two\">
        <div class=\"card\">
          <iframe src=\"[[CLARITY_TREND]]\"></iframe>
          <div class=\"meta\">Clarity Gain Δ over time — hover for details; zoom with drag.</div>
        </div>
        <div class=\"card\">
          <iframe src=\"[[EMPATHY_CURVE]]\" class=\"small\"></iframe>
          <div class=\"meta\">Empathy activation ratio by day.</div>
        </div>
      </div>
    </section>

    <section id=\"charts\" class=\"panel\">
      <div class=\"card\"><iframe src=\"[[CLARITY_TREND]]\"></iframe></div>
      <div class=\"card\"><iframe src=\"[[EMPATHY_CURVE]]\" class=\"small\"></iframe></div>
    </section>

    <section id=\"explorer\" class=\"panel\">
      <div class=\"card\"><iframe src=\"[[EXPLORER]]\" class=\"small\"></iframe></div>
      <a class=\"cta\" href=\"[[EXPLORER]]\" target=\"_blank\">Open Session Explorer in a new tab →</a>
    </section>

    <section id=\"heatmap\" class=\"panel\">
      <div class=\"card\"><iframe src=\"[[HEATMAP]]\" class=\"small\"></iframe></div>
    </section>
  </main>

  <script>
    const tabs = document.querySelectorAll('nav.tabs button');
    const panels = document.querySelectorAll('.panel');
    tabs.forEach(btn => btn.addEventListener('click', () => {
      tabs.forEach(b=>b.classList.remove('active'));
      panels.forEach(p=>p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');
    }));
  </script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Build static Dashboard UI v2 for Owlume.")
    ap.add_argument("--charts_dir", default="artifacts/interactive")
    ap.add_argument("--reports_dir", default="reports")
    ap.add_argument("--out_html", default="reports/clarity_dashboard_v2.html")
    args = ap.parse_args()

    charts_dir = Path(args.charts_dir)
    reports_dir = Path(args.reports_dir)

    # Validate expected files
    clarity_trend = charts_dir / "clarity_trend.html"
    empathy_curve = charts_dir / "empathy_curve.html"
    heatmap = charts_dir / "mode_principle_heatmap.html"
    explorer = reports_dir / "clarity_dashboard.html"

    for p in [clarity_trend, empathy_curve, heatmap, explorer]:
        if not p.exists():
            raise SystemExit(f"Missing input: {p}")

    out_html = Path(args.out_html)
    out_html.parent.mkdir(parents=True, exist_ok=True)    # Build final HTML by replacing tokens
    html = (
        HTML_TEMPLATE
        .replace('[[CLARITY_TREND]]', os.path.relpath(clarity_trend, out_html.parent))
        .replace('[[EMPATHY_CURVE]]', os.path.relpath(empathy_curve, out_html.parent))
        .replace('[[HEATMAP]]', os.path.relpath(heatmap, out_html.parent))
        .replace('[[EXPLORER]]', os.path.relpath(explorer, out_html.parent))
    )

    out_html.write_text(html, encoding="utf-8")
    print(f"[L3-S4] Wrote: {out_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


