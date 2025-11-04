#!/usr/bin/env python3
"""
S8-S1 — Dashboard v3 Ecosystem Overlay

Reads reports/S7-S6_ecosystem_learning_summary.md and injects an overlay
card into reports/index.html between:

    <!-- S7-S6 OVERLAY START -->
    ...
    <!-- S7-S6 OVERLAY END -->

If the markers are not present, it will append the overlay just before </body>.
"""

from __future__ import annotations
import io
import os
import re
import argparse
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PATH_SUMMARY = os.path.join(ROOT, "reports", "S7-S6_ecosystem_learning_summary.md")
PATH_DASHBOARD = os.path.join(ROOT, "reports", "index.html")

MARKER_START = "<!-- S7-S6 OVERLAY START -->"
MARKER_END = "<!-- S7-S6 OVERLAY END -->"


def _parse_summary(path: str) -> dict:
    """Parse key metrics, sparklines, and the learning note from the S7-S6 report."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"S7-S6 summary not found at {path}")

    with io.open(path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]

    data = {
        "generated": None,
        "clarity_last": 0.0,
        "clarity_slope": 0.0,
        "empathy_last": 0.0,
        "empathy_slope": 0.0,
        "return_ratio": "—",
        "bias_drift": 0.0,
        "spark_clarity": "",
        "spark_empathy": "",
        "learning_note": "",
    }

    # simple state for narrative extraction
    in_learning = False
    learning_lines = []

    for ln in lines:
        # Generated line
        if ln.startswith("**Generated:**"):
            # e.g. **Generated:** 2025-11-03T03:53:03.123456+00:00 (UTC)
            m = re.search(r"\*\*Generated:\*\*\s*([0-9T:\.\+\-Z]+)", ln)
            if m:
                data["generated"] = m.group(1)

        # Vitals
        if ln.lstrip().startswith("- Rolling Clarity"):
            # - Rolling Clarity Δ (EMA last): 0.123  • trend slope: +0.0003
            m = re.search(r":\s*([-0-9\.]+).+slope:\s*([+\-0-9\.]+)", ln)
            if m:
                data["clarity_last"] = float(m.group(1))
                data["clarity_slope"] = float(m.group(2))
            continue

        if ln.lstrip().startswith("- Rolling Empathy"):
            m = re.search(r":\s*([-0-9\.]+).+slope:\s*([+\-0-9\.]+)", ln)
            if m:
                data["empathy_last"] = float(m.group(1))
                data["empathy_slope"] = float(m.group(2))
            continue

        if ln.lstrip().startswith("- Reciprocity Return Ratio"):
            # e.g. "- Reciprocity Return Ratio (>0): 52.3%"
            parts = ln.split(":", 1)
            if len(parts) == 2:
                data["return_ratio"] = parts[1].strip()
            continue

        if ln.lstrip().startswith("- Bias-Vector Drift"):
            m = re.search(r":\s*([-0-9\.]+)", ln)
            if m:
                data["bias_drift"] = float(m.group(1))
            continue

        # Sparklines
        if ln.lstrip().startswith("**Clarity Δ spark:**"):
            m = re.search(r"`([^`]+)`", ln)
            if m:
                data["spark_clarity"] = m.group(1)
            continue

        if ln.lstrip().startswith("**Empathy spark:**"):
            m = re.search(r"`([^`]+)`", ln)
            if m:
                data["spark_empathy"] = m.group(1)
            continue

        # Learning narrative
        if ln.startswith("## What the System Is Learning"):
            in_learning = True
            continue

        if in_learning:
            # stop at next section
            if ln.startswith("## "):
                in_learning = False
                continue
            if ln.strip():
                learning_lines.append(ln.strip())

    data["learning_note"] = " ".join(learning_lines).strip()
    return data


def _build_overlay_html(data: dict) -> str:
    """Return the full HTML overlay block, including markers."""
    gen = data.get("generated") or datetime.now(timezone.utc).isoformat()
    clarity_last = data["clarity_last"]
    clarity_slope = data["clarity_slope"]
    empathy_last = data["empathy_last"]
    empathy_slope = data["empathy_slope"]
    return_ratio = data["return_ratio"]
    bias_drift = data["bias_drift"]
    spark_c = data["spark_clarity"] or "·" * 12
    spark_e = data["spark_empathy"] or "·" * 12
    note = data["learning_note"] or "No reciprocity events in the current window; overlay is in heartbeat mode."

    trend_c = "rising" if clarity_slope > 0 else "flattening" if abs(clarity_slope) < 1e-4 else "declining"
    trend_e = "rising" if empathy_slope > 0 else "flattening" if abs(empathy_slope) < 1e-4 else "declining"

    # Ecosystem status badge
    is_heartbeat = ("No reciprocity events were found" in note) or ("heartbeat mode" in note)
    status_label = "HEARTBEAT ONLY" if is_heartbeat else "ACTIVE"
    status_bg = "#6b7280" if is_heartbeat else "#16a34a"   # gray vs green
    status_fg = "#ffffff"

    return f"""{MARKER_START}
<div class="card">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <h2 style="margin:0;">Stage 7 — Ecosystem Learning Overlay</h2>
    <span class="pill" style="
      background:{status_bg};
      color:{status_fg};
      padding:2px 10px;
      border-radius:999px;
      font-size:0.75rem;
      font-weight:500;
      white-space:nowrap;">
      Ecosystem: {status_label}
    </span>
  </div>
  <p style="margin-top:4px; color:#6b7280; font-size:0.85rem;">
    Source: <code>S7-S6_ecosystem_learning_summary.md</code> • Generated: {gen}
  </p>

  <div class="grid" style="margin-top:8px;">
    <div>
      <h3 style="margin:0 0 4px 0; font-size:0.95rem;">Clarity Δ</h3>
      <p style="margin:0; font-size:0.9rem;">
        EMA last: <strong>{clarity_last:.3f}</strong><br/>
        Trend slope: <span>{clarity_slope:+.4f}</span><br/>
        State: <span style="text-transform:capitalize;">{trend_c}</span>
      </p>
    </div>
    <div>
      <h3 style="margin:0 0 4px 0; font-size:0.95rem;">Empathy</h3>
      <p style="margin:0; font-size:0.9rem;">
        EMA last: <strong>{empathy_last:.3f}</strong><br/>
        Trend slope: <span>{empathy_slope:+.4f}</span><br/>
        State: <span style="text-transform:capitalize;">{trend_e}</span>
      </p>
    </div>
    <div>
      <h3 style="margin:0 0 4px 0; font-size:0.95rem;">Ecosystem Vitals</h3>
      <p style="margin:0; font-size:0.9rem;">
        Reciprocity Return Ratio: <strong>{return_ratio}</strong><br/>
        Bias Drift (L2): <strong>{bias_drift:.3f}</strong>
      </p>
    </div>
  </div>

  <div style="margin-top:12px;">
    <h3 style="margin:0 0 4px 0; font-size:0.95rem;">Learning Trend — Clarity Δ vs Empathy</h3>
    <p style="margin:0; font-size:0.8rem; color:#6b7280;">
      ASCII sparkline chart over the rolling window (same points used in S7-S6).
    </p>
    <pre style="margin:4px 0 0 0; font-size:0.85rem; font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;">
Clarity Δ: {spark_c}
Empathy : {spark_e}
    </pre>
  </div>

  <div style="margin-top:12px;">
    <h3 style="margin:0 0 4px 0; font-size:0.95rem;">What the System Is Learning</h3>
    <p style="margin:0; font-size:0.9rem; line-height:1.45;">
      {note}
    </p>
  </div>
</div>
{MARKER_END}"""


def _update_dashboard(html_path: str, overlay_html: str, debug: bool = False):
    if not os.path.exists(html_path):
        raise FileNotFoundError(f"Dashboard HTML not found at {html_path}")

    with io.open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    start_idx = html.find(MARKER_START)
    end_idx = html.find(MARKER_END)

    if start_idx != -1 and end_idx != -1:
        end_idx += len(MARKER_END)
        if debug:
            print("[S8-S1] Replacing existing overlay block in index.html")
        new_html = html[:start_idx] + overlay_html + html[end_idx:]
    else:
        # append before </body> if markers not present
        if debug:
            print("[S8-S1] Inserting new overlay block into index.html")
        insert_pos = html.lower().rfind("</body>")
        if insert_pos == -1:
            insert_pos = len(html)
        # ensure a blank line before
        new_html = html[:insert_pos] + "\n" + overlay_html + "\n" + html[insert_pos:]

    with io.open(html_path, "w", encoding="utf-8") as f:
        f.write(new_html)


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--debug", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main():
    args = _parse_args()

    if args.debug:
        print("[S8-S1] Using summary:", PATH_SUMMARY)
        print("[S8-S1] Updating dashboard:", PATH_DASHBOARD)

    data = _parse_summary(PATH_SUMMARY)
    overlay_html = _build_overlay_html(data)

    if args.debug:
        print("[S8-S1] Overlay preview:\n", overlay_html[:200], "...\n")

    if args.dry_run:
        print("[S8-S1] Dry-run enabled; not writing to index.html")
        return

    _update_dashboard(PATH_DASHBOARD, overlay_html, debug=args.debug)

    if args.debug:
        print("[S8-S1] Done. Dashboard overlay updated.")


if __name__ == "__main__":
    main()
