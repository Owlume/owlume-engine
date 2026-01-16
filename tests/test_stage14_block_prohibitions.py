import json
from pathlib import Path

import jsonschema

from src.governance.block_prohibitions import (
    BlockProhibitionsPolicy,
    check_block_prohibitions,
)


def _repo_root() -> Path:
    # /tests/test_stage14_block_prohibitions.py -> repo root is one level up
    return Path(__file__).resolve().parents[1]


def _load(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_negative_rules_validate_against_schema():
    root = _repo_root()
    rules_path = root / "data" / "policy" / "stage14_block_negative_rules.v1.json"
    schema_path = root / "schemas" / "block_negative_rules.schema.json"

    rules = _load(rules_path)
    schema = _load(schema_path)

    jsonschema.validate(instance=rules, schema=schema)


def test_missing_core_context_is_conservatively_prohibited():
    # With no context, HARD/HIGH/COMPROMISED requirements cannot be satisfied -> prohibited.
    violations = check_block_prohibitions({})
    assert len(violations) >= 1


def test_moral_political_flags_prohibit_block():
    ctx = {
        "constraint_status": "HARD",
        "harm_profile": "HIGH",
        "judgment_integrity": "COMPROMISED",
        "flags": {"moral_disagreement": True},
        "bias_evidence": {"failed_interventions": ["REFLECT", "WARN"]},
        "justification": {"why_block_is_necessary": "x", "why_lower_measures_failed": "y"},
        "unblock_conditions": {"required_actions": ["x"], "reassessment_triggers": ["new evidence"]},
    }
    violations = check_block_prohibitions(ctx)
    assert any(v.rule_id == "NEG-007" for v in violations)


def test_analysis_only_mode_prohibits_block():
    ctx = {
        "constraint_status": "HARD",
        "harm_profile": "HIGH",
        "judgment_integrity": "COMPROMISED",
        "mode": "ANALYSIS_ONLY",
        "bias_evidence": {"failed_interventions": ["REFLECT", "WARN"]},
        "justification": {"why_block_is_necessary": "x", "why_lower_measures_failed": "y"},
        "unblock_conditions": {"required_actions": ["x"], "reassessment_triggers": ["new evidence"]},
        "flags": {},
    }
    violations = check_block_prohibitions(ctx)
    assert any(v.rule_id == "NEG-008" for v in violations)


def test_legitimate_block_context_has_no_prohibition_violations():
    """
    A context that satisfies HARD/HIGH/COMPROMISED and includes required
    justification + unblock + prior interventions should not be prohibited,
    assuming no moral/political flags and not analysis-only mode.
    """
    ctx = {
        "constraint_status": "HARD",
        "harm_profile": "HIGH",
        "judgment_integrity": "COMPROMISED",
        "bias_evidence": {"failed_interventions": ["REFLECT", "WARN", "SLOW"]},
        "justification": {"why_block_is_necessary": "x", "why_lower_measures_failed": "y"},
        "unblock_conditions": {"required_actions": ["x"], "reassessment_triggers": ["new evidence"]},
        "flags": {"moral_disagreement": False, "political_disagreement": False, "ideological_disagreement": False},
        "mode": "EXECUTION",
    }
    violations = check_block_prohibitions(ctx)
    assert violations == []
