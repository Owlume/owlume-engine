from __future__ import annotations
from typing import Optional, Dict, Any
from .types import FrameAuditResult, FrameAuditTrace
from .check_registry import CHECK_SPECS, TRACE_SPEC
from .checks import DETECTORS

import re


try:
    from src.frame_audit.score import score_checks  # type: ignore
except Exception as e:  # pragma: no cover
    score_checks = None  # type: ignore

try:
    from src.frame_audit.checks import CHECKS as FA_CHECKS  # list of callables
except Exception:
    FA_CHECKS = []

# -----------------------------
# Types / helpers
# -----------------------------

Severity = str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
Status = str    # "PASS" | "WARN" | "FAIL"


def _evidence_span(text: str, snippet: str) -> Optional[Dict[str, Any]]:
    """Return a deterministic evidence span for a snippet if found; else None."""
    if not snippet:
        return None
    idx = text.find(snippet)
    if idx < 0:
        return None
    return {
        "start": idx,
        "end": idx + len(snippet),
        "text": snippet,
    }


def _check(
    check_id: str,
    status: Status,
    severity: Severity,
    rationale: str,
    *,
    evidence_spans: Optional[List[Dict[str, Any]]] = None,
    assumption_refs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "check_id": check_id,
        "status": status,
        "severity": severity,
        "rationale": rationale,
        "evidence_spans": evidence_spans or [],
        "assumption_refs": assumption_refs or [],
    }


def _context_dict(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return context if isinstance(context, dict) else {}


def _get_uncertainty_assumptions(context: Optional[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """
    Returns assumptions list if the uncertainty_register is present and assumptions is a list.
    Does NOT validate disconfirming_tests here by design.
    """
    ctx = _context_dict(context)
    reg = ctx.get("uncertainty_register")
    if not isinstance(reg, dict):
        return None
    assumptions = reg.get("assumptions")
    if not isinstance(assumptions, list):
        return None

    # Normalize: keep only dict assumptions
    norm: List[Dict[str, Any]] = []
    for a in assumptions:
        if isinstance(a, dict):
            norm.append(a)
    return norm


def _assumption_id(a: Dict[str, Any]) -> str:
    return str(a.get("id", "")).strip()


def _assumption_statement(a: Dict[str, Any]) -> str:
    return str(a.get("statement", "")).strip()


def _is_structurally_valid_register(assumptions: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Structural validity for UR-MISSING-REGISTER-1:
    - assumptions list exists and non-empty
    - each assumption is dict with non-empty id and statement

    IMPORTANT: disconfirming_tests is NOT required here (handled by UR-NO-DISCONFIRMING-TEST-1).
    """
    if not assumptions:
        return False, []

    ids: List[str] = []
    for a in assumptions:
        aid = _assumption_id(a)
        stmt = _assumption_statement(a)
        if not aid or not stmt:
            return False, []
        ids.append(aid)
    return True, ids

def _load_fa_check_fns():
    try:
        import src.frame_audit.checks as fa_mod  # type: ignore
    except Exception:
        return []

    # Common patterns: CHECKS list of callables, or individual functions.
    if hasattr(fa_mod, "CHECKS") and isinstance(getattr(fa_mod, "CHECKS"), list):
        fns = [fn for fn in getattr(fa_mod, "CHECKS") if callable(fn)]
        return fns

    # Fallback: collect callables named like check_fa_*()
    fns = []
    for name in dir(fa_mod):
        if name.startswith("check_") and callable(getattr(fa_mod, name)):
            fn = getattr(fa_mod, name)
            # only include FA checks by name heuristic if you have it, otherwise include all
            fns.append(fn)
    return fns


# -----------------------------
# UR checks (Step 4 discipline)
# -----------------------------

_STRONG_CLAIM_RE = re.compile(
    r"""
    \b(
        must|clearly|obviously|definitely|certainly|guaranteed|inevitably|
        will|always|never|cannot\s+fail|can't\s+fail|no\s+doubt
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _extract_strong_claim_snippets(text: str) -> List[str]:
    """
    Deterministic strong-claim extraction:
    - find trigger tokens
    - expand to a short window around the match
    - de-duplicate by snippet text
    """
    if not text:
        return []

    snippets: List[str] = []
    for m in _STRONG_CLAIM_RE.finditer(text):
        start = max(0, m.start() - 30)
        end = min(len(text), m.end() + 60)
        snippet = text[start:end].strip()
        if snippet and snippet not in snippets:
            snippets.append(snippet)

    # Cap to avoid runaway
    return snippets[:10]


def _tokenize(s: str) -> List[str]:
    s = s.lower()
    # basic tokenization; deterministic
    toks = re.findall(r"[a-z0-9]+", s)
    # remove very short tokens
    return [t for t in toks if len(t) >= 3]


def _overlap_score(a: str, b: str) -> int:
    ta = set(_tokenize(a))
    tb = set(_tokenize(b))
    return len(ta.intersection(tb))


def check_ur_missing_register(text: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    UR-MISSING-REGISTER-1
    FAIL only when the frame makes strong/definitive claims but provides no uncertainty register.
    PASS when there are no strong-claim markers (UR discipline not required).
    """
    # Only require a register if we detect strong claims
    claim_snippets = _extract_strong_claim_snippets(text)
    if not claim_snippets:
        return _check(
            "UR-MISSING-REGISTER-1",
            "PASS",
            "LOW",
            "No strong-claim markers detected; uncertainty register not required for this frame.",
        )

    assumptions = _get_uncertainty_assumptions(context)
    if assumptions is None:
        ev = _evidence_span(text, claim_snippets[0][:120])
        return _check(
            "UR-MISSING-REGISTER-1",
            "FAIL",
            "HIGH",
            "Strong claims detected but no uncertainty_register.assumptions provided; add explicit assumptions and confidence/disconfirmers.",
            evidence_spans=[ev] if ev else [],
        )

    ok, ids = _is_structurally_valid_register(assumptions)
    if not ok:
        ev = _evidence_span(text, claim_snippets[0][:120])
        return _check(
            "UR-MISSING-REGISTER-1",
            "FAIL",
            "HIGH",
            "Strong claims detected and uncertainty_register is present but structurally invalid (each assumption must have id + statement).",
            evidence_spans=[ev] if ev else [],
        )

    return _check(
        "UR-MISSING-REGISTER-1",
        "PASS",
        "LOW",
        "Uncertainty register present with structurally valid assumptions (id + statement).",
        assumption_refs=ids,
    )


def check_ur_implicit_assumption(text: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    UR-IMPLICIT-ASSUMPTION-1
    Penalize strong claims in the frame that are not mapped to any assumption statement.
    Deterministic mapping via token overlap; threshold tuned to reduce false positives.
    """
    assumptions = _get_uncertainty_assumptions(context)
    if assumptions is None:
        # Missing register is handled elsewhere; don't double-penalize.
        return _check(
            "UR-IMPLICIT-ASSUMPTION-1",
            "PASS",
            "LOW",
            "No register to map against; handled by UR-MISSING-REGISTER-1.",
        )

    ok, ids = _is_structurally_valid_register(assumptions)
    if not ok:
        # structural problems are handled by UR-MISSING-REGISTER-1
        return _check(
            "UR-IMPLICIT-ASSUMPTION-1",
            "PASS",
            "LOW",
            "Register structurally invalid; handled by UR-MISSING-REGISTER-1.",
        )

    claim_snippets = _extract_strong_claim_snippets(text)
    if not claim_snippets:
        return _check(
            "UR-IMPLICIT-ASSUMPTION-1",
            "PASS",
            "LOW",
            "No strong-claim markers detected; nothing to map.",
            assumption_refs=ids,
        )

    # Map each claim snippet to best assumption by overlap; require threshold >= 4
    # This makes matching more conservative and reduces false positives.
    THRESH = 4

    matched_ids: List[str] = []
    unmapped: List[str] = []

    for snip in claim_snippets:
        best_id = ""
        best = 0
        for a in assumptions:
            aid = _assumption_id(a)
            stmt = _assumption_statement(a)
            if not aid or not stmt:
                continue
            sc = _overlap_score(snip, stmt)
            if sc > best:
                best = sc
                best_id = aid
        if best_id and best >= THRESH:
            if best_id not in matched_ids:
                matched_ids.append(best_id)
        else:
            unmapped.append(snip)

    if not unmapped:
        return _check(
            "UR-IMPLICIT-ASSUMPTION-1",
            "PASS",
            "LOW",
            "All detected strong claims are mapped to an explicit assumption in the register.",
            assumption_refs=matched_ids,
        )

    # Deterministic severity policy (A-Lite): no CRITICAL escalation here.
    if len(unmapped) == 1:
        sev = "MEDIUM"
        status = "WARN"
    else:
        sev = "HIGH"
        status = "FAIL"

    ev = _evidence_span(text, unmapped[0][:120])
    return _check(
        "UR-IMPLICIT-ASSUMPTION-1",
        status,
        sev,
        f"{len(unmapped)} strong claim(s) appear not to be explicitly mapped to any listed assumption statement.",
        evidence_spans=[ev] if ev else [],
        assumption_refs=matched_ids,
    )


def check_ur_no_disconfirming_tests(text: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    UR-NO-DISCONFIRMING-TEST-1
    Penalize assumptions that have missing/empty disconfirming_tests.
    IMPORTANT: this should not cause UR-MISSING-REGISTER-1 to fail.
    """
    assumptions = _get_uncertainty_assumptions(context)
    if assumptions is None:
        return _check(
            "UR-NO-DISCONFIRMING-TEST-1",
            "PASS",
            "LOW",
            "No register present; handled by UR-MISSING-REGISTER-1.",
        )

    ok, ids = _is_structurally_valid_register(assumptions)
    if not ok:
        return _check(
            "UR-NO-DISCONFIRMING-TEST-1",
            "PASS",
            "LOW",
            "Register structurally invalid; handled by UR-MISSING-REGISTER-1.",
        )

    missing_ids: List[str] = []
    for a in assumptions:
        aid = _assumption_id(a)
        if not aid:
            continue
        tests = a.get("disconfirming_tests", None)
        if (not isinstance(tests, list)) or (len(tests) == 0):
            missing_ids.append(aid)

    if not missing_ids:
        return _check(
            "UR-NO-DISCONFIRMING-TEST-1",
            "PASS",
            "LOW",
            "All assumptions include at least one disconfirming_tests item.",
            assumption_refs=ids,
        )

    # Deterministic severity policy
    if len(missing_ids) == 1:
        status = "WARN"
        sev = "MEDIUM"
    else:
        status = "FAIL"
        sev = "HIGH"

    ev = _evidence_span(text, text[:120].strip())
    return _check(
        "UR-NO-DISCONFIRMING-TEST-1",
        status,
        sev,
        f"{len(missing_ids)} assumption(s) missing disconfirming_tests; add falsifiable checks that would change your confidence.",
        evidence_spans=[ev] if ev else [],
        assumption_refs=missing_ids,
    )

# -----------------------------
# FA loader (from src/frame_audit/checks.py)
# -----------------------------
def _load_fa_check_fns():
    """
    Load FA check callables from src.frame_audit.checks.py.

    In this repo, checks.py does NOT export a CHECKS list.
    It defines check_* functions that return a CheckResult object with .check_id.
    """
    try:
        import src.frame_audit.checks as fa_mod  # type: ignore
    except Exception:
        return []

    fns = []
    for name in dir(fa_mod):
        if not name.startswith("check_"):
            continue
        fn = getattr(fa_mod, name, None)
        if not callable(fn):
            continue

        # Probe once to ensure it emits FA-* (CheckResult object)
        try:
            out = fn("Either we pivot now or we die. Choose one.", {})
            cid = getattr(out, "check_id", None)
            if isinstance(cid, str) and cid.startswith("FA-"):
                fns.append(fn)
        except Exception:
            continue

    # Deterministic ordering by emitted check_id
    def _key(fn_):
        try:
            out_ = fn_("Either we pivot now or we die. Choose one.", {})
            cid_ = getattr(out_, "check_id", "")
        except Exception:
            cid_ = ""
        return (str(cid_), getattr(fn_, "__name__", ""))

    return sorted(fns, key=_key)

    def _try_call(fn):
        text = "Either we pivot now or we die. Choose one."
        ctx = {"stakeholders": ["Exec team"], "success_metrics": ["Retention +10%"], "timeframe": "4 weeks"}
        # Try common invocation styles
        for args, kwargs in (
            ((text, ctx), {}),
            ((text,), {"context": ctx}),
            ((text,), {}),
            ((), {"text": text, "context": ctx}),
            ((), {"text": text}),
        ):
            try:
                return fn(*args, **kwargs)
            except Exception:
                continue
        return None

    # Normalize FA CheckResult (object) -> dict for downstream scoring/tests
    if not isinstance(result, dict) and hasattr(result, "check_id"):
        result = {
            "check_id": result.check_id,
            "status": "FAIL" if getattr(result, "hit", False) else "PASS",
            "severity": "HIGH" if float(getattr(result, "score", 0.0)) >= 0.8 else "MEDIUM",
            "confidence": float(getattr(result, "confidence", 1.0)),
            "weight": float(getattr(result, "weight", 0.0)),
            "score": float(getattr(result, "score", 0.0)),
            "label": getattr(result, "label", None),
            "evidence": [
            {
                "start": getattr(e, "start", None),
                "end": getattr(e, "end", None),
                "text": getattr(e, "text", None),
                "reason": getattr(e, "reason", None),
            }
            for e in (getattr(result, "evidence", None) or [])
        ],
    }

    # 1) Prefer any exported registry if present; support list/dict/spec shapes
    for reg_name in ("FA_CHECK_FNS", "FA_CHECKS", "CHECKS", "ALL_CHECKS"):
        reg = getattr(fa_mod, reg_name, None)
        if isinstance(reg, list) and reg:
            # list of callables
            if all(callable(x) for x in reg):
                candidates = list(reg)
            else:
                # list of specs (dict/object) that point to a function
                candidates = []
                for item in reg:
                    fn = None
                    if callable(item):
                        fn = item
                    elif isinstance(item, dict):
                        v = item.get("fn") or item.get("check_fn") or item.get("callable") or item.get("func")
                        if callable(v):
                            fn = v
                        elif isinstance(v, str) and hasattr(fa_mod, v):
                            fn = getattr(fa_mod, v)
                    else:
                        # object spec with .fn or .func
                        for attr in ("fn", "func", "callable"):
                            if hasattr(item, attr):
                                v = getattr(item, attr)
                                if callable(v):
                                    fn = v
                                elif isinstance(v, str) and hasattr(fa_mod, v):
                                    fn = getattr(fa_mod, v)
                    if callable(fn):
                        candidates.append(fn)
        elif isinstance(reg, dict) and reg:
            # dict mapping -> try values
            candidates = [v for v in reg.values() if callable(v)]
        else:
            continue

        # Probe candidates and keep only FA-* emitters
        fns = []
        for fn in candidates:
            out = _try_call(fn)
            cid = _extract_check_id(out)
            if isinstance(cid, str) and cid.startswith("FA-"):
                fns.append(fn)

        if fns:
            # sort deterministically by emitted check_id then name
            def _key(fn_):
                out_ = _try_call(fn_)
                cid_ = _extract_check_id(out_) or ""
                return (str(cid_), getattr(fn_, "__name__", ""))
            return sorted(fns, key=_key)

    # 2) Final fallback: probe all check_* callables in module
    candidates = [getattr(fa_mod, n) for n in dir(fa_mod) if n.startswith("check_") and callable(getattr(fa_mod, n))]
    fns = []
    for fn in candidates:
        out = _try_call(fn)
        cid = _extract_check_id(out)
        if isinstance(cid, str) and cid.startswith("FA-"):
            fns.append(fn)

    return sorted(fns, key=lambda f: getattr(f, "__name__", ""))


# -----------------------------
# Registry
# -----------------------------

FA_CHECK_FNS = _load_fa_check_fns()

CHECKS = [
    # UR checks
    check_ur_missing_register,
    check_ur_implicit_assumption,
    check_ur_no_disconfirming_tests,
] + list(FA_CHECK_FNS)


# -----------------------------
# Public API
# -----------------------------

def _score_from_hits(risk_breakdown: dict[str, float]) -> float:
    # Simple bounded sum for Stage 11
    raw = sum(risk_breakdown.values())
    return min(1.0, raw)

def audit_frame(text: str, context: Optional[Dict[str, Any]] = None) -> FrameAuditResult:
    hits = []
    risk_breakdown: dict[str, float] = {}

    for spec in CHECK_SPECS:
        if not spec.enabled:
            continue
        detector = DETECTORS.get(spec.check_id)
        if detector is None:
            # Missing implementation; treat as zero risk for now
            risk_breakdown[spec.check_id] = 0.0
            continue
        hit = detector(text, context)
        if hit is None:
            risk_breakdown[spec.check_id] = 0.0
            continue
        hits.append(hit)
        # check contribution = spec.weight * hit.score
        risk_breakdown[spec.check_id] = spec.weight * max(0.0, min(1.0, hit.score))

    frame_risk_score = _score_from_hits(risk_breakdown)

    trace = FrameAuditTrace(
        spec=TRACE_SPEC,
        text=text,
        context=context,
        hits=hits,
        risk_breakdown=risk_breakdown,
        frame_risk_score=frame_risk_score,
    )

    return FrameAuditResult(
        spec=TRACE_SPEC,
        frame_risk_score=frame_risk_score,
        risk_breakdown=risk_breakdown,
        trace=trace,
    )

def _normalize_check_result(x):
    if x is None:
        return {
            "check_id": "UNKNOWN",
            "status": "PASS",
            "severity": "LOW",
            "confidence": 1.0,
            "weight": 0.0,
            "score": 0.0,
            "label": None,
            "evidence": [],
        }

    if isinstance(x, dict):
        return x

    if hasattr(x, "check_id"):
        return {
            "check_id": getattr(x, "check_id", None),
            "status": "FAIL" if getattr(x, "hit", False) else "PASS",
            "severity": "HIGH" if float(getattr(x, "score", 0.0)) >= 0.8 else "MEDIUM",
            "confidence": float(getattr(x, "confidence", 1.0)),
            "weight": float(getattr(x, "weight", 0.0)),
            "score": float(getattr(x, "score", 0.0)),
            "label": getattr(x, "label", None),
            "evidence": [
                {
                    "start": getattr(e, "start", None),
                    "end": getattr(e, "end", None),
                    "text": getattr(e, "text", None),
                    "reason": getattr(e, "reason", None),
                }
                for e in (getattr(x, "evidence", None) or [])
            ],
        }

    return {
        "check_id": "UNKNOWN",
        "status": "PASS",
        "severity": "LOW",
        "confidence": 1.0,
        "weight": 0.0,
        "score": 0.0,
        "label": None,
        "evidence": [],
    }

    # Fallback: keep pipeline stable
    return {
        "check_id": "UNKNOWN",
        "status": "PASS",
        "severity": "LOW",
        "confidence": 1.0,
        "weight": 0.0,
        "score": 0.0,
        "label": None,
        "evidence": [],
    }

    # --- FINAL NORMALIZATION PASS (critical) ---
    if isinstance(trace.get("checks"), list):
        trace["checks"] = [_normalize_check_result(c) for c in trace["checks"]]

    return trace
