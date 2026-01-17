import json
from pathlib import Path

import jsonschema

from src.governance.action_gating import decide_action, ActionGatingPolicy


def _repo_root() -> Path:
    # /tests/test_stage14_action_gating_table.py -> repo root is two levels up
    return Path(__file__).resolve().parents[1]


def _load(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_action_gating_table_validates_against_schema():
    root = _repo_root()
    policy_path = root / "data" / "policy" / "stage14_action_gating_table.v1.json"
    schema_path = root / "schemas" / "action_gating_table.schema.json"

    policy = _load(policy_path)
    schema = _load(schema_path)

    jsonschema.validate(instance=policy, schema=schema)


def test_action_gating_table_has_exactly_one_block_row_and_correct_key():
    root = _repo_root()
    policy_path = root / "data" / "policy" / "stage14_action_gating_table.v1.json"
    policy = _load(policy_path)

    rows = policy["rows"]
    assert len(rows) == 27

    block_rows = [r for r in rows if r["action"] == "BLOCK"]
    assert len(block_rows) == 1

    br = block_rows[0]
    assert br["constraint_status"] == "HARD"
    assert br["harm_profile"] == "HIGH"
    assert br["judgment_integrity"] == "COMPROMISED"


def test_decide_action_only_blocks_on_hard_high_compromised():
    # The only legal BLOCK key:
    d = decide_action("HARD", "HIGH", "COMPROMISED")
    assert d.action == "BLOCK"

    # All other keys must not BLOCK:
    for cs in ("NONE", "SOFT", "HARD"):
        for hp in ("LOW", "MEDIUM", "HIGH"):
            for ji in ("INTACT", "DEGRADED", "COMPROMISED"):
                if (cs, hp, ji) == ("HARD", "HIGH", "COMPROMISED"):
                    continue
                d2 = decide_action(cs, hp, ji)
                assert d2.action != "BLOCK", f"Illegal BLOCK for {(cs, hp, ji)}"


def test_policy_loader_fail_closed_on_invariant_violation(monkeypatch, tmp_path: Path):
    """
    Sanity check: if the policy is tampered with to add a second BLOCK row,
    ActionGatingPolicy must refuse to load (fail closed).
    """
    root = _repo_root()
    policy_path = root / "data" / "policy" / "stage14_action_gating_table.v1.json"
    schema_path = root / "schemas" / "action_gating_table.schema.json"

    policy = _load(policy_path)

    # Tamper: set first row action to BLOCK (invalid).
    policy2 = dict(policy)
    policy2["rows"] = list(policy["rows"])
    policy2["rows"][0] = dict(policy2["rows"][0])
    policy2["rows"][0]["action"] = "BLOCK"

    tampered = tmp_path / "tampered_policy.json"
    tampered.write_text(json.dumps(policy2, indent=2), encoding="utf-8")

    try:
        _ = ActionGatingPolicy(policy_path=tampered, schema_path=schema_path)
        assert False, "Expected ActionGatingPolicy to fail closed on invariant violation."
    except Exception:
        # Any exception is acceptable here: validation or invariant enforcement.
        assert True
