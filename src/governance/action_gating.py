"""
Stage 14 — Action Gating (Canonical, Non-Tunable)

This module is the single source of truth for selecting a governance action
(ADVISORY / REFLECT / WARN / SLOW / REQUIRE_ACK / BLOCK) given:

- constraint_status: NONE | SOFT | HARD
- harm_profile: LOW | MEDIUM | HIGH
- judgment_integrity: INTACT | DEGRADED | COMPROMISED

Policy is loaded from:
  /data/policy/stage14_action_gating_table.v1.json

Invariants:
- Exactly 27 rows (3x3x3)
- Exactly one BLOCK row
- BLOCK row must be (HARD, HIGH, COMPROMISED)

If invariants fail, this module fails closed (raises).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Literal, Tuple, Any
import json

import jsonschema


ConstraintStatus = Literal["NONE", "SOFT", "HARD"]
HarmProfile = Literal["LOW", "MEDIUM", "HIGH"]
JudgmentIntegrity = Literal["INTACT", "DEGRADED", "COMPROMISED"]
Action = Literal["ADVISORY", "REFLECT", "WARN", "SLOW", "REQUIRE_ACK", "BLOCK"]


@dataclass(frozen=True)
class GatingDecision:
    constraint_status: ConstraintStatus
    harm_profile: HarmProfile
    judgment_integrity: JudgmentIntegrity
    action: Action
    policy_version: str


def _repo_root() -> Path:
    # Repo layout assumption: /src/governance/action_gating.py
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _validate_policy(policy: Dict[str, Any], schema: Dict[str, Any]) -> None:
    jsonschema.validate(instance=policy, schema=schema)


def _enforce_invariants(policy: Dict[str, Any]) -> None:
    rows = policy["rows"]

    # 1) Ensure full state-space coverage with uniqueness.
    if len(rows) != 27:
        raise ValueError(f"Action gating table must have exactly 27 rows; got {len(rows)}.")

    keys = set()
    for r in rows:
        k = (r["constraint_status"], r["harm_profile"], r["judgment_integrity"])
        if k in keys:
            raise ValueError(f"Duplicate row key detected: {k}")
        keys.add(k)

    expected = {(cs, hp, ji)
                for cs in ("NONE", "SOFT", "HARD")
                for hp in ("LOW", "MEDIUM", "HIGH")
                for ji in ("INTACT", "DEGRADED", "COMPROMISED")}
    missing = expected - keys
    extra = keys - expected
    if missing:
        raise ValueError(f"Missing row keys in action gating table: {sorted(missing)}")
    if extra:
        raise ValueError(f"Unexpected row keys in action gating table: {sorted(extra)}")

    # 2) Enforce exactly one BLOCK row and its position.
    block_rows = [r for r in rows if r["action"] == "BLOCK"]
    if len(block_rows) != 1:
        raise ValueError(f"Action gating table must contain exactly one BLOCK row; got {len(block_rows)}.")

    br = block_rows[0]
    required = ("HARD", "HIGH", "COMPROMISED")
    got = (br["constraint_status"], br["harm_profile"], br["judgment_integrity"])
    if got != required:
        raise ValueError(f"BLOCK row must be {required}; got {got}.")


class ActionGatingPolicy:
    """
    Loads and serves the canonical Stage 14 action gating table.
    Fail-closed if schema or invariants are violated.
    """

    def __init__(self, policy_path: Path | None = None, schema_path: Path | None = None) -> None:
        root = _repo_root()
        self._policy_path = policy_path or root / "data" / "policy" / "stage14_action_gating_table.v1.json"
        self._schema_path = schema_path or root / "schemas" / "action_gating_table.schema.json"

        policy = _load_json(self._policy_path)
        schema = _load_json(self._schema_path)

        _validate_policy(policy, schema)
        _enforce_invariants(policy)

        self._policy = policy
        self._index: Dict[Tuple[ConstraintStatus, HarmProfile, JudgmentIntegrity], Action] = {}

        for r in policy["rows"]:
            k = (r["constraint_status"], r["harm_profile"], r["judgment_integrity"])
            self._index[k] = r["action"]

    @property
    def version(self) -> str:
        return str(self._policy["spec"]["version"])

    @property
    def non_tunable(self) -> bool:
        return bool(self._policy["spec"]["non_tunable"])

    def decide_action(
        self,
        constraint_status: ConstraintStatus,
        harm_profile: HarmProfile,
        judgment_integrity: JudgmentIntegrity,
    ) -> GatingDecision:
        k = (constraint_status, harm_profile, judgment_integrity)
        if k not in self._index:
            # Should never happen if invariants are intact, but fail closed.
            raise KeyError(f"No action mapping for key: {k}")

        action: Action = self._index[k]  # type: ignore[assignment]
        return GatingDecision(
            constraint_status=constraint_status,
            harm_profile=harm_profile,
            judgment_integrity=judgment_integrity,
            action=action,
            policy_version=self.version,
        )


# Convenience singleton (common pattern in Owlume engine modules).
_DEFAULT_POLICY: ActionGatingPolicy | None = None


def decide_action(
    constraint_status: ConstraintStatus,
    harm_profile: HarmProfile,
    judgment_integrity: JudgmentIntegrity,
) -> GatingDecision:
    """
    Functional façade over the canonical policy.
    """
    global _DEFAULT_POLICY
    if _DEFAULT_POLICY is None:
        _DEFAULT_POLICY = ActionGatingPolicy()
    return _DEFAULT_POLICY.decide_action(constraint_status, harm_profile, judgment_integrity)
