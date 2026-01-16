#!/usr/bin/env python3
"""
scripts/runtime_emit_demo.py

Stage 14 — Runtime wiring demo

This is an explicit, one-command runtime emitter that:
- Runs the Elenx engine (analyze → questions)
- Constructs an "attempted" output kind + content
- Calls the single intended call site: src.runtime_finalize.finalize_output()
- Prints the final output (possibly BLOCK-replaced QUESTIONS)

Usage:
  python -u scripts/runtime_emit_demo.py --text "..." --kind QUESTIONS
  python -u scripts/runtime_emit_demo.py --text "..." --kind INSTRUCTIONS --irreversible --distortion --window-low
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from src.elenx_engine import ElenxEngine
from src.elenx_loader import load_packs
from src.runtime_finalize import finalize_output


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_did() -> str:
    return datetime.now(timezone.utc).strftime("DID_%Y%m%dT%H%M%SZ")


def render_attempted(kind: str, det, questions) -> Tuple[str, Dict[str, Any]]:
    """
    Produce an attempted output payload.

    Discipline:
    - QUESTIONS kind is always safe.
    - INSTRUCTIONS/ADVICE/ACTION is treated as action-like and subject to Stage 14.
    """
    meta = {
        "mode": getattr(det, "mode", None),
        "principle": getattr(det, "principle", None),
        "confidence": getattr(det, "confidence", None),
        "ts_utc": utc_now_iso(),
    }

    if kind == "QUESTIONS":
        lines = []
        lines.append(f"Mode×Principle: {meta['mode']} × {meta['principle']} (conf={meta['confidence']})")
        lines.append("")
        for i, q in enumerate(questions or [], 1):
            lines.append(f"{i}. {q}")
        content = "\n".join(lines).strip() + "\n"
        return content, meta

    # For demo purposes, provide an "action-like" attempted content.
    # This is intentionally simple: the point is Stage 14 gating, not advice quality.
    content = (
        "Attempted action-guiding output (demo):\n"
        "- Step 1: Do X.\n"
        "- Step 2: Do Y.\n"
        "- Step 3: Do Z.\n"
    )
    return content, meta


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 14 runtime wiring demo emitter")
    ap.add_argument("--text", required=True, help="Input text to analyze")
    ap.add_argument("--kind", default="QUESTIONS", choices=["QUESTIONS", "REFRAME", "INSTRUCTIONS", "ADVICE", "ACTION"])
    ap.add_argument("--input-type", default="S", help="Internal input type label, e.g., S/Q")
    ap.add_argument("--user-id", default=None, help="Optional user_id for logging/audit")
    ap.add_argument("--trace-ref", default=None, help="Optional trace ref string")

    # Governance signals (Charter §4)
    ap.add_argument("--irreversible", action="store_true", help="Signal: irreversible_risk=True")
    ap.add_argument("--distortion", action="store_true", help="Signal: distortion_present=True")
    ap.add_argument("--window-low", action="store_true", help="Signal: insufficient_reflection_window=True")

    ap.add_argument("--debug", action="store_true", help="Print decision_info JSON")
    args = ap.parse_args()

    # Engine run (packs required by repo contract)
    packs = load_packs()
    engine = ElenxEngine(packs)

    det, questions = engine.analyze(args.text, empathy_on=True)

    # Construct attempted output
    did = make_did()
    attempted_content, meta = render_attempted(args.kind, det, questions)

    # SINGLE intended call site (Stage 14 wiring)
    final_kind, final_content, decision_info = finalize_output(
        did=did,
        input_type=args.input_type,
        output_kind=args.kind,
        content=attempted_content,
        irreversible_risk=args.irreversible,
        distortion_present=args.distortion,
        insufficient_reflection_window=args.window_low,
        user_id=args.user_id,
        mode=getattr(det, "mode", None),
        principle=getattr(det, "principle", None),
        trace_ref=args.trace_ref,
        meta=meta,
        extra={"demo": True, "source": "scripts/runtime_emit_demo.py"},
    )

    # Emit final output
    print("")
    print("=== FINAL OUTPUT ===")
    print(f"kind={final_kind}")
    print("--------------------")
    print(final_content)

    if args.debug:
        print("")
        print("=== DECISION INFO (debug) ===")
        print(json.dumps(decision_info, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
