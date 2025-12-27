from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .types import CheckHit
from . import rules

Detector = Callable[[str, Optional[Dict[str, Any]]], Optional[CheckHit]]

def detect_fa_001_false_dichotomy(text: str, context: Optional[Dict[str, Any]] = None) -> Optional[CheckHit]:
    spans = rules.find_false_dichotomy_spans(text)
    if not spans:
        return None
    return CheckHit(
        check_id="FA-001",
        score=1.0,
        evidence_spans=spans,
        rationale="Forced binary language detected (either/or, choose one, or-else framing).",
    )

def detect_fa_002_undefined_success(text: str, context: Optional[Dict[str, Any]] = None) -> Optional[CheckHit]:
    if rules.has_explicit_success_criteria(text, context):
        return None
    return CheckHit(
        check_id="FA-002",
        score=1.0,
        evidence_spans=[],
        rationale="No measurable success criteria detected (metric + threshold/timeframe).",
    )

def detect_fa_003_missing_stakeholders(text: str, context: Optional[Dict[str, Any]] = None) -> Optional[CheckHit]:
    if rules.has_stakeholders(text, context):
        return None
    return CheckHit(
        check_id="FA-003",
        score=1.0,
        evidence_spans=[],
        rationale="Stakeholders not explicitly named in text or context.",
    )

def detect_fa_004_scope_creep(text: str, context: Optional[Dict[str, Any]] = None) -> Optional[CheckHit]:
    sig = rules.scope_creep_signal(text)
    if sig < 0.5:
        return None
    return CheckHit(
        check_id="FA-004",
        score=min(1.0, sig),
        evidence_spans=[],
        rationale="Multiple deliverables/add-ons without boundaries (scope creep signal).",
    )

def detect_fa_005_timeframe_ambiguous(text: str, context: Optional[Dict[str, Any]] = None) -> Optional[CheckHit]:
    sig = rules.timeframe_ambiguous_signal(text, context)
    if sig <= 0.0:
        return None
    return CheckHit(
        check_id="FA-005",
        score=1.0,
        evidence_spans=[],
        rationale="Urgency language (soon/ASAP) without a concrete timeframe.",
    )

def detect_fa_006_constraint_conflict(text: str, context: Optional[Dict[str, Any]] = None) -> Optional[CheckHit]:
    sig = rules.constraint_conflict_signal(text)
    if sig <= 0.0:
        return None
    return CheckHit(
        check_id="FA-006",
        score=1.0,
        evidence_spans=[],
        rationale="Conflicting constraints detected (e.g., perfect/ASAP combined with no budget/resources).",
    )

DETECTORS: Dict[str, Detector] = {
    "FA-001": detect_fa_001_false_dichotomy,
    "FA-002": detect_fa_002_undefined_success,
    "FA-003": detect_fa_003_missing_stakeholders,
    "FA-004": detect_fa_004_scope_creep,
    "FA-005": detect_fa_005_timeframe_ambiguous,
    "FA-006": detect_fa_006_constraint_conflict,
}
