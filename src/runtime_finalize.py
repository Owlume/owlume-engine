# src/runtime_finalize.py
# Stage 14 — Runtime Finalize (Single Intended Call Site)
#
# This module is the ONLY intended call site for src.judgment_gate.apply_judgment_gate.
# Any surface (GPT adapter, CLI, API) must call finalize_output() and must NOT call the gate directly.

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.judgment_gate import (
    JudgmentContext,
    GovernanceSignals,
    OutputPacket,
    apply_judgment_gate,
)


def finalize_output(
    *,
    did: str,
    input_type: str,
    output_kind: str,
    content: str,
    # governance signals (Charter §4)
    irreversible_risk: bool = False,
    distortion_present: bool = False,
    insufficient_reflection_window: bool = False,
    # optional context (for audit trace)
    user_id: Optional[str] = None,
    mode: Optional[str] = None,
    principle: Optional[str] = None,
    trace_ref: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Final output boundary.

    Returns:
      (final_kind, final_content, decision_info)

    Surfaces should display final_content and may use final_kind for UI labels.
    decision_info is diagnostic only; do not use it to tune policy.
    """
    attempted = OutputPacket(
        kind=output_kind,
        content=content,
        meta=(meta or {}),
    )

    ctx = JudgmentContext(
        did=did,
        input_type=input_type,
        user_id=user_id,
        mode=mode,
        principle=principle,
        trace_ref=trace_ref,
        extra=(extra or {}),
    )

    signals = GovernanceSignals(
        irreversible_risk=bool(irreversible_risk),
        distortion_present=bool(distortion_present),
        insufficient_reflection_window=bool(insufficient_reflection_window),
    )

    final_packet, decision_info = apply_judgment_gate(
        ctx=ctx,
        attempted=attempted,
        signals=signals,
    )

    return final_packet.kind, final_packet.content, decision_info
