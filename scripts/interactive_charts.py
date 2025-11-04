#!/usr/bin/env python3
"""
Owlume — L3-S2 Interactive Plot Pack

Reads the L3-S1 dataset and renders interactive Plotly HTML charts:
- clarity_trend.html           (Clarity Gain Δ over time with empathy overlay)
- empathy_curve.html           (Empathy activation over time + distribution)
- mode_principle_heatmap.html  (Mode × Principle intensity heatmap)

Inputs
- /data/metrics/clarity_gain_dashboard.json  (from L3-S1)

Outputs
- /artifacts/interactive/*.html

Usage
  python -u scripts/interactive_charts.py \
    --in_json data/metrics/clarity_gain_dashboard.json \
    --out_dir artifacts/interactive

Notes
- Uses Plotly offline (no internet).
- Safe to open HTML files locally or host on GitHub Pages.
"""
from __future__ import annotations
import argparse
import json
import os
from typing import Any, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ----------------------------
# Helpers
# ----------------------------

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_dashboard_rows(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input JSON not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame.from_records(data)
    # Types
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for c in ["cg_pre", "cg_post", "cg_delta", "empathy_ratio"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "empathy_on" in df.columns:
        df["empathy_on"] = df["empathy_on"].astype("boolean")
    # Clean labels
    df["mode"] = df.get("mode", pd.Series([None]*len(df))).fillna("-")
    df["principle"] = df.get("principle", pd.Series([None]*len(df))).fillna("-")
    df["mode_principle"] = df["mode_principle"].fillna(df["mode"] + " × " + df["principle"])
    # Sort by time
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


# ----------------------------
# Charts
# ----------------------------

def plot_trend(df: pd.DataFrame) -> go.Figure:
    """Clarity Gain Δ over time; color = empathy_on; size = |Δ| for emphasis."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data", showarrow=False)
        return fig

    # Size emphasizes magnitude; hover shows rich context.
    size_series = (df["cg_delta"].abs() * 30).clip(lower=8, upper=40)
    fig = px.scatter(
        df,
        x="timestamp",
        y="cg_delta",
        color=df["empathy_on"].map({True: "Empathy on", False: "Empathy off", pd.NA: "Unknown"}),
        size=size_series,
        hover_data={
            "timestamp": True,
            "cg_delta": ":.3f",
            "mode_principle": True,
            "empathy_state": True,
            "did": True,
        },
        labels={"cg_delta": "Clarity Gain Δ", "timestamp": "Time", "color": "Empathy"},
    )
    fig.update_traces(marker=dict(line=dict(width=0)))
    fig.update_layout(
        title="Clarity Gain Δ over Time (colored by Empathy)",
        xaxis_title="Time",
        yaxis_title="Δ",
        hovermode="closest",
    )

    # Add a zero baseline.
    fig.add_hline(y=0, line_width=1, line_dash="dot")
    return fig


def plot_empathy_curve(df: pd.DataFrame) -> go.Figure:
    """Empathy activation over time and distribution as stacked bars by tier."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data", showarrow=False)
        return fig

    # Daily activation ratio
    dfd = df.copy()
    dfd["date"] = dfd["timestamp"].dt.date
    daily = dfd.groupby("date")["empathy_on"].mean(numeric_only=True).reset_index(name="activation_rate")

    fig = px.line(
        daily,
        x="date",
        y="activation_rate",
        markers=True,
        labels={"date": "Date", "activation_rate": "Empathy activation (0–1)"},
        title="Empathy Activation Over Time",
    )
    fig.update_yaxes(range=[0, 1])
    fig.update_layout(hovermode="x unified")
    return fig


def plot_mode_principle_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap: frequency × average Δ per Mode × Principle."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data", showarrow=False)
        return fig

    dfg = (
        df.groupby(["mode", "principle"], dropna=False)
          .agg(count=("did", "count"), avg_delta=("cg_delta", "mean"))
          .reset_index()
    )

    # Score combines usage with impact (tweakable)
    dfg["score"] = dfg["count"] * dfg["avg_delta"].fillna(0)

    # Pivot for heatmap
    pivot = dfg.pivot(index="mode", columns="principle", values="score").fillna(0)

    fig = px.imshow(
        pivot,
        aspect="auto",
        origin="lower",
        title="Mode × Principle Intensity (count × avg Δ)",
        labels=dict(x="Principle", y="Mode", color="Intensity"),
    )

    # Improve readability
    fig.update_xaxes(side="top")
    fig.update_layout(margin=dict(l=60, r=20, t=60, b=60))
    return fig


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Render interactive Plotly charts for Owlume L3-S2.")
    ap.add_argument("--in_json", default="data/metrics/clarity_gain_dashboard.json")
    ap.add_argument("--out_dir", default="artifacts/interactive")
    args = ap.parse_args()

    print("[L3-S2] Loading:", args.in_json)
    df = load_dashboard_rows(args.in_json)
    _ensure_dir(args.out_dir)

    # Trend
    fig1 = plot_trend(df)
    out1 = os.path.join(args.out_dir, "clarity_trend.html")
    fig1.write_html(out1, include_plotlyjs="cdn", full_html=True)
    print("[L3-S2] Wrote:", out1)

    # Empathy curve
    fig2 = plot_empathy_curve(df)
    out2 = os.path.join(args.out_dir, "empathy_curve.html")
    fig2.write_html(out2, include_plotlyjs="cdn", full_html=True)
    print("[L3-S2] Wrote:", out2)

    # Heatmap
    fig3 = plot_mode_principle_heatmap(df)
    out3 = os.path.join(args.out_dir, "mode_principle_heatmap.html")
    fig3.write_html(out3, include_plotlyjs="cdn", full_html=True)
    print("[L3-S2] Wrote:", out3)

    # Optional quick index
    index_html = f"""
<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"/>
<title>Owlume — Interactive Charts</title>
<style>body{{font-family:ui-sans-serif,system-ui,Segoe UI,Roboto;max-width:980px;margin:40px auto;padding:0 16px;}} a{{display:block;margin:8px 0;}}</style>
</head><body>
<h1>🦉 Owlume — Interactive Charts</h1>
<p>Generated by <code>scripts/interactive_charts.py</code></p>
<ul>
  <li><a href=\"clarity_trend.html\">Clarity Trend</a></li>
  <li><a href=\"empathy_curve.html\">Empathy Activation</a></li>
  <li><a href=\"mode_principle_heatmap.html\">Mode × Principle Heatmap</a></li>
</ul>
</body></html>
"""
    idx = os.path.join(args.out_dir, "index.html")
    with open(idx, "w", encoding="utf-8") as f:
        f.write(index_html)
    print("[L3-S2] Wrote:", idx)

    print("[L3-S2] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

