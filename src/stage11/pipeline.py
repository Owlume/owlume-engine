from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.frame_audit.audit import audit_frame  # existing kernel


@dataclass(frozen=True)
class Stage11Event:
    sample_id: str
    before: float
    after: float
    improved: bool
    interventions: list[str]


def run_on_samples(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Deterministic Stage 11 runner:
    - audits each sample text
    - applies no additional mutation beyond what audit_frame already does
    - produces a stable summary + per-event records
    """
    events: list[Stage11Event] = []

    for s in samples:
        sid = str(s.get("id", "unknown"))
        text = str(s.get("text", ""))

        # Kernel returns FrameAuditResult-like dict/object; we normalize conservatively.
        res = audit_frame(text=text, context={})

        # Normalize FrameAuditResult (object) vs dict outputs deterministically
        before_val = getattr(res, "before_score", None)
        if before_val is None:
            before_val = getattr(res, "frame_risk_score", None)
        before = float(before_val or 0.0)

        after_val = getattr(res, "after_score", None)
        after = float(after_val if after_val is not None else before)

        improved = after < before

        interventions: list[str] = []
        tr = getattr(res, "trace", None) or {}


        cycles = tr.get("cycles") if isinstance(tr, dict) else None
        if cycles and isinstance(cycles, list):
            last = cycles[-1] or {}
            applied = last.get("applied_interventions") or []
            # store as strings for stability
            interventions = [str(x) for x in applied]

        events.append(Stage11Event(
            sample_id=sid,
            before=before,
            after=after,
            improved=improved,
            interventions=interventions,
        ))

    n = len(events)
    mean_before = sum(e.before for e in events) / n if n else 0.0
    mean_after = sum(e.after for e in events) / n if n else 0.0
    mean_delta = mean_after - mean_before
    improved_rate = (sum(1 for e in events if e.improved) / n) if n else 0.0

    return {
        "n_events": n,
        "mean_before": mean_before,
        "mean_after": mean_after,
        "mean_delta": mean_delta,
        "improved_rate": improved_rate,
        "events": [asdict(e) for e in events],
    }
