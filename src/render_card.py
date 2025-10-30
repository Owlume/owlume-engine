# src/render_card.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path
import json, os

# ---------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------
def _get(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur = d
    for key in path.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur

def write_clarity_card_md(record: dict, out_path: Path) -> Path:
    md = render_clarity_card(record)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    return out_path

def _fmt_delta(x: float) -> str:
    sign = "+" if x >= 0 else "-"
    return f"{sign}{abs(x):.2f}"

def _tier_from_delta(delta: float, th: Dict[str, float]) -> str:
    low, med, high = th.get("low",0.1), th.get("medium",0.25), th.get("high",0.4)
    if delta >= high: return "HIGH"
    if delta >= med:  return "MED"
    if delta >= low:  return "LOW"
    return "—"

def _first_nonempty(*vals: Optional[str]) -> str:
    for v in vals:
        if isinstance(v,str) and v.strip():
            return v.strip()
    return "-"

def _coerce_questions(rec: Dict[str,Any]) -> List[Dict[str,str]]:
    out=[]
    raw=rec.get("questions")
    if isinstance(raw,list):
        for q in raw:
            if isinstance(q,dict):
                voice=_first_nonempty(q.get("voice"),q.get("label"),"?")
                text=_first_nonempty(q.get("text"),q.get("question"),"")
                if text: out.append({"voice":voice,"text":text})
    if not out and isinstance(rec.get("voices"),dict):
        for v,items in rec["voices"].items():
            if isinstance(items,list):
                for t in items:
                    if isinstance(t,str) and t.strip():
                        out.append({"voice":v,"text":t.strip()})
    return out[:3]

# ---------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------
def render_clarity_card(record: Dict[str, Any],
                        thresholds: Optional[Dict[str, float]] = None) -> str:
    # --- Title: Mode × Principle (support both shapes) ---
    det = record.get("detection", {}) if isinstance(record.get("detection"), dict) else {}
    mode = _first_nonempty(
        det.get("mode"),
        record.get("mode_detected"),
        record.get("mode")
    )
    principle = _first_nonempty(
        det.get("principle"),
        record.get("principle_detected"),
        record.get("principle")
    )

    # --- Clarity Gain numbers ---
    cg_pre, cg_post = record.get("cg_pre"), record.get("cg_post")
    cg_delta = record.get("cg_delta") or (
        (float(cg_post) - float(cg_pre))
        if isinstance(cg_pre, (int, float)) and isinstance(cg_post, (int, float))
        else 0.0
    )

    th = thresholds or record.get("thresholds") or {"low": 0.1, "medium": 0.25, "high": 0.4}
    tier = _tier_from_delta(float(cg_delta), th)

    # --- Contexts & proof signals (optional) ---
    ctx = _get(record, "tags.contexts", []) or record.get("context_drivers", [])
    if not isinstance(ctx, list):
        ctx = []
    ctx_str = ", ".join(x for x in ctx if isinstance(x, str) and x.strip()) or "-"

    proof = record.get("proof_signals") or _get(record, "signals.proof", [])
    if not isinstance(proof, list):
        proof = []
    proof_str = ", ".join(x for x in proof if isinstance(x, str) and x.strip()) or "-"

    # --- Questions (will be empty for your current JSONL, which is fine) ---
    qs = _coerce_questions(record)
    q_md = "\n".join(f"{i + 1}. **{q['voice']}** → {q['text']}" for i, q in enumerate(qs)) or "_No questions._"

    # --- Formatting helpers ---
    def _fmt(x):
        try:
            return f"{float(x):.2f}"
        except Exception:
            return "-"

    cg_line = f"{_fmt(cg_pre)} → {_fmt(cg_post)} (Δ {_fmt_delta(float(cg_delta))}) [{tier}]"

    # --- Empathy state if present ---
    empathy_state = _first_nonempty(record.get("empathy_state"))
    empathy_line = f"\n> **Empathy:** {empathy_state}" if empathy_state != "-" else ""

    # --- Timestamp & ID (prefer did → id → _id) ---
    ts = _first_nonempty(str(record.get("timestamp", "")).replace("T", " "), str(record.get("time", "")))
    rid = _first_nonempty(str(record.get("did", "")), str(record.get("id", "")), str(record.get("_id", "")))
    meta = f"\n> _{ts} • id:{rid}_" if ts != "-" or rid != "-" else ""

    # --- Final Markdown block ---
    md = (
        f"> **Mode × Principle:** {mode} × {principle}\n"
        f"> **Top 3 questions**\n> {q_md.replace('\n', '\n> ')}\n"
        f"> **Clarity Gain:** {cg_line}"
        f"{empathy_line}\n"
        f"> **Context:** {ctx_str}\n"
        f"> **Proof signals:** {proof_str}{meta}"
    )
    return md

# --- add near the bottom of src/render_card.py (above the __main__ block) ---

from pathlib import Path

def write_clarity_card_md(record: dict, out_path: Path) -> Path:
    """Render a single record as Markdown and write it to disk."""
    md = render_clarity_card(record)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    return out_path


# CLI single test
if __name__ == "__main__":
    sample = {
        "detection":{"mode":"Decision Strategy","principle":"Evidence & Validation"},
        "questions":[
            {"voice":"Thiel","text":"What would invalidate the evidence?"},
            {"voice":"Feynman","text":"Explain the core claim simply."},
            {"voice":"Peterson","text":"Start with the smallest test."}
        ],
        "cg_pre":0.32,"cg_post":0.68,
        "tags":{"contexts":["Incentive Misalignment","Stakeholder Conflict"]},
        "proof_signals":["Depth-of-Reflection ↑","Rare Insight"],
        "timestamp":"2025-10-18T13:45:00","id":"demo-1"
    }
    print(render_clarity_card(sample))
