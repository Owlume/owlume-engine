# src/block_runtime.py
# Stage 14 — BLOCK Runtime Wiring (Execution Layer)
#
# Policy note:
# - Non-tunable. No thresholds in config.
# - Narrow interpretation: prefer false negatives over false positives.
# - Constrains action only; preserves analysis/questions.

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import json
import os
import uuid


BLOCK_LOG_PATH = os.path.join("data", "logs", "block_events.jsonl")


@dataclass(frozen=True)
class BlockInputs:
    # Boundary classification (must be set by caller):
    action_imminent: bool  # Charter §4(1)

    # Irreversibility assessment (must be set by caller; boolean, not a score):
    irreversible_risk: bool  # Charter §4(2)

    # Distortion presence (must be set by caller using existing signals):
    distortion_present: bool  # Charter §4(3)

    # Reflection window (must be set by caller from trace / session state):
    insufficient_reflection_window: bool  # Charter §4(4)


@dataclass(frozen=True)
class BlockDecision:
    triggered: bool
    # A closed, auditable reason code set (no extension without new Stage):
    reason_code: Optional[str]  # "BLOCK_STAGE14_ALL_CONDITIONS_MET" or None
    # Mirrors the 4 legitimacy conditions for review:
    conditions: Dict[str, bool]


def decide_block(inputs: BlockInputs) -> BlockDecision:
    """
    Decide BLOCK strictly per Stage 14 Charter §4.
    Narrow interpretation: all four must be true.
    """
    conditions = {
        "action_imminent": bool(inputs.action_imminent),
        "irreversible_risk": bool(inputs.irreversible_risk),
        "distortion_present": bool(inputs.distortion_present),
        "insufficient_reflection_window": bool(inputs.insufficient_reflection_window),
    }
    triggered = all(conditions.values())
    reason_code = "BLOCK_STAGE14_ALL_CONDITIONS_MET" if triggered else None
    return BlockDecision(triggered=triggered, reason_code=reason_code, conditions=conditions)


def emit_block_event(
    *,
    decision: BlockDecision,
    did: str,
    user_id: Optional[str],
    input_type: str,
    output_type_attempted: str,
    mode: Optional[str],
    principle: Optional[str],
    trace_ref: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Append-only event emission. Does not alter runtime behavior besides logging.
    Must be called iff decision.triggered is True.
    """
    if not decision.triggered:
        raise ValueError("emit_block_event called when decision.triggered is False")

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "BLOCK_TRIGGERED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "did": did,
        "user_id": user_id,
        "input_type": input_type,
        "output_type_attempted": output_type_attempted,
        "mode": mode,
        "principle": principle,
        "reason_code": decision.reason_code,
        "conditions": decision.conditions,
        "trace_ref": trace_ref,
        "extra": extra or {},
        "policy": {
            "stage": 14,
            "charter": "Stage 14 — BLOCK Governance Charter",
            "review_protocol": "Stage 14 — BLOCK Review & Audit Protocol",
            "interpretation": "narrow",
            "tunable": False,
        },
    }

    os.makedirs(os.path.dirname(BLOCK_LOG_PATH), exist_ok=True)
    with open(BLOCK_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event
