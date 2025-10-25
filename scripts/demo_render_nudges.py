# scripts/demo_render_nudges.py
# Mini UX Demo — Nudge Cards
# Prints 2–3 nicely styled nudges with tone, reason, and context tags.
#
# Usage:
#   python -u scripts/demo_render_nudges.py
#   python -u scripts/demo_render_nudges.py --input data/runtime/next_nudges.json
#
# The script will read nudges from --input if provided (or a sensible default),
# otherwise it will render 3 sample nudges for demo purposes.

import os
import sys
import json
import argparse
from datetime import datetime

# --- Ensure UTF-8 in Windows terminals (avoids cp1252 errors) ---
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------- Helpers ----------
def human_time(ts: str | None) -> str:
    """Render a friendly timestamp if present; else return '-'."""
    if not ts:
        return "-"
    try:
        # Accepts either ISO-like strings or epoch seconds as string
        if ts.isdigit():
            return datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%SZ")
        # Try parse flexible ISO formats
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%SZ")
    except Exception:
        return ts

def taglist(items) -> str:
    if not items:
        return "-"
    return " ".join(f"`{t}`" for t in items)

def nudge_key(n: dict) -> str:
    """Stable key for dedupe: prefer id; if missing/generic, fall back to title+reason."""
    nid = str(n.get("id", "")).strip().lower()
    if nid and nid not in {"nudge", "nudge_1", "n/a", "-"}:
        return nid
    title = str(n.get("title", "")).strip().lower()
    reason = str(n.get("reason", "")).strip().lower()
    return f"{title}|{reason}"

def dedupe_by_id(items):
    """Remove duplicates using nudge_key while preserving order."""
    seen = set()
    out = []
    for x in items:
        k = nudge_key(x)
        if k in seen:
            continue
        seen.add(k)
        out.append(x)
    return out

def dedupe_by_id(items):
    """Remove duplicates using nudge_key while preserving order."""
    seen = set()
    out = []
    for x in items:
        k = nudge_key(x)
        if k in seen:
            continue
        seen.add(k)
        out.append(x)
    return out

def load_nudges(path: str | None):
    """Load nudges from JSON file. Handles UTF-8, UTF-8 BOM, UTF-16 encodings and multiple wrapper shapes."""
    import json, os

    if not path or not os.path.exists(path):
        return None

    data = None
    last_err = None

    # Try several encodings — PowerShell may add BOM or use UTF-16
    for enc in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            with open(path, "r", encoding=enc) as f:
                data = json.load(f)
            print(f"[info] Loaded {path} using encoding={enc}")
            break
        except Exception as e:
            last_err = e
            data = None

    if data is None:
        print(f"[warn] Could not read nudges from {path}: {last_err}")
        return None

    # --- Normalize outer JSON shapes ---
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # Handle common wrappers used by different generator versions
        for key in ("nudges", "candidates", "items", "results"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # Single-object fallback
        return [data]

    return None

    data = None
    last_err = None
    for enc in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            with open(path, "r", encoding=enc) as f:
                data = json.load(f)
            break  # success
        except Exception as e:
            last_err = e
            data = None

    if data is None:
        print(f"[warn] Could not read nudges from {path}: {last_err}")
        return None

    # Normalize shapes
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "nudges" in data and isinstance(data["nudges"], list):
            return data["nudges"]
        return [data]
    return None

def sample_nudges():
    """Return 3 realistic sample nudges aligned with T5 styles."""
    return [
        {
            "id": "post_session_boost",
            "type": "moment",             # gentle | moment | recovery
            "tone": "encouraging",        # encouraging | neutral | firm
            "title": "Nice work — keep the clarity momentum",
            "message": "Your clarity improved recently. Capture one **next step** while it’s fresh.",
            "reason": "recent session and CG ok",
            "contexts": ["moment", "after_reflection"],
            "suggested_time": "soon",
            "actions": ["Open a quick reflection", "Log a next step"],
            "meta": {"cg_delta": "+0.12", "streak_days": 2, "did": "DID-2025-1042"},
            "timestamp": None
        },
        {
            "id": "gentle_daily_invite",
            "type": "gentle",
            "tone": "neutral",
            "title": "A 60-second check-in",
            "message": "What’s **one thing** today that feels fuzzy? Paste it — I’ll help map the blind spots.",
            "reason": "daily rhythm",
            "contexts": ["daily", "light_touch"],
            "suggested_time": "morning",
            "actions": ["Start a 60-sec reflection"],
            "meta": {"streak_days": 4},
            "timestamp": None
        },
        {
            "id": "streak_recovery",
            "type": "recovery",
            "tone": "firm",
            "title": "Let’s get your clarity streak back",
            "message": "You missed a couple of days. Choose **one** pending decision and we’ll de-risk it together.",
            "reason": "streak dipped",
            "contexts": ["recovery", "streak"],
            "suggested_time": "evening",
            "actions": ["Resume with a quick prompt", "Review recent decisions"],
            "meta": {"missed_days": 2, "last_seen": "2025-10-20T08:41:00Z"},
            "timestamp": None
        },
    ]

def style_pill(text: str, kind: str = "tone", plain: bool = False) -> str:
    """Return a small styled pill for tone/type."""
    if plain:
        return f"**{text.capitalize()}**"
    # Keep symbols minimal and readable in most terminals.
    if kind == "tone":
        icon = {"encouraging": "✨", "neutral": "•", "firm": "⚑"}.get(text, "•")
        return f"{icon} **{text.capitalize()}**"
    if kind == "type":
        icon = {"gentle": "🌤️", "moment": "⏱️", "recovery": "🧭"}.get(text, "🔹")
        return f"{icon} **{text.capitalize()}**"
    return f"**{text}**"

def infer_from_reason(reason: str) -> dict:
    """
    Derive a nudge template from a free-text 'reason' when title/type/tone/message are missing.
    Returns partial fields to merge into the normalized nudge.
    """
    r = (reason or "").lower()

    # Heuristic buckets
    if ("recent session" in r) or ("cg ok" in r) or ("clarity improved" in r):
        return {
            "id": "post_session_boost",
            "type": "moment",
            "tone": "encouraging",
            "title": "Nice work — keep the clarity momentum",
            "message": "Your clarity improved recently. Capture one **next step** while it’s fresh.",
            "actions": ["Open a quick reflection", "Log a next step"],
            "contexts": ["moment", "after_reflection"],
            "suggested_time": "soon",
        }

    if ("daily" in r) or ("morning" in r) or ("rhythm" in r):
        return {
            "id": "gentle_daily_invite",
            "type": "gentle",
            "tone": "neutral",
            "title": "A 60-second check-in",
            "message": "What’s **one thing** today that feels fuzzy? Paste it — I’ll help map the blind spots.",
            "actions": ["Start a 60-sec reflection"],
            "contexts": ["daily", "light_touch"],
            "suggested_time": "morning",
        }

    if ("streak" in r) or ("missed" in r) or ("recovery" in r):
        return {
            "id": "streak_recovery",
            "type": "recovery",
            "tone": "firm",
            "title": "Let’s get your clarity streak back",
            "message": "You missed a couple of days. Choose **one** pending decision and we’ll de-risk it together.",
            "actions": ["Resume with a quick prompt", "Review recent decisions"],
            "contexts": ["recovery", "streak"],
            "suggested_time": "evening",
        }

    # Fallback
    return {}


def normalize_nudge(n: dict) -> dict:
    """Map common generator field names into the renderer's expected schema and infer sensible defaults."""
    if not isinstance(n, dict):
        return {}

    def pick(d, *keys, default=None):
        for k in keys:
            if k in d and d[k] not in (None, "", []):
                return d[k]
        return default

    base = {
        "id": pick(n, "id", "nudge_id", "key", default="nudge"),
        "type": (pick(n, "type", "category", "kind", default="-") or "-").lower(),
        "tone": (pick(n, "tone", "mood", default="neutral") or "neutral").lower(),
        "title": pick(n, "title", "name", "heading", default="Nudge"),
        "message": pick(n, "message", "text", "body", default=""),
        "reason": pick(n, "reason", "why", "rationale", default="-"),
        "contexts": pick(n, "contexts", "context", "tags", default=[]),
        "suggested_time": pick(n, "suggested_time", "when", default="-"),
        "actions": pick(n, "actions", "suggestions", "cta", default=[]),
        "meta": pick(n, "meta", "metadata", default={}),
        "timestamp": pick(n, "timestamp", "ts", default=None),
    }

       # If the generator didn't provide the main UX fields, infer from 'reason'
    if (base["title"] == "Nudge" and base["message"] == "") or base["type"] == "-":
        inferred = infer_from_reason(base.get("reason", ""))

        # Helper: treat these as "missing"/defaults so it's OK to override
        def is_missing(val, defaults):
            return (val is None) or (val == "") or (val in defaults)

        # Overwrite only when base holds defaults
        if is_missing(base.get("id"), {"nudge"}):
            base["id"] = inferred.get("id", base["id"])
        if is_missing(base.get("title"), {"Nudge"}):
            base["title"] = inferred.get("title", base["title"])
        if is_missing(base.get("tone"), {"neutral"}):
            base["tone"] = inferred.get("tone", base["tone"])
        if is_missing(base.get("type"), {"-"}):
            base["type"] = inferred.get("type", base["type"])
        if is_missing(base.get("message"), {""}):
            base["message"] = inferred.get("message", base["message"])
        if is_missing(base.get("suggested_time"), {"-"}):
            base["suggested_time"] = inferred.get("suggested_time", base["suggested_time"])

        # Lists: extend if base is empty
        if not base.get("actions"):
            base["actions"] = inferred.get("actions", base["actions"])
        if not base.get("contexts"):
            base["contexts"] = inferred.get("contexts", base["contexts"])

    return base

def horizontal_rule(width=60) -> str:
    return "—" * width

def render_nudge_md(n: dict, index: int, plain: bool = False) -> str:
    """Render a single nudge as Markdown-ish terminal card."""
    n = normalize_nudge(n)
    nid = n.get("id", f"nudge_{index}")
    ntype = n.get("type", "-")
    tone = n.get("tone", "neutral")
    title = (n.get("title", "Nudge") or "").strip().strip('"').strip("“”'")
    msg = n.get("message", "")
    reason = n.get("reason", "-")
    contexts = n.get("contexts", [])
    when = n.get("suggested_time", "-")
    actions = n.get("actions", [])
    meta = n.get("meta", {})
    ts = human_time(n.get("timestamp"))

    # Build sections
    header = (
        f"### {title}\n"
        f"{style_pill(ntone := tone, 'tone', plain)} • "
        f"{style_pill(ntype := ntype, 'type', plain)}  \n"
        f"`id:{nid}`"
    )
    body = f"{msg}"
    tags = f"**Reason:** {reason}\n**Context:** {taglist(contexts)}\n**When:** `{when}`"
    actions_md = "- " + "\n- ".join(actions) if actions else "- (none)"
    meta_parts = []
    for k, v in (meta or {}).items():
        meta_parts.append(f"`{k}`={v}")
    meta_line = " ".join(meta_parts) if meta_parts else "-"
    footer = f"**Meta:** {meta_line}\n**Timestamp:** `{ts}`"

    card = (
        f"{horizontal_rule()}\n"
        f"{header}\n\n"
        f"{body}\n\n"
        f"{tags}\n\n"
        f"**Actions**\n{actions_md}\n\n"
        f"{footer}\n"
        f"{horizontal_rule()}\n"
    )
    return card

# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser(description="Render Nudge Cards (Mini UX Demo)")
    parser.add_argument("--input", "-i", default="data/runtime/next_nudges.json",
                        help="Path to a JSON file produced by generate_nudge.py")
    parser.add_argument("--max", type=int, default=3, help="Max nudges to render (default: 3)")
    parser.add_argument("--plain", action="store_true", help="Disable emoji/icons")
    args = parser.parse_args()

    nudges = load_nudges(args.input)
    using_samples = False

    # If file loaded but has 0 items, show samples
    if nudges is not None and len(nudges) == 0:
        print("[info] Input file contained 0 nudges; showing samples for demo.")
        nudges = sample_nudges()
        using_samples = True

    # 🔧 Normalize *before* we consider dedupe/top-up so ids/titles are final
    if nudges:
        nudges = [normalize_nudge(n) for n in nudges]  

    # Ensure we always show 2–3 cards for demo polish
    if nudges:
        target = max(2, min(3, args.max))
        if len(nudges) < target:
            extras = sample_nudges()
        # avoid duplicate IDs
            nudges = dedupe_by_id(nudges + extras)[:target]

    if not nudges:
        nudges = sample_nudges()
        using_samples = True

    print("\n=== OWLUME — NUDGE CARDS (T5-S4 Mini UX Demo) ===")
    if using_samples:
        print("Source: samples (no input file found)\n")
    else:
        print(f"Source: {args.input}\n")

    count = 0
    for i, n in enumerate(nudges, 1):
        print(render_nudge_md(n, i, args.plain))
        count += 1
        if count >= max(1, args.max):
            break

    print("Hints:")
    print(" - Pipe this into a Markdown viewer-friendly terminal for richer formatting.")
    print(" - To use real output, run your generator first, e.g.:")
    print("     python -u scripts/generate_nudge.py --templates data/nudge_templates.json "
          "--history data/runtime/nudge_history.json --context data/runtime/nudge_context.json "
          f"--out {args.input}")
    print("")

if __name__ == "__main__":
    main()
