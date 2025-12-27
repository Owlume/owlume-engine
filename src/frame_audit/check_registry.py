from __future__ import annotations

from .types import CheckSpec

TRACE_SPEC: dict[str, str] = {
    "name": "frame_audit_trace",
    "version": "1.0",
    "scale": "0-1",
}

# These IDs must match your golden samples/tests.
CHECK_SPECS: list[CheckSpec] = [
    CheckSpec(
        check_id="FA-001",
        name="False dichotomy",
        description="Forces a binary choice where additional options or sequencing may exist.",
        weight=0.12,
        severity="high",
        enabled=True,
    ),
    CheckSpec(
        check_id="FA-002",
        name="Undefined success criteria",
        description="No measurable success metric / acceptance test.",
        weight=0.10,
        severity="high",
        enabled=True,
    ),
    CheckSpec(
        check_id="FA-003",
        name="Missing stakeholders",
        description="Key stakeholders/owners/impacted groups are absent.",
        weight=0.08,
        severity="medium",
        enabled=True,
    ),
    CheckSpec(
        check_id="FA-004",
        name="Scope creep / boundary blur",
        description="Many deliverables or add-ons without boundaries.",
        weight=0.08,
        severity="medium",
        enabled=True,
    ),
    CheckSpec(
        check_id="FA-005",
        name="Timeframe ambiguous",
        description="Uses urgency language (soon/ASAP) without a concrete timeframe.",
        weight=0.06,
        severity="medium",
        enabled=True,
    ),
    CheckSpec(
        check_id="FA-006",
        name="Constraint conflict",
        description="Conflicting constraints (e.g., perfect + ASAP + no budget).",
        weight=0.08,
        severity="high",
        enabled=True,
    ),
]

CHECK_ORDER: list[str] = [c.check_id for c in CHECK_SPECS]


