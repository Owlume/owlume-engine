"""
Stage 14 — BLOCK Prohibitions (Negative Charter Enforcement)

Machine-checkable negative charter rules that MUST prohibit BLOCK when violated.

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


class BlockProhibitionsError(ValueError):
    pass


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


class BlockProhibitionsPolicy:
    """
    Loads and serves the canonical Stage 14 negative rules pack.
    The pack is treated as policy law: non_tunable must be true.
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

        spec = rules.get("spec", {})
        if spec.get("non_tunable") is not True:
            raise BlockProhibitionsError("Negative rules must be non_tunable=true.")

        # The policy file stores "prohibitions" as a list of {code, description}.
        # We keep them for auditability, but enforcement is code-based below.
        self._prohibitions = rules.get("prohibitions", [])

    def check(self, ctx: Dict[str, Any]) -> List[ProhibitionViolation]:
        """
        Evaluate prohibitions. Any returned violation prohibits BLOCK.
        Missing context is treated as prohibited where relevant.
        """
        violations: List[ProhibitionViolation] = []

        # ---------------------------------------------------------------------
        # 0) Conservative core-context requirement (fail closed)
        # ---------------------------------------------------------------------
        # If you cannot even establish the HARD/HIGH/COMPROMISED gate context,
        # BLOCK must be prohibited.
        core_keys = ("constraint_status", "harm_profile", "judgment_integrity")
        if any(k not in ctx for k in core_keys):
            violations.append(
                ProhibitionViolation(
                    rule_id="MISSING_CORE_CONTEXT",
                    severity="HARD",
                    description="BLOCK prohibited: missing core context (constraint_status/harm_profile/judgment_integrity).",
                )
            )
            return violations  # fail-closed early

        # ---------------------------------------------------------------------
        # 1) Negative charter: moral/political/ideological disagreement flags
        # ---------------------------------------------------------------------
        flags = ctx.get("flags", {})
        if isinstance(flags, dict):
            if any(
                bool(flags.get(k))
                for k in ("moral_disagreement", "political_disagreement", "ideological_disagreement")
            ):
                violations.append(
                    ProhibitionViolation(
                        rule_id="NEG-007",
                        severity="HARD",
                        description="BLOCK prohibited when moral/political/ideological disagreement is present.",
                    )
                )

        # ---------------------------------------------------------------------
        # 2) Negative charter: analysis-only contexts must never BLOCK
        # ---------------------------------------------------------------------
        # The tests use mode="ANALYSIS_ONLY".
        if ctx.get("mode") == "ANALYSIS_ONLY":
            violations.append(
                ProhibitionViolation(
                    rule_id="NEG-008",
                    severity="HARD",
                    description="BLOCK prohibited in ANALYSIS_ONLY mode.",
                )
            )

        # ---------------------------------------------------------------------
        # 3) Missing required narrative justification / unblock conditions
        # ---------------------------------------------------------------------
        # Even when core gate context is present, BLOCK requires justification and unblock.
        required_paths = [
            "justification.why_block_is_necessary",
            "justification.why_lower_measures_failed",
            "unblock_conditions.required_actions",
            "unblock_conditions.reassessment_triggers",
        ]
        for dotted in required_paths:
            got = _get_path(ctx, dotted)
            if got is None:
                violations.append(
                    ProhibitionViolation(
                        rule_id="MISSING_REQUIRED_CONTEXT",
                        severity="HARD",
                        description=f"BLOCK prohibited: missing required field {dotted}.",
                    )
                )
                break
            if isinstance(got, str) and got.strip() == "":
                violations.append(
                    ProhibitionViolation(
                        rule_id="MISSING_REQUIRED_CONTEXT",
                        severity="HARD",
                        description=f"BLOCK prohibited: empty required field {dotted}.",
                    )
                )
                break
            if isinstance(got, list) and len(got) == 0:
                violations.append(
                    ProhibitionViolation(
                        rule_id="MISSING_REQUIRED_CONTEXT",
                        severity="HARD",
                        description=f"BLOCK prohibited: empty required list {dotted}.",
                    )
                )
                break

        # ---------------------------------------------------------------------
        # 4) Failed interventions must include REFLECT and WARN (and generally show escalation)
        # ---------------------------------------------------------------------
        fi = _get_path(ctx, "bias_evidence.failed_interventions")
        if fi is None:
            fi = ctx.get("failed_interventions")

        if not isinstance(fi, list):
            violations.append(
                ProhibitionViolation(
                    rule_id="MISSING_FAILED_INTERVENTIONS",
                    severity="HARD",
                    description="BLOCK prohibited: failed_interventions missing or not a list.",
                )
            )
        else:
            present = {x for x in fi if isinstance(x, str)}
            if "REFLECT" not in present or "WARN" not in present:
                violations.append(
                    ProhibitionViolation(
                        rule_id="INSUFFICIENT_PRIOR_INTERVENTIONS",
                        severity="HARD",
                        description="BLOCK prohibited: failed_interventions must include REFLECT and WARN.",
                    )
                )

        # ---------------------------------------------------------------------
        # 5) Explicit “non-configurable” prohibition (policy law)
        # ---------------------------------------------------------------------
        # This is defensive: if a caller tries to pass tuning knobs, that violates charter.
        if any(k in ctx for k in ("block_threshold", "override_block", "allow_block_override", "tune_block")):
            violations.append(
                ProhibitionViolation(
                    rule_id="NO_CONFIG_KNOBS",
                    severity="HARD",
                    description="BLOCK prohibited: no thresholds, config knobs, or overrides permitted for BLOCK.",
                )
            )

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
