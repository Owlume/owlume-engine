import json
from pathlib import Path

from src.governance.policy_fingerprint import compute_action_gating_table_hash


def _repo_root() -> Path:
    # /tests/test_stage14_policy_fingerprint.py -> repo root is one level up
    return Path(__file__).resolve().parents[1]


def _load(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_golden_block_event_policy_hash_matches_action_gating_table():
    root = _repo_root()

    # Load golden BLOCK event
    block_event_path = root / "data" / "golden" / "stage14_valid_block_event.json"
    block_event = _load(block_event_path)

    recorded_hash = block_event["audit"]["decision_table_hash"]

    # Compute current canonical hash
    computed_hash = compute_action_gating_table_hash()

    assert (
        recorded_hash == computed_hash
    ), (
        "Golden BLOCK event policy hash does not match current "
        "stage14_action_gating_table.v1.json. "
        "This indicates a governance drift and must be reviewed explicitly."
    )
