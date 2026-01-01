from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------
# Minimal Uncertainty Register utilities (deterministic; low-drift)
# Purpose:
# - Provide a lightweight "Uncertainty Register" block that can be added
#   when missing, detected when present, and parsed/validated in a basic way.
# - Keep behavior stable and conservative (no heavy NLP, no external deps).
# ---------------------------------------------------------------------

UR_HEADER_RE = re.compile(r"(?im)^\s*(uncertainty register|uncertainties|assumptions register)\s*:\s*$")
UR_BLOCK_RE = re.compile(
    r"(?is)(^|\n)\s*(Uncertainty Register|Uncertainties|Assumptions Register)\s*:\s*\n(.*?)(\n\s*\n|\Z)"
)

# Heuristic strong-claim cues (kept broad but simple)
_STRONG_CLAIM_CUES = [
    r"\bclearly\b",
    r"\bobviously\b",
    r"\bno doubt\b",
    r"\bguarantee(d)?\b",
    r"\bwill (definitely|certainly)\b",
    r"\bmust\b",
    r"\bproven\b",
    r"\b100%\b",
]
STRONG_CLAIM_RE = re.compile(r"(?i)(" + "|".join(_STRONG_CLAIM_CUES) + r")")

UR_TEMPLATE = """Uncertainty Register:
- Claim: <the key claim that could be wrong>
  Confidence (0–1): <e.g., 0.6>
  Evidence: <what supports it>
  Disconfirming test: <what would prove it wrong fast>
  Assumptions: <hidden assumptions behind the claim>
"""

# ----------------------------
# Public data structures
# ----------------------------

@dataclass(frozen=True)
class UncertaintyRegisterItem:
    claim: str
    confidence: float | None = None
    evidence: str | None = None
    disconfirming_test: str | None = None
    assumptions: str | None = None


# ----------------------------
# Detection / insertion
# ----------------------------

def has_uncertainty_register(text: str) -> bool:
    if not text:
        return False
    return bool(UR_HEADER_RE.search(text))


def add_uncertainty_register(text: str) -> str:
    """
    Append a minimal UR template if missing. Deterministic.
    """
    text = text or ""
    if has_uncertainty_register(text):
        return text
    # Keep formatting predictable: add a blank line then the template.
    sep = "\n\n" if text.strip() else ""
    return text.rstrip() + sep + UR_TEMPLATE


# ----------------------------
# Parsing
# ----------------------------

def extract_uncertainty_register_block(text: str) -> str | None:
    """
    Returns the raw UR block content (the bullets/lines after the header),
    or None if not found.
    """
    if not text:
        return None
    m = UR_BLOCK_RE.search(text)
    if not m:
        return None
    return (m.group(3) or "").strip() or None


def parse_uncertainty_register(text: str) -> list[UncertaintyRegisterItem]:
    """
    Best-effort parse of the UR template or similarly structured content.
    If parsing fails, returns an empty list (no exceptions).
    """
    block = extract_uncertainty_register_block(text)
    if not block:
        return []

    # Very lightweight parsing: look for "- Claim:" sections.
    items: list[UncertaintyRegisterItem] = []
    lines = [ln.rstrip() for ln in block.splitlines()]

    cur: dict[str, Any] = {}
    for ln in lines:
        s = ln.strip()
        if not s:
            continue

        if s.lower().startswith("- claim:"):
            # Flush previous
            if cur.get("claim"):
                items.append(_dict_to_item(cur))
            cur = {"claim": s.split(":", 1)[1].strip()}
            continue

        # Indented fields (support both "-" and plain indent)
        key, val = _parse_field_line(s)
        if key:
            cur[key] = val

    if cur.get("claim"):
        items.append(_dict_to_item(cur))

    return items


def _parse_field_line(s: str) -> tuple[str | None, str | None]:
    lower = s.lower()

    if lower.startswith("confidence"):
        # "Confidence (0–1): 0.6" or "Confidence: 0.6"
        val = s.split(":", 1)[1].strip() if ":" in s else ""
        return ("confidence", val or None)

    if lower.startswith("evidence:"):
        return ("evidence", s.split(":", 1)[1].strip() or None)

    if lower.startswith("disconfirming test:") or lower.startswith("disconfirming tests:"):
        return ("disconfirming_test", s.split(":", 1)[1].strip() or None)

    if lower.startswith("assumptions:"):
        return ("assumptions", s.split(":", 1)[1].strip() or None)

    return (None, None)


def _dict_to_item(cur: dict[str, Any]) -> UncertaintyRegisterItem:
    conf = cur.get("confidence")
    conf_f: float | None = None
    if conf is not None:
        conf_f = _safe_float(conf)

    return UncertaintyRegisterItem(
        claim=str(cur.get("claim") or "").strip(),
        confidence=conf_f,
        evidence=_none_if_empty(cur.get("evidence")),
        disconfirming_test=_none_if_empty(cur.get("disconfirming_test")),
        assumptions=_none_if_empty(cur.get("assumptions")),
    )


def _safe_float(x: Any) -> float | None:
    try:
        s = str(x).strip()
        if not s:
            return None
        # Accept 60% style inputs
        if s.endswith("%"):
            return float(s[:-1]) / 100.0
        return float(s)
    except Exception:
        return None


def _none_if_empty(x: Any) -> str | None:
    if x is None:
        return None
    s = str(x).strip()
    return s if s else None


# ----------------------------
# Validation (minimal)
# ----------------------------

def validate_uncertainty_register_items(items: list[UncertaintyRegisterItem]) -> tuple[bool, list[str]]:
    """
    Minimal validation:
    - at least 1 item
    - each item has a non-empty claim
    - confidence, if present, is within [0, 1]
    """
    errors: list[str] = []

    if not items:
        errors.append("UR: no items parsed")
        return (False, errors)

    for i, it in enumerate(items, start=1):
        if not it.claim.strip():
            errors.append(f"UR item {i}: missing claim")
        if it.confidence is not None and not (0.0 <= it.confidence <= 1.0):
            errors.append(f"UR item {i}: confidence out of range: {it.confidence}")

    return (len(errors) == 0, errors)


# ----------------------------
# Strong-claim helpers
# ----------------------------

def find_strong_claim_spans(text: str) -> list[tuple[int, int]]:
    """
    Returns spans for strong-claim cue matches.
    """
    if not text:
        return []
    return [(m.start(), m.end()) for m in STRONG_CLAIM_RE.finditer(text)]


def has_strong_claim_cues(text: str) -> bool:
    return bool(find_strong_claim_spans(text))
