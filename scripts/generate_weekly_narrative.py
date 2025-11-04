#!/usr/bin/env python3
import argparse, glob, json, os, statistics
from datetime import datetime, timezone, timedelta

def load_recent_aggregates(pattern: str, days=7):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = []
    for p in sorted(glob.glob(pattern)):
        try:
            ts = datetime.fromtimestamp(os.path.getmtime(p), timezone.utc)
            if ts >= cutoff:
                with open(p, "r", encoding="utf-8") as f:
                    items.append((ts, json.load(f)))
        except Exception:
            pass
    return items

def render_md(week_iso: str, vitals_sample, aggregates):
    deltas = [a.get("avg_delta") for _, a in aggregates if "avg_delta" in a]
    empathy_rates = [a.get("empathy_rate") for _, a in aggregates if "empathy_rate" in a]
    positive = [a.get("positive_rate") for _, a in aggregates if "positive_rate" in a]

    md = []
    md.append(f"# 7 Days of Clarity — Week {week_iso}")
    md.append("")
    if vitals_sample:
        md.append(f"**Last Vitals:** Δ̄={vitals_sample['delta_avg']:.3f} • Empathy={vitals_sample['empathy_rate']*100:.1f}% • Positive={vitals_sample['positive_rate']*100:.1f}% • Drift={vitals_sample['drift']:.3f} • Tunnel={vitals_sample['tunnel']:.3f} • Aim={vitals_sample['aim']}")
        md.append("")

    if deltas:
        md.append(f"- Δavg (week): mean={statistics.mean(deltas):.3f}, max={max(deltas):.3f}, min={min(deltas):.3f}")
    if empathy_rates:
        md.append(f"- Empathy rate (week): mean={statistics.mean(empathy_rates)*100:.1f}%")
    if positive:
        md.append(f"- Positive rate (week): mean={statistics.mean(positive)*100:.1f}%")
    md.append("")

    md.append("## Highlights")
    md.append("- Top clarity gains and where they happened (Modes × Principles).")
    md.append("- Biggest drifts and how we corrected them.")
    md.append("- Notable empathy assists that changed outcomes.")

    md.append("")
    md.append("## Next Week Focus")
    md.append("- Guardrails for drift/tunnel.")
    md.append("- One experiment to raise empathy activation.")
    md.append("- One question to ask before first meeting each day.")
    md.append("")
    return "\n".join(md)

def read_last_summary(summary_path: str):
    if not os.path.exists(summary_path):
        return None
    with open(summary_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f).get("vitals")
        except Exception:
            return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aggregates_glob", default="data/metrics/aggregates_*.json")
    ap.add_argument("--summary_json", default="reports/summary.json")
    ap.add_argument("--out_dir", default="reports/weekly")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    week_iso = datetime.now(timezone.utc).date().isocalendar()
    week_tag = f"{week_iso[0]}-W{week_iso[1]:02d}"

    vitals = read_last_summary(args.summary_json)  # from S6-S4
    aggs = load_recent_aggregates(args.aggregates_glob, days=7)

    md = render_md(week_tag, vitals, aggs)
    out_path = os.path.join(args.out_dir, f"weekly_{week_tag}.md")
    with open(out_path, "w", encoding="utf-8") as w:
        w.write(md)
    print(f"[S6-S2] weekly narrative → {out_path}")

if __name__ == "__main__":
    main()
