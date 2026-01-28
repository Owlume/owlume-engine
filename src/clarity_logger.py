# src/clarity_logger.py
from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict

from jsonschema import Draft7Validator

from judgment_landing import (
    JudgmentLandingError,
    build_judgment_terminal_state,
    enforce_judgment_landing_on_termination,
)


def _read_json(path: str) -> Any:
    # Accept UTF-8 BOM safely (Windows)
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_schema(schema_path: str) -> Dict[str, Any]:
    return _read_json(schema_path)


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> None:
    v = Draft7Validator(schema)
    errors = sorted(v.iter_errors(record), key=lambda e: e.path)
    if errors:
        msgs = "\n".join(
            [f"- {'/'.join([str(p) for p in e.path]) or '(root)'} → {e.message}" for e in errors]
        )
        raise ValueError(f"Record failed schema validation:\n{msgs}")


def make_session_id(prefix: str = "DLM") -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{ts}"


def log_record(record: Dict[str, Any], logs_dir: str = "data/logs") -> str:
    _ensure_dir(logs_dir)
    month = datetime.datetime.now().strftime("%Y%m")
    path = os.path.join(logs_dir, f"clarity_gain_{month}.jsonl")

    # --- termination gate ---
    j = record.get("judgment_landing")
    if not isinstance(j, dict):
        raise JudgmentLandingError("Missing judgment_landing; cannot log as complete.")

    jts = build_judgment_terminal_state(
        jtype=j.get("type"),
        statement=j.get("statement"),
        confidence=j.get("confidence"),
        acknowledged=(j.get("acknowledged") is True),
    )

    enforce_judgment_landing_on_termination(jts)
    record.setdefault("detected", {})["judgment_terminal_state"] = jts.__dict__

    # NEVER allow root-level judgment_terminal_state
    if "judgment_terminal_state" in record:
        record.pop("judgment_terminal_state", None)

    # REGRESSION GUARD
    assert "judgment_terminal_state" not in record, (
        "BUG: root judgment_terminal_state detected; schema forbids this"
    )

    with open(path, "a", encoding="utf-8-sig") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return path
