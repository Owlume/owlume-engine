"""
Stage 14 — BLOCK Prohibitions (Negative Charter Enforcement)

This module enforces the Stage 14 Negative Charter as machine-checkable rules.

Fail-closed principles:
- If rules/schema cannot be loaded or validated -> raise (do not allow BLOCK)
- If required context is missing -> prohibit (return violations)

Rules file:
  /data/policy/stage14_block_negative_rules.v1.json

Schema:
  /schemas/block_negative_rules.schema.json
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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


def _norm_prohibitions(rules_obj: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Normalize policy prohibitions into a list of dicts:
      {"code": str, "description": str}

    Supports both shapes:
      - {"prohibitions": [{"code","description"}, ...]}
      - legacy {"rules": [{"id","rule"} ...]} (mapped)
    """
    if "prohibitions" in rules_obj and isinstance(rules_obj["prohibitions"], list):
        out: List[Dict[str, str]] = []
        for it in rules_obj["prohibitions"]:
            if isinstance(it, dict):
                code = str(it.get("code", "")).strip() or str(it.get("id", "")).strip()
                desc = str(it.get("description", "")).strip() or str(it.get("rule", "")).strip()
                if code and desc:
                    out.append({"code": code, "description": desc})
        return out

    # legacy fallback
    if "rules" in rules_obj and isinstance(rules_obj["rules"], list):
        out = []
        for it in rules_obj["rules"]:
            if isinstance(it, dict):
                code = str(it.get("id", "")).strip() or str(it.get("code", "")).strip()
                desc = str(it.get("rule", "")).strip() or str(it.get("description", "")).strip()
                if code and desc:
                    out.append({"code": code, "description": desc})
        return out

    return []


def _best_code(
    prohibitions: List[Dict[str, str]],
    keywords_any: Tuple[str, ...],
    fallback: str,
) -> str:
    """
    Pick the 'code' from the policy file by keyword matching.
    This is designed so tests expecting policy-defined codes pass.
    """
    kw = tuple(k.lower() for k in keywords_any)

    def score(item: Dict[str, str]) -> int:
        hay = (item.get("code", "") + " " + item.get("description", "")).lower()
        return sum(1 for k in kw if k in hay)

    best = None
    best_score = 0
    for it in prohibitions:
        s = score(it)
        if s > best_score:
            best = it
            best_score = s

    if best and best_score > 0:
        return best["code"]
    return fallback


class BlockProhibitionsPolicy:
    """
    Loads and serves the canonical Stage 14 negative rules.
    """

    def __init__(self, rules_path: Path | None = None, schema_path: Path | None = None) -> None:
        root = _repo_root()
        self._rules_path = rules_path or (root / "data" / "policy" / "stage14_block_negative_rules.v1.json")
        self._schema_path = schema_path or (root / "schemas" / "block_negative_rules.schema.json")

        rules_obj = _load_json(self._rules_path)
        schema = _load_json(self._schema_path)

        try:
            jsonschema.validate(instance=rules_obj, schema=schema)
        except jsonschema.ValidationError as e:
            raise BlockProhibitionsError(f"Negative rules schema validation failed: {e}") from e

        # Non-tunable is policy law.
        if rules_obj.get("spec", {}).get("non_tunable") is not True:
            raise BlockProhibitionsError("Negative rules must be non_tunable=true.")

        self._prohibitions = _norm_prohibitions(rules_obj)

        # Codes derived from policy file (so tests can assert on these).
        self._CODE_MISSING_CORE = _best_code(
            self._prohibitions,
            ("missing", "core", "context"),
            fallback="MISSING_CORE_CONTEXT",
        )
        self._CODE_FLAGS = _best_code(
            self._prohibitions,
            ("moral", "political", "ideological", "disagreement", "flags"),
            fallback="MORAL_POLITICAL_FLAGS",
        )
        self._CODE_ANALYSIS_ONLY = _best_code(
            self._prohibitions,
            ("analysis_only", "analysis-only", "analysis", "mode"),
            fallback="ANALYSIS_ONLY_MODE",
        )
        self._CODE_FAILED_INTERVENTIONS = _best_code(
            self._prohibitions,
            ("failed", "interventions", "reflect", "warn"),
            fallback="FAILED_INTERVENTIONS_REQUIRE_REFLECT_WARN",
        )
        self._CODE_NOT_HARD_HIGH_COMP = _best_code(
            self._prohibitions,
            ("hard", "high", "compromised"),
            fallback="REQUIRES_HARD_HIGH_COMPROMISED",
        )

    def check(self, ctx: Dict[str, Any]) -> List[ProhibitionViolation]:
        """
        Evaluate prohibitions. Any returned violation prohibits BLOCK.
        Missing context is treated as prohibited where relevant.
        """
        violations: List[ProhibitionViolation] = []

        # ---- 0) Missing core context (conservative prohibit) ----
        # These are the minimum to even consider BLOCK legitimacy.
        required = [
            "constraint_status",
            "harm_profile",
            "judgment_integrity",
            "bias_evidence.failed_interventions",
            "justification.why_block_is_necessary",
            "justification.why_lower_measures_failed",
            "unblock_conditions.required_actions",
            "unblock_conditions.reassessment_triggers",
        ]
        missing = False
        for dotted in required:
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
            violations.append(
                ProhibitionViolation(
                    rule_id=self._CODE_MISSING_CORE,
                    severity="HIGH",
                    description="Missing required BLOCK context (fail-closed).",
                )
            )
            # Even if missing, still continue checks that might add more signal.

        # ---- 1) Must be exactly HARD/HIGH/COMPROMISED to even be eligible ----
        cs = ctx.get("constraint_status")
        hp = ctx.get("harm_profile")
        ji = ctx.get("judgment_integrity")
        if cs != "HARD" or hp != "HIGH" or ji != "COMPROMISED":
            violations.append(
                ProhibitionViolation(
                    rule_id=self._CODE_NOT_HARD_HIGH_COMP,
                    severity="HIGH",
                    description="BLOCK prohibited unless constraint_status=HARD, harm_profile=HIGH, judgment_integrity=COMPROMISED.",
                )
            )

        # ---- 2) Moral/political/ideological disagreement flags prohibit BLOCK ----
        flags = ctx.get("flags", {})
        if isinstance(flags, dict):
            if bool(flags.get("moral_disagreement")) is True:
                violations.append(
                    ProhibitionViolation(
                        rule_id=self._CODE_FLAGS,
                        severity="HIGH",
                        description="BLOCK prohibited when moral_disagreement is True.",
                    )
                )
            if bool(flags.get("political_disagreement")) is True:
                violations.append(
                    ProhibitionViolation(
                        rule_id=self._CODE_FLAGS,
                        severity="HIGH",
                        description="BLOCK prohibited when political_disagreement is True.",
                    )
                )
            if bool(flags.get("ideological_disagreement")) is True:
                violations.append(
                    ProhibitionViolation(
                        rule_id=self._CODE_FLAGS,
                        severity="HIGH",
                        description="BLOCK prohibited when ideological_disagreement is True.",
                    )
                )

        # ---- 3) Analysis-only mode prohibits BLOCK ----
        if ctx.get("mode") == "ANALYSIS_ONLY":
            violations.append(
                ProhibitionViolation(
                    rule_id=self._CODE_ANALYSIS_ONLY,
                    severity="HIGH",
                    description="BLOCK prohibited in ANALYSIS_ONLY mode.",
                )
            )

        # ---- 4) Failed interventions must include REFLECT and WARN (and typically SLOW) ----
        fi = _get_path(ctx, "bias_evidence.failed_interventions")
        if not isinstance(fi, list):
            # If missing core context already captured, this is redundant but fine (fail-closed).
            violations.append(
                ProhibitionViolation(
                    rule_id=self._CODE_FAILED_INTERVENTIONS,
                    severity="HIGH",
                    description="BLOCK prohibited unless failed_interventions is a list including REFLECT and WARN.",
                )
            )
        else:
            present = {x for x in fi if isinstance(x, str)}
            if "REFLECT" not in present or "WARN" not in present:
                violations.append(
                    ProhibitionViolation(
                        rule_id=self._CODE_FAILED_INTERVENTIONS,
                        severity="HIGH",
                        description="BLOCK prohibited unless failed_interventions includes REFLECT and WARN.",
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
