# src/judgment_gate.py
# Stage 14 — Judgment Gate (Output Boundary Governor)
#
# Purpose:
# - This module is the single boundary where Owlume may constrain acting.
# - It must NOT constrain analysis or question generation.
#
# Maximum discipline rules:
# - No thresholds, no config knobs, no overrides.
# - BLOCK runs ONLY for action-like output kinds.
# - BLOCK triggers ONLY when all 4 Charter §4 conditions are true.
# - On BLOCK: preserve seeing by replacing with QUESTIONS (not silence).
#
# Dependencies:
# - src.block_runtime provides decide_block + emit_block_event (append-only logging).

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from src.block_runtime import BlockInputs, decide_block, emit_block_event

# Closed set: these are the only output kinds eligible for Stage 14 gating.
ACTION_KINDS = {"ACTION", "ADVICE", "INSTRUCTIONS"}


@dataclass(frozen=True)
class JudgmentContext:
    """
    Context passed to the output boundary.

    Keep this lean. This is not a feature surface; it is governance plumbing.
    """
    did: str
    input_type: str  # e.g. "S" / "Q" or other internal classification
    user_id: Optional[str] = None
    mode: Optional[str] = None
    principle: Optional[str] = None
    trace_ref: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GovernanceSignals:
    """
    The four Charter §4 signals must be provided as booleans by upstream systems.

    Discipline rule:
    - If uncertain, default these toward False to avoid false positives.
    """
    irreversible_risk: bool
    distortion_present: bool
    insufficient_reflection_window: bool


@dataclass(frozen=True)
class OutputPacket:
    """
    Output boundary representation.

    kind: controls whether Stage 14 gating applies.
    content: user-visible text.
    meta: optional metadata (read-only; should not be required for governance).
    """
    kind: str
    content: str
    meta: Dict[str, Any] = field(default_factory=dict)


def _blocked_replacement_content() -> str:
    """
    Replacement content when BLOCK triggers.
    Must preserve 'seeing' (questions/reframe), not action guidance.
    """
    return (
        "I can’t provide action-guiding instructions here.\n\n"
        "To protect your judgment, let’s widen the reflection window first:\n"
        "1) What is the irreversible downside if you act on this now?\n"
        "2) Which assumption would be most costly if it’s wrong?\n"
        "3) What evidence would change your decision?\n"
        "4) If you advised a trusted peer, what would you tell them to question before acting?\n"
    )


def apply_judgment_gate(
    *,
    ctx: JudgmentContext,
    attempted: OutputPacket,
    signals: GovernanceSignals,
) -> Tuple[OutputPacket, Dict[str, Any]]:
    """
    Stage 14 output boundary gate.

    Returns:
      (final_output_packet, decision_info)

    decision_info is for internal debugging/trace only. It MUST NOT be used
    to tune policy. BLOCK policy is fixed by Charter.
    """
    # Stage 14 applies ONLY to action-like outputs.
    action_imminent = attempted.kind in ACTION_KINDS

    if not action_imminent:
        return attempted, {"blocked": False, "reason": "NON_ACTION_OUTPUT"}

    inputs = BlockInputs(
        action_imminent=True,
        irreversible_risk=bool(signals.irreversible_risk),
        distortion_present=bool(signals.distortion_present),
        insufficient_reflection_window=bool(signals.insufficient_reflection_window),
    )

    decision = decide_block(inputs)

    if not decision.triggered:
        return attempted, {"blocked": False, "reason": "CHARTER_CONDITIONS_NOT_MET", "conditions": decision.conditions}

    # BLOCK triggered: emit immutable event, then replace output with QUESTIONS.
    emit_block_event(
        decision=decision,
        did=ctx.did,
        user_id=ctx.user_id,
        input_type=ctx.input_type,
        output_type_attempted=attempted.kind,
        mode=ctx.mode,
        principle=ctx.principle,
        trace_ref=ctx.trace_ref,
        extra={
            **(ctx.extra or {}),
            "gate": "src/judgment_gate.py",
        },
    )

    blocked = OutputPacket(
        kind="QUESTIONS",
        content=_blocked_replacement_content(),
        meta={
            **(attempted.meta or {}),
            "blocked": True,
            "blocked_by": "STAGE14_BLOCK",
            "blocked_reason_code": decision.reason_code,
        },
    )
    return blocked, {"blocked": True, "reason": "BLOCK_TRIGGERED", "conditions": decision.conditions}
