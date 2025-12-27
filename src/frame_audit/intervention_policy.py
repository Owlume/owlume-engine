from __future__ import annotations

from typing import Optional

from .interventions import InterventionID
from .types import FrameAuditResult

CHECK_TO_INTERVENTION: dict[str, InterventionID] = {
    "FA-001": InterventionID.FIX_EXPAND_OPTIONS,
    "FA-002": InterventionID.FIX_ADD_SUCCESS_CRITERIA,
    "FA-003": InterventionID.FIX_ADD_STAKEHOLDERS,
    "FA-004": InterventionID.FIX_TIGHTEN_SCOPE,
    "FA-005": InterventionID.FIX_ADD_CONSTRAINTS,      # closest deterministic template
    "FA-006": InterventionID.FIX_ADD_CONSTRAINTS,      # conflict => force explicit constraints/tradeoffs
}

PRIORITY: list[str] = ["FA-002", "FA-001", "FA-003", "FA-006", "FA-005", "FA-004"]

def select_primary_intervention(result: FrameAuditResult) -> Optional[InterventionID]:
    rb = result.risk_breakdown or {}
    for check_id in PRIORITY:
        if rb.get(check_id, 0.0) > 0.0:
            return CHECK_TO_INTERVENTION.get(check_id)
    return None

def rank_interventions(result: FrameAuditResult) -> list[InterventionID]:
    chosen: list[InterventionID] = []
    rb = result.risk_breakdown or {}
    for check_id in PRIORITY:
        if rb.get(check_id, 0.0) <= 0.0:
            continue
        iv = CHECK_TO_INTERVENTION.get(check_id)
        if iv and iv not in chosen:
            chosen.append(iv)
    return chosen


