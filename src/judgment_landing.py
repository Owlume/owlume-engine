# src/judgment_landing.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Optional


# Must match clarity_gain_record.schema.json enums
JudgmentType = Literal["position", "constraint", "next_step", "defer"]

ACK_TEXT = "This judgment is mine. Owlume did not decide for me."


class JudgmentLandingError(RuntimeError):
    """Raised when an Owlume interaction attempts to terminate without a valid Judgment Landing."""


@dataclass(frozen=True)
class JudgmentTerminalState:
    type: JudgmentType
    statement: str
    confidence: float
    owner: Literal["user"]
    acknowledged: bool
    timestamp: str  # ISO-8601 date-time


def _iso_now() -> str:
    # timezone-aware ISO-8601; jsonschema 'date-time' accepts this format
    return datetime.now(timezone.utc).isoformat()


def build_judgment_terminal_state(
    *,
    jtype: JudgmentType,
    statement: str,
    confidence: float,
    acknowledged: bool,
) -> JudgmentTerminalState:
    """
    Build the terminal judgment state.

    Governance invariant:
    - Must be user-owned.
    - Must be explicitly acknowledged.
    - Must be structurally valid and bounded.
    """
    # Strict enum
    if jtype not in ("position", "constraint", "next_step", "defer"):
        raise JudgmentLandingError(f"Invalid judgment type: {jtype}")

    s = (statement or "").strip()
    if len(s) < 10:
        raise JudgmentLandingError("Judgment statement too short (min 10 chars).")
    if len(s) > 500:
        raise JudgmentLandingError("Judgment statement too long (max 500 chars).")

    try:
        c = float(confidence)
    except Exception as e:
        raise JudgmentLandingError("Confidence must be a number in [0,1].") from e

    if not (0.0 <= c <= 1.0):
        raise JudgmentLandingError("Confidence must be between 0.0 and 1.0.")

    if acknowledged is not True:
        # Authority seal: no ack = no termination
        raise JudgmentLandingError("Responsibility acknowledgment must be true.")

    return JudgmentTerminalState(
        type=jtype,
        statement=s,
        confidence=c,
        owner="user",
        acknowledged=True,
        timestamp=_iso_now(),
    )


def enforce_judgment_landing_on_termination(jts: Optional[JudgmentTerminalState]) -> None:
    """
    Termination gate: an Owlume interaction may not end without a valid judgment terminal state.

    IMPORTANT:
    - This function must be pure validation only.
    - It must not mutate any external record/dict.
    """
    if jts is None:
        raise JudgmentLandingError("Missing judgment_terminal_state; cannot terminate interaction.")

    if jts.owner != "user":
        raise JudgmentLandingError("Judgment terminal state must be user-owned (owner='user').")

    if jts.acknowledged is not True:
        raise JudgmentLandingError("Judgment terminal state must be acknowledged (acknowledged=true).")

    # Defensive bounds (schema will also validate)
    if jts.type not in ("position", "constraint", "next_step", "defer"):
        raise JudgmentLandingError(f"Invalid judgment type in terminal state: {jts.type}")

    if not isinstance(jts.statement, str) or len(jts.statement.strip()) < 10:
        raise JudgmentLandingError("Judgment statement too short/invalid in terminal state.")

    if not (0.0 <= float(jts.confidence) <= 1.0):
        raise JudgmentLandingError("Confidence out of range in terminal state.")
