"""
Stage 14 — BLOCK Event Validation (Canonical)

This module provides a single enforcement function to validate a BLOCK event
against the Stage 14 schema contract.

Fail-closed: raises on any violation.

Schema:
  /schemas/constraint_block_event.schema.json
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json

import jsonschema


def _repo_root() -> Path:
    # /src/governance/validate_block_event.py -> repo root is two levels up
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class BlockEventValidationError(ValueError):
    pass


def validate_block_event(event: Dict[str, Any], schema_path: Path | None = None) -> None:
    """
    Validate a BLOCK event payload.

    Raises:
      BlockEventValidationError on any schema violation.
    """
    root = _repo_root()
    schema_file = schema_path or (root / "schemas" / "constraint_block_event.schema.json")

    schema = _load_json(schema_file)

    try:
        jsonschema.validate(instance=event, schema=schema)
    except jsonschema.ValidationError as e:
        raise BlockEventValidationError(str(e)) from e
