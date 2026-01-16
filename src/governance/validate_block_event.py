"""
Stage 14 — BLOCK Event Validation

Validates BLOCK event objects against the schema AND enforces non-tunable invariants
as executable checks (fail closed).

Schema:
  /schemas/constraint_block_event.schema.json
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import json

import jsonschema


class BlockEventValidationError(ValueError):
    pass


def _repo_root() -> Path:
    # /src/governance/validate_block_event.py -> repo root is two levels up
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_block_event(event: Dict[str, Any], schema_path: Path | None = None) -> None:
    """
    Validate the event with JSON Schema + Stage14 invariants.
    Raises BlockEventValidationError on any failure.
    """
    root = _repo_root()
    sp = schema_path or (root / "schemas" / "constraint_block_event.schema.json")

    schema = _load_json(sp)

    try:
        jsonschema.validate(instance=event, schema=schema)
    except jsonschema.ValidationError as e:
        raise BlockEventValidationError(f"BLOCK event schema validation failed: {e.message}") from e

    # ---- Stage 14 non-tunable invariants (fail closed) ----
    # 1) Must be a BLOCK-triggered event type (schema may allow, but we enforce contract).
    et = event.get("event_type")
    if et != "BLOCK_TRIGGERED":
        raise BlockEventValidationError(f"BLOCK requires event_type='BLOCK_TRIGGERED'; got {et!r}")

    # 2) system_state.harm must be IRREVERSIBLE
    harm = (event.get("system_state") or {}).get("harm")
    if harm != "IRREVERSIBLE":
        raise BlockEventValidationError(f"BLOCK requires system_state.harm='IRREVERSIBLE'; got {harm!r}")

    # 3) constraint.certainty must be HIGH
    certainty = (event.get("constraint") or {}).get("certainty")
    if certainty != "HIGH":
        raise BlockEventValidationError(f"BLOCK requires constraint.certainty='HIGH'; got {certainty!r}")

    # 4) failed_interventions must include REFLECT and WARN
    fi = (event.get("bias_evidence") or {}).get("failed_interventions")
    if not isinstance(fi, list):
        raise BlockEventValidationError("BLOCK requires bias_evidence.failed_interventions as a list.")
    if "REFLECT" not in fi:
        raise BlockEventValidationError(f"BLOCK requires failed_interventions include REFLECT; got {fi!r}")
    if "WARN" not in fi:
        raise BlockEventValidationError(f"BLOCK requires failed_interventions include WARN; got {fi!r}")
