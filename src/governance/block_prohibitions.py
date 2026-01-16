"""
Stage 14 — BLOCK Prohibitions (Negative Charter Enforcement)

This module enforces the Stage 14 Negative Charter as machine-checkable rules.

It evaluates a context payload and returns violations that prohibit BLOCK.
Fail-closed principles:
- If rules/schema cannot be loaded or validated -> raise (do not allow BLOCK)
- If required context is missing for a prohibition -> treat as prohibited (conservative)

Rules file:
  /data/policy/stage14_block_negative_rules.v1.json

Schema:
  /schemas/block_negative_rules.schema.json
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

import jsonschema


@dataclass(frozen=True)
class ProhibitionViolation:
    rule_id: str
    severity: str
    description: str


def _repo_root() -> Path:
    # /src/governance/block_prohibitions.py -> repo root is two levels up
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_path(obj: Dict[str, Any], dotted: str) -> Optional[Any]:
    """
    Safe dotted-path getter for dicts.
    Returns None if any part is missing.
    """
    cur: Any = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


class BlockProhibitionsError(ValueError):
    pass


class BlockProhibitionsPolicy:
    """
    Loads and serves the canonical Stage 14 negative rules.
    """

    def __init__(self, rules_path: Path | None = None, schema_path: Path | None = None) -> None:
        root = _repo_root()
        self._rules_path = rules_path or (root / "data" / "policy" / "stage14_block_negative_rules.v1.json")
        self._schema_path = schema_path or (root / "schemas" / "block_negative_rules.schema.json")

        rules = _load_json(self._rules_path)
        schema = _load_json(self._schema_path)

        try:
            jsonschema.validate(instance=rules, schema=schema)
        except jsonschema.ValidationError as e:
            raise BlockProhibitionsError(f"Negative rules schema validation failed: {e}") from e

        if rules["spec"].get("non_tunable") is not True:
            raise BlockProhibitionsError("Negative rules must be non_tunable=true.")

        self._rules = rules["rules"]

    def check(self, ctx: Dict[str, Any]) -> List[ProhibitionViolation]:
        """
        Evaluate prohibitions. Any returned violation prohibits BLOCK.
        Missing context is treated as prohibited where relevant.
        """
        violations: List[ProhibitionViolation] = []

        for rule in self._rules:
            rule_id = rule["id"]
            severity = rule["severity"]
            desc = rule["description"]
            when = rule["when"]

            # Each rule has exactly one key in `when`.
            key = next(iter(when.keys()))
            val = when[key]

            if key == "constraint_status_not":
                cs = ctx.get("constraint_status")
                if cs is None or cs != "HARD":
                    violations.append(ProhibitionViolation(rule_id, severity, desc))

            elif key == "harm_profile_not":
                hp = ctx.get("harm_profile")
                if hp is None or hp != "HIGH":
                    violations.append(ProhibitionViolation(rule_id, severity, desc))

            elif key == "judgment_integrity_not":
                ji = ctx.get("judgment_integrity")
                if ji is None or ji != "COMPROMISED":
                    violations.append(ProhibitionViolation(rule_id, severity, desc))

            elif key == "missing_any":
                # val is list of dotted paths; missing OR empty strings/empty arrays prohibit.
                missing = False
                for dotted in val:
                    got = _get_path(ctx, dotted)
                    if got is None:
                        missing = True
                        break
                    if isinstance(got, str) and got.strip() == "":
                        missing = True
                        break
                    if isinstance(got, list) and len(got) == 0:
                        missing = True
                        break
                if missing:
                    violations.append(ProhibitionViolation(rule_id, severity, desc))

            elif key == "failed_interventions_missing_any":
                # Look for ctx["bias_evidence"]["failed_interventions"] or ctx["failed_interventions"].
                fi = _get_path(ctx, "bias_evidence.failed_interventions")
                if fi is None:
                    fi = ctx.get("failed_interventions")
                if not isinstance(fi, list):
                    violations.append(ProhibitionViolation(rule_id, severity, desc))
                else:
                    needed = set(val)
                    present = set([x for x in fi if isinstance(x, str)])
                    if not needed.issubset(present):
                        violations.append(ProhibitionViolation(rule_id, severity, desc))

            elif key == "flags_any_true":
                flags = ctx.get("flags", {})
                if not isinstance(flags, dict):
                    # Missing flags is not automatically prohibited; treat as false.
                    continue
                if any(bool(flags.get(name)) is True for name in val):
                    violations.append(ProhibitionViolation(rule_id, severity, desc))

            elif key == "mode_any":
                mode = ctx.get("mode")
                # If mode missing, do not prohibit; only prohibit if explicitly in these modes.
                if mode in val:
                    violations.append(ProhibitionViolation(rule_id, severity, desc))

            else:
                # Unknown rule type -> fail closed.
                raise BlockProhibitionsError(f"Unknown negative rule trigger: {key}")

        return violations


_DEFAULT_POLICY: BlockProhibitionsPolicy | None = None


def check_block_prohibitions(ctx: Dict[str, Any]) -> List[ProhibitionViolation]:
    """
    Functional façade. Returns violations that prohibit BLOCK.
    """
    global _DEFAULT_POLICY
    if _DEFAULT_POLICY is None:
        _DEFAULT_POLICY = BlockProhibitionsPolicy()
    return _DEFAULT_POLICY.check(ctx)
