from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

Span = Tuple[int, int]  # (start, end)

@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    name: str
    description: str
    weight: float  # contribution to risk
    severity: str  # "low"|"medium"|"high"
    enabled: bool = True

@dataclass
class CheckHit:
    check_id: str
    score: float              # 0..1 for that check
    evidence_spans: List[Span] = field(default_factory=list)
    rationale: str = ""

@dataclass
class FrameAuditTrace:
    spec: Dict[str, Any]
    text: str
    context: Optional[Dict[str, Any]]
    hits: List[CheckHit]
    risk_breakdown: Dict[str, float]
    frame_risk_score: float

@dataclass
class FrameAuditResult:
    spec: Dict[str, Any]
    frame_risk_score: float
    risk_breakdown: Dict[str, float]
    trace: FrameAuditTrace

