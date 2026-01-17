import json
from pathlib import Path

import jsonschema

from src.governance.validate_block_event import validate_block_event, BlockEventValidationError


def _repo_root() -> Path:
    # /tests/test_stage14_block_schema.py -> repo root is one level up
    return Path(__file__).resolve().parents[1]


def _load(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_golden_block_event_validates():
    root = _repo_root()
    ev_path = root / "data" / "golden" / "stage14_valid_block_event.json"
    event = _load(ev_path)

    # Validate via runtime helper (preferred).
    validate_block_event(event)


def test_block_event_rejects_wrong_system_state():
    root = _repo_root()
    ev_path = root / "data" / "golden" / "stage14_valid_block_event.json"
    event = _load(ev_path)

    event2 = dict(event)
    event2["system_state"] = dict(event["system_state"])
    event2["system_state"]["harm"] = "REVERSIBLE"  # illegal

    try:
        validate_block_event(event2)
        assert False, "Expected validation failure for wrong system_state."
    except BlockEventValidationError:
        assert True


def test_block_event_requires_unblock_conditions():
    root = _repo_root()
    ev_path = root / "data" / "golden" / "stage14_valid_block_event.json"
    event = _load(ev_path)

    event2 = dict(event)
    event2.pop("unblock_conditions", None)

    try:
        validate_block_event(event2)
        assert False, "Expected validation failure when unblock_conditions missing."
    except BlockEventValidationError:
        assert True


def test_block_event_requires_reflect_and_warn_in_failed_interventions():
    root = _repo_root()
    ev_path = root / "data" / "golden" / "stage14_valid_block_event.json"
    event = _load(ev_path)

    event2 = dict(event)
    event2["bias_evidence"] = dict(event["bias_evidence"])
    event2["bias_evidence"]["failed_interventions"] = ["SLOW", "REQUIRE_ACK"]  # missing REFLECT and WARN

    try:
        validate_block_event(event2)
        assert False, "Expected validation failure when REFLECT/WARN not present."
    except BlockEventValidationError:
        assert True


def test_block_event_rejects_non_high_constraint_certainty():
    root = _repo_root()
    ev_path = root / "data" / "golden" / "stage14_valid_block_event.json"
    event = _load(ev_path)

    event2 = dict(event)
    event2["constraint"] = dict(event["constraint"])
    event2["constraint"]["certainty"] = "MEDIUM"  # illegal, must be HIGH

    try:
        validate_block_event(event2)
        assert False, "Expected validation failure for non-HIGH constraint certainty."
    except BlockEventValidationError:
        assert True
