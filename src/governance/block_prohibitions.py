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


def _norm_rule_id(rule: Dict[str, Any]) -> str:
    return str(rule.get("id") or rule.get("code") or "UNKNOWN_RULE")


def _norm_desc(rule: Dict[str, Any]) -> str:
    return str(rule.get("description") or rule.get("rule") or "")


def _norm_sev(rule: Dict[str, Any]) -> str:
    # Default severity is HIGH for fail-closed prohibitions.
    sev = rule.get("severity")
    return str(sev) if sev is not None else "HIGH"


class BlockProhibitionsPolicy:
    """
    Loads and serves the canonical Stage 14 negative rules.

    Supports two policy shapes:
      - legacy: {"rules": [...]}
      - schema-aligned: {"prohibitions": [...]}

    Each item can be:
      A) full rule object with "when" triggers:
         {id, severity, description, when:{...}}

      B) minimal prohibition item (schema-aligned list style):
         {code, description}
         -> treated as unconditional prohibition (always violated).
         This is intentionally fail-closed.
    """

    def __init__(self, rules_path: Path | None = None, schema_path: Path | None = None) -> None:
        root = _repo_root()
        self._rules_path = rules_path or (root / "data" / "policy" / "stage14_block_negative_rules.v1.json")
        self._schema_path = schema_path or (root / "schemas" / "block_negative_rules.schema.json")

        rules_doc = _load_json(self._rules_path)
        schema = _load_json(self._schema_path)

        try:
            jsonschema.validate(instance=rules_doc, schema=schema)
        except jsonschema.ValidationError as e:
            raise BlockProhibitionsError(f"Negative rules schema validation failed: {e}") from e

        # Hard requirement: negative rules are policy-law (non-tunable).
        if rules_doc.get("spec", {}).get("non_tunable") is not True:
            raise BlockProhibitionsError("Negative rules must be non_tunable=true.")

        # Accept both keys; canonical is "prohibitions" (new), but allow "rules" (legacy).
        items = rules_doc.get("prohibitions")
        if items is None:
            items = rules_doc.get("rules")

        if items is None:
            raise BlockProhibitionsError("Negative rules must include 'prohibitions' (or legacy 'rules').")

        if not isinstance(items, list):
            raise BlockProhibitionsError("Negative rules list must be an array.")

        self._items: List[Dict[str, Any]] = items

    def check(self, ctx: Dict[str, Any]) -> List[ProhibitionViolation]:
        """
        Evaluate prohibitions. Any returned violation prohibits BLOCK.
        Missing context is treated as prohibited where relevant.
        """
        violations: List[ProhibitionViolation] = []

        for rule in self._items:
            if not isinstance(rule, dict):
                # Unknown entry -> fail closed.
                raise BlockProhibitionsError("Invalid prohibition entry; expected object.")

            rule_id = _norm_rule_id(rule)
            severity = _norm_sev(rule)
            desc = _norm_desc(rule)

            when = rule.get("when")

            # If no "when" is present, treat as an unconditional prohibition.
            # This allows schema-aligned minimal items {code, description}.
            if when is None:
                violations.append(ProhibitionViolation(rule_id, severity, desc))
                continue

            if not isinstance(when, dict) or len(when) != 1:
                raise BlockProhibitionsError(f"Invalid 'when' for rule {rule_id}; expected single-key object.")

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
                if not isinstance(val, list):
                    raise BlockProhibitionsError(f"Rule {rule_id} missing_any must be a list.")
                missing = False
                for dotted in val:
                    if not isinstance(dotted, str):
                        raise BlockProhibitionsError(f"Rule {rule_id} missing_any paths must be strings.")
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
                if not isinstance(val, list):
                    raise BlockProhibitionsError(f"Rule {rule_id} failed_interventions_missing_any must be a list.")
                fi = _get_path(ctx, "bias_evidence.failed_interventions")
                if fi is None:
                    fi = ctx.get("failed_interventions")
                if not isinstance(fi, list):
                    violations.append(ProhibitionViolation(rule_id, severity, desc))
                else:
                    needed = {x for x in val if isinstance(x, str)}
                    present = {x for x in fi if isinstance(x, str)}
                    if not needed.issubset(present):
                        violations.append(ProhibitionViolation(rule_id, severity, desc))

            elif key == "flags_any_true":
                # If flags missing -> treat as false (do not prohibit).
                if not isinstance(val, list):
                    raise BlockProhibitionsError(f"Rule {rule_id} flags_any_true must be a list.")
                flags = ctx.get("flags", {})
                if not isinstance(flags, dict):
                    continue
                if any(bool(flags.get(name)) is True for name in val if isinstance(name, str)):
                    violations.append(ProhibitionViolation(rule_id, severity, desc))

            elif key == "mode_any":
                # If mode missing, do not prohibit; only prohibit if explicitly in these modes.
                if not isinstance(val, list):
                    raise BlockProhibitionsError(f"Rule {rule_id} mode_any must be a list.")
                mode = ctx.get("mode")
                if isinstance(mode, str) and mode in val:
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
