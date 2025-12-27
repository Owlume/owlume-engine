from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

Span = Tuple[int, int]  # (start, end)

@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    name: str
    description: str
    weight: float
    severity: str
    enabled: bool = True

@dataclass
class CheckHit:
    check_id: str
    score: float
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

    @property
    def result(self) -> Dict[str, Any]:
        """
        Backward-compatible dict view used by tests/harness code.
        """
        return {
            "frame_risk_score": self.frame_risk_score,
            "risk_breakdown": self.risk_breakdown,
            "hits": [h.check_id for h in (self.trace.hits or [])],
        }

    @property
    def checks(self) -> List[Dict[str, Any]]:
        """
        Backward-compatible list-of-dicts view:
            [{"check_id": "...", "triggered": bool, ...}, ...]
        Uses CHECK_SPECS ordering when available.
        """
        # Import here to avoid import cycles at module load time.
        try:
            from .check_registry import CHECK_SPECS  # type: ignore
            ordered_ids = [c.check_id for c in CHECK_SPECS]
            spec_by_id = {c.check_id: c for c in CHECK_SPECS}
        except Exception:
            ordered_ids = list((self.risk_breakdown or {}).keys())
            spec_by_id = {}

        hits = self.trace.hits or []
        hit_by_id = {h.check_id: h for h in hits}

        out: List[Dict[str, Any]] = []
        rb = self.risk_breakdown or {}

        # Ensure we include all ordered specs
        for cid in ordered_ids:
            h = hit_by_id.get(cid)
            triggered = h is not None
            spec = spec_by_id.get(cid)

            out.append(
                {
                    "check_id": cid,
                    "triggered": triggered,
                    "score": float(getattr(h, "score", 0.0)) if triggered else 0.0,
                    "weight": float(getattr(spec, "weight", 0.0)) if spec else 0.0,
                    "risk": float(rb.get(cid, 0.0)),
                    "evidence_spans": list(getattr(h, "evidence_spans", [])) if triggered else [],
                    "rationale": str(getattr(h, "rationale", "")) if triggered else "",
                    "name": str(getattr(spec, "name", "")) if spec else "",
                    "severity": str(getattr(spec, "severity", "")) if spec else "",
                }
            )

        # Include any extra hits not in registry (defensive)
        for h in hits:
            if h.check_id in set(ordered_ids):
                continue
            out.append(
                {
                    "check_id": h.check_id,
                    "triggered": True,
                    "score": float(h.score),
                    "weight": 0.0,
                    "risk": float(rb.get(h.check_id, 0.0)),
                    "evidence_spans": list(h.evidence_spans or []),
                    "rationale": str(h.rationale or ""),
                    "name": "",
                    "severity": "",
                }
            )

        return out



