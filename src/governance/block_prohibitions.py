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
    sev = rule.get("severity")
    return str(sev) if sev is not None else "HIGH"


# ---- Code-based prohibitions (schema-aligned simple list) ----
# These are *runtime* negative rules: they prohibit BLOCK given ctx.
# Non-runtime meta rules must not generate violations (e.g. NO_CONFIG_KNOBS).
_RUNTIME_CODE_RULES = {
    # Prohibit BLOCK if any moral/political/ideological disagreement flags are true.
    "NO_BLOCK_ON_MORAL_OR_POLITICAL_DISAGREEMENT": "flags_any_true",
    # Prohibit BLOCK if system is in analysis-only mode.
    "NO_BLOCK_IN_ANALYSIS_ONLY_MODE": "mode_eq",
    # Prohibit BLOCK if output kind is QUESTIONS (BLOCK must never apply to QUESTIONS).
    "NO_BLOCK_ON_QUESTIONS": "output_kind_eq",
    # Prohibit BLOCK if output kind is REFRAME (if your policy uses this).
    "NO_BLOCK_ON_REFRAME": "output_kind_eq",
    # Prohibit BLOCK if output kind is ANALYSIS (if your policy uses this).
    "NO_BLOCK_ON_ANALYSIS": "output_kind_eq",
}

# Meta/charter-only statements: should NEVER create a runtime violation.
_META_ONLY_CODES = {
    "NO_CONFIG_KNOBS",
}


def _infer_output_kind(ctx: Dict[str, Any]) -> Optional[str]:
    """
    Best-effort output kind extractor.
    Supports multiple field names used across the codebase/tests.
    """
    for k in ("output_kind", "kind", "output_type_attempted"):
        v = ctx.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


class BlockProhibitionsPolicy:
    """
    Loads and serves the canonical Stage 14 negative rules.

    Supports two policy shapes:
      - legacy: {"rules": [...]}
      - schema-aligned: {"prohibitions": [...]}

    Each item can be:
      A) full rule object with "when" triggers:
         {id, severity, description, when:{...}}

      B) simple prohibition item:
         {code, description}
         -> evaluated by code-based logic (not unconditional).
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

        if rules_doc.get("spec", {}).get("non_tunable") is not True:
            raise BlockProhibitionsError("Negative rules must be non_tunable=true.")

        items = rules_doc.get("prohibitions")
        if items is None:
            items = rules_doc.get("rules")
        if items is None or not isinstance(items, list):
            raise BlockProhibitionsError("Negative rules must include 'prohibitions' (or legacy 'rules') list.")

        self._items: List[Dict[str, Any]] = items

    def check(self, ctx: Dict[str, Any]) -> List[ProhibitionViolation]:
        violations: List[ProhibitionViolation] = []
        # ---- Fail-closed: missing core context prohibits BLOCK ----
        # If we don't have the minimum state needed to even assess BLOCK legitimacy,
        # we must conservatively prohibit BLOCK.
        core_missing = []

        for k in ("constraint_status", "harm_profile", "judgment_integrity"):
            v = ctx.get(k)
            if not isinstance(v, str) or not v.strip():
                core_missing.append(k)

        # These are also required for legitimate BLOCK posture in Stage 14.
        fi = _get_path(ctx, "bias_evidence.failed_interventions")
        if not isinstance(fi, list) or len(fi) == 0:
            core_missing.append("bias_evidence.failed_interventions")

        jb = ctx.get("justification", {})
        if not isinstance(jb, dict) or not isinstance(jb.get("why_block_is_necessary"), str) or not jb.get("why_block_is_necessary", "").strip():
            core_missing.append("justification.why_block_is_necessary")
        if not isinstance(jb, dict) or not isinstance(jb.get("why_lower_measures_failed"), str) or not jb.get("why_lower_measures_failed", "").strip():
            core_missing.append("justification.why_lower_measures_failed")

        ub = ctx.get("unblock_conditions", {})
        if not isinstance(ub, dict) or not isinstance(ub.get("required_actions"), list) or len(ub.get("required_actions", [])) == 0:
            core_missing.append("unblock_conditions.required_actions")
        if not isinstance(ub, dict) or not isinstance(ub.get("reassessment_triggers"), list) or len(ub.get("reassessment_triggers", [])) == 0:
            core_missing.append("unblock_conditions.reassessment_triggers")

        if core_missing:
            violations.append(
                ProhibitionViolation(
                    rule_id="MISSING_CORE_CONTEXT",
                    severity="HIGH",
                    description="Missing core BLOCK context (fail-closed): " + ", ".join(core_missing),
                )
            )


        for rule in self._items:
            if not isinstance(rule, dict):
                raise BlockProhibitionsError("Invalid prohibition entry; expected object.")

            rule_id = _norm_rule_id(rule)
            severity = _norm_sev(rule)
            desc = _norm_desc(rule)

            # If "when" exists -> evaluate legacy trigger rules.
            when = rule.get("when")
            if when is not None:
                if not isinstance(when, dict) or len(when) != 1:
                    raise BlockProhibitionsError(f"Invalid 'when' for rule {rule_id}; expected single-key object.")

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
                    if not isinstance(val, list):
                        raise BlockProhibitionsError(f"Rule {rule_id} flags_any_true must be a list.")
                    flags = ctx.get("flags", {})
                    if not isinstance(flags, dict):
                        continue
                    if any(bool(flags.get(name)) is True for name in val if isinstance(name, str)):
                        violations.append(ProhibitionViolation(rule_id, severity, desc))

                elif key == "mode_any":
                    if not isinstance(val, list):
                        raise BlockProhibitionsError(f"Rule {rule_id} mode_any must be a list.")
                    mode = ctx.get("mode")
                    if isinstance(mode, str) and mode in val:
                        violations.append(ProhibitionViolation(rule_id, severity, desc))

                else:
                    raise BlockProhibitionsError(f"Unknown negative rule trigger: {key}")

                continue  # done with legacy-trigger rule

            # Otherwise: schema-aligned "code/description" item -> evaluate by code.
            code = rule.get("code")
            if not isinstance(code, str) or not code.strip():
                # No code, no when -> fail closed.
                raise BlockProhibitionsError(f"Prohibition missing 'code' and 'when': {rule!r}")

            code = code.strip()

            # Meta-only charter statements do not create runtime violations.
            if code in _META_ONLY_CODES:
                continue

            # Known runtime code rules.
            if code == "NO_BLOCK_ON_MORAL_OR_POLITICAL_DISAGREEMENT":
                flags = ctx.get("flags", {})
                if not isinstance(flags, dict):
                    # Missing flags -> treat as false (do not prohibit)
                    continue
                if any(bool(flags.get(k)) is True for k in ("moral_disagreement", "political_disagreement", "ideological_disagreement")):
                    violations.append(ProhibitionViolation(code, severity, desc))
                continue

            if code == "NO_BLOCK_IN_ANALYSIS_ONLY_MODE":
                mode = ctx.get("mode")
                if isinstance(mode, str) and mode.strip().upper() == "ANALYSIS_ONLY":
                    violations.append(ProhibitionViolation(code, severity, desc))
                continue

            if code in ("NO_BLOCK_ON_QUESTIONS", "NO_BLOCK_ON_REFRAME", "NO_BLOCK_ON_ANALYSIS"):
                out_kind = _infer_output_kind(ctx)
                if out_kind is None:
                    # If we cannot determine output kind, do not prohibit on this basis.
                    continue
                if code == "NO_BLOCK_ON_QUESTIONS" and out_kind.upper() == "QUESTIONS":
                    violations.append(ProhibitionViolation(code, severity, desc))
                elif code == "NO_BLOCK_ON_REFRAME" and out_kind.upper() == "REFRAME":
                    violations.append(ProhibitionViolation(code, severity, desc))
                elif code == "NO_BLOCK_ON_ANALYSIS" and out_kind.upper() == "ANALYSIS":
                    violations.append(ProhibitionViolation(code, severity, desc))
                continue

            # Unknown code -> fail closed (policy-law safety).
            raise BlockProhibitionsError(f"Unknown prohibition code: {code}")

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
