# src/ui_utils.py
from __future__ import annotations
from typing import Dict, Any

def render_pack_console(pack: Dict[str, Any]) -> str:
    """
    Pretty console renderer for a Question Pack produced by question_renderer.render_question_pack().
    Displays Mode × Principle, confidence, empathy, priors, and numbered questions.
    """
    mode = pack.get("mode_label", "–")
    principle = pack.get("principle_label", "–")
    conf = pack.get("confidence", 0)
    empathy = "🫶" if pack.get("empathy_on") else "–"
    tags = pack.get("tags", {})
    fallacies = ", ".join(tags.get("fallacies", [])) or "–"
    contexts = ", ".join(tags.get("contexts", [])) or "–"

    header = f"\n🦉  Owlume — {mode} × {principle}  ({conf:.2f})"
    header += f"\nEmpathy: {empathy} | Fallacies: {fallacies} | Contexts: {contexts}\n"

    lines = []
    for q in pack.get("questions", []):
        lines.append(f" {q['order']:>2}. {q['text']}")
    return header + "\n".join(lines)

def print_pack_console(pack: Dict[str, Any]) -> None:
    """Direct print helper."""
    print(render_pack_console(pack))

# --- T3-S4: Share UI helpers ---
CHANNEL_ICONS = {
    "markdown": "📝",
    "image": "🖼️",
}

def format_share_footer(share: dict) -> str:
    """
    Returns a small italic footer with a channel icon when share.status == "opt_in".
    Example: _📝 Shared via Markdown • 2025-10-18T14:55:00Z_
    """
    if not share or share.get("status") != "opt_in":
        return ""
    ch = (share.get("channel") or "markdown").lower()
    icon = CHANNEL_ICONS.get(ch, "📤")
    ts = share.get("timestamp") or ""
    label = ch.capitalize()
    return f"\n_{icon} Shared via {label} • {ts}_"
