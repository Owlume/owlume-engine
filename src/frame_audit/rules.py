from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

Span = Tuple[int, int]

# --- Patterns ---
_RE_EITHER_OR = re.compile(r"\beither\b.*\bor\b", re.IGNORECASE | re.DOTALL)
_RE_CHOOSE_ONE = re.compile(r"\b(choose one|pick one|only one)\b", re.IGNORECASE)
_RE_BINARY_PRESSURE = re.compile(r"\b(or else|otherwise)\b", re.IGNORECASE)

_RE_HAS_NUMBER = re.compile(r"\b\d+(\.\d+)?\b")
_RE_HAS_PERCENT = re.compile(r"\b\d+(\.\d+)?\s*%\b")
_RE_TIME_UNITS = re.compile(r"\b(day|days|week|weeks|month|months|quarter|quarters|year|years)\b", re.IGNORECASE)
_RE_TIME_ABSOLUTE = re.compile(r"\b(by|within|in)\s+\d+\s*(day|days|week|weeks|month|months|quarter|quarters|year|years)\b", re.IGNORECASE)

_RE_METRIC_WORDS = re.compile(r"\b(metric|kpi|measure|success|acceptance test|criteria)\b", re.IGNORECASE)
_RE_BUSINESS_METRICS = re.compile(r"\b(churn|retention|revenue|arr|nps|conversion|latency|error rate)\b", re.IGNORECASE)

_RE_STAKEHOLDER_WORDS = re.compile(
    r"\b(customer|client|user|stakeholder|exec|leadership|team|hr|legal|employees|finance|ops|support|partner)\b",
    re.IGNORECASE,
)

_RE_SCOPE_AND_ALSO = re.compile(r"\b(and also|as well as|in addition|plus|also)\b", re.IGNORECASE)
_RE_SCOPE_MANY_ITEMS = re.compile(r"\b(plan|deck|diagram|implementation|tests|schemas)\b", re.IGNORECASE)

_RE_URGENT = re.compile(r"\b(asap|soon|urgent|immediately|right away)\b", re.IGNORECASE)

_RE_NO_BUDGET = re.compile(r"\b(no budget|zero budget|no money|no resources)\b", re.IGNORECASE)
_RE_PERFECT = re.compile(r"\b(perfect|flawless|100%|zero defects)\b", re.IGNORECASE)

# --- Span helpers ---
def _spans_for_pattern(text: str, pattern: re.Pattern) -> List[Span]:
    return [(m.start(), m.end()) for m in pattern.finditer(text or "")]

def find_false_dichotomy_spans(text: str) -> List[Span]:
    t = text or ""
    spans: List[Span] = []
    spans += _spans_for_pattern(t, _RE_EITHER_OR)
    spans += _spans_for_pattern(t, _RE_CHOOSE_ONE)
    spans += _spans_for_pattern(t, _RE_BINARY_PRESSURE)
    spans = sorted(spans, key=lambda s: (s[0], s[1]))

    # Merge overlaps
    merged: List[Span] = []
    for s in spans:
        if not merged:
            merged.append(s)
            continue
        prev = merged[-1]
        if s[0] <= prev[1]:
            merged[-1] = (prev[0], max(prev[1], s[1]))
        else:
            merged.append(s)
    return merged

def has_explicit_success_criteria(text: str, context: Optional[Dict[str, Any]] = None) -> bool:
    if context:
        sm = context.get("success_metrics")
        if isinstance(sm, list) and len(sm) > 0:
            return True
        if isinstance(sm, str) and sm.strip():
            return True

    t = text or ""
    has_metric_language = bool(_RE_METRIC_WORDS.search(t) or _RE_BUSINESS_METRICS.search(t))
    has_threshold = bool(_RE_HAS_PERCENT.search(t) or _RE_HAS_NUMBER.search(t))
    has_time = bool(_RE_TIME_UNITS.search(t) or _RE_TIME_ABSOLUTE.search(t))

    # Accept: mentions metrics AND includes either a threshold or timeframe.
    return has_metric_language and (has_threshold or has_time)

def has_stakeholders(text: str, context: Optional[Dict[str, Any]] = None) -> bool:
    if context:
        s = context.get("stakeholders")
        if isinstance(s, list) and len([x for x in s if str(x).strip()]) > 0:
            return True
        if isinstance(s, str) and s.strip():
            return True
    return bool(_RE_STAKEHOLDER_WORDS.search(text or ""))

def scope_creep_signal(text: str) -> float:
    t = text or ""
    # Many deliverables + many conjunctions => higher signal
    items = len(_RE_SCOPE_MANY_ITEMS.findall(t))
    conj = len(_RE_SCOPE_AND_ALSO.findall(t))
    score = 0.0
    score += min(1.0, items / 5.0) * 0.6
    score += min(1.0, conj / 3.0) * 0.4
    return min(1.0, score)

def has_concrete_timeframe(text: str, context: Optional[Dict[str, Any]] = None) -> bool:
    if context and context.get("timeframe"):
        return True
    t = text or ""
    return bool(_RE_TIME_ABSOLUTE.search(t) or _RE_TIME_UNITS.search(t) or _RE_HAS_NUMBER.search(t))

def timeframe_ambiguous_signal(text: str, context: Optional[Dict[str, Any]] = None) -> float:
    t = text or ""
    urgent = bool(_RE_URGENT.search(t))
    concrete = has_concrete_timeframe(t, context)
    return 1.0 if urgent and not concrete else 0.0

def constraint_conflict_signal(text: str) -> float:
    t = text or ""
    no_budget = bool(_RE_NO_BUDGET.search(t))
    perfect = bool(_RE_PERFECT.search(t))
    urgent = bool(_RE_URGENT.search(t))
    # Conflict if no budget plus either perfect or urgent (or both)
    if no_budget and (perfect or urgent):
        return 1.0
    return 0.0


