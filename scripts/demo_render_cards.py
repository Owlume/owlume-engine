# scripts/demo_render_cards.py
import json
import os
import sys
from typing import Any, Dict, Optional

# Ensure UTF-8 for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# import renderer
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from render_card import render_clarity_card  # noqa: E402

DEFAULT_JSONL = os.path.join("data", "logs", "clarity_gain_samples.jsonl")
DEFAULT_THRESHOLDS = os.path.join("data", "clarity_gain_thresholds.json")


def load_thresholds(path: str) -> Optional[Dict[str, float]]:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if all(k in raw for k in ("low", "medium", "high")):
        return {"low": raw["low"], "medium": raw["medium"], "high": raw["high"]}
    return {"low": 0.1, "medium": 0.25, "high": 0.4}


def maybe_share_footer(record: Dict[str, Any]) -> str:
    """Return the Markdown footer if share.status == 'opt_in', else empty string."""
    share = record.get("share") or {}
    if share.get("status") == "opt_in":
        ch = (share.get("channel") or "markdown").capitalize()
        ts = share.get("timestamp") or ""
        return f"\n_Shared via {ch} • {ts}_"
    return ""


def main():
    jsonl = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSONL
    th_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_THRESHOLDS
    thresholds = load_thresholds(th_path)

    if not os.path.isfile(jsonl):
        print(f"No JSONL found at: {jsonl}")
        return

    with open(jsonl, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except Exception as e:
                print(f"Skipping invalid line: {e}")
                continue

            # Render the core card
            card_md = render_clarity_card(record, thresholds=thresholds)

            # Append the optional share footer (T3-S3)
            footer = maybe_share_footer(record)
            if footer:
                card_md = f"{card_md}\n{footer}"

            print(card_md)
            print()  # blank line between cards


if __name__ == "__main__":
    main()

