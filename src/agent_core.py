"""
Owlume — Stage 4 · L5
T2 — Learning Loop Core
File: src/agent_core.py

Implements the Learning Agent core functions:
- self_prompt(): generate candidate questioning variants for meta-eval
- meta_eval(): compare predicted vs. actual clarity gain and score effectiveness
- learn(): compute policy deltas from empathy × clarity signals
- log_learning_event(): append a Learning Agent record to runtime JSONL

This module is schema-aligned with /schemas/learning_agent.schema.json
and writes records consumable by /scripts/aggregate_agent_memory.py.

Windows-safe: ASCII markers only in prints.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

# -------------------------------
# Config
# -------------------------------
RUNTIME_LOG = Path("data/runtime/agent_memory.jsonl")
AGENT_VERSION = "0.1.0"

# Learning hyperparams (conservative defaults)
MAX_STEP = 0.08  # cap per-update magnitude
MIN_STEP = 0.01  # minimum nudge if direction is clear
DECAY = 0.92     # dampen repeated changes across sessions
EMPATHY_WEIGHT_GAIN = 0.5  # how much E influences delta magnitude

# Safety bounds for policy vector values
POLICY_MIN = 0.0
POLICY_MAX = 1.0

# Keys we expect in a baseline policy
DEFAULT_POLICY_KEYS = (
    "risk_probe",
    "assumption_challenge",
    "empathy_weight",
    "tone_warmth",
)


# -------------------------------
# Data structures (aligned with schema fields)
# -------------------------------
@dataclass
class EmpathyState:
    state: str  # "ON" | "OFF" | "AUTO"
    intensity: Optional[float] = None  # 0..1
    rationale: Optional[str] = None


@dataclass
class ContextState:
    mode: str
    principle: str
    empathy_state: EmpathyState


@dataclass
class InputsEmpathy:
    E: float  # 0..1
    feedback: Optional[dict] = None


@dataclass
class InputsClarity:
    cg_pre: float
    cg_post: float
    cg_delta: float


@dataclass
class PolicyUpdate:
    changed_keys: List[str]
    delta: Dict[str, float]
    reason: str


@dataclass
class MetaEval:
    predicted_cg_delta: float
    actual_cg_delta: float
    error: float
    meta_score: float  # 0..1


# -------------------------------
# Utilities
# -------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(x: float, lo: float, hi: float) -> float:
    return min(max(x, lo), hi)


def _ensure_policy_keys(policy: Dict[str, float]) -> Dict[str, float]:
    out = dict(policy)
    for k in DEFAULT_POLICY_KEYS:
        out.setdefault(k, 0.5)
        out[k] = _clamp(out[k], POLICY_MIN, POLICY_MAX)
    return out


# -------------------------------
# Self-prompting & meta evaluation
# -------------------------------

def self_prompt(context: ContextState, policy: Dict[str, float]) -> List[str]:
    """Generate lightweight candidate questioning variants for testing.

    In production this would branch prompts more richly. Here we vary only
    a few axes derived from the policy knobs to keep things interpretable.
    """
    p = _ensure_policy_keys(policy)
    variants = []

    rp = p["risk_probe"]
    ac = p["assumption_challenge"]
    ew = p["empathy_weight"]
    tw = p["tone_warmth"]

    base = f"[{context.mode}×{context.principle}]"

    variants.append(
        f"{base} If the key risk came true tomorrow, what breaks first—and how would you know?"
    )
    variants.append(
        f"{base} What assumption, if false, collapses this plan—and what quick test can we run this week?"
    )

    # Slightly warmer variant if tone_warmth high or empathy ON/AUTO
    if tw > 0.6 or context.empathy_state.state in ("ON", "AUTO"):
        variants.append(
            f"{base} From the stakeholders' vantage point, what might feel unseen or risky here?"
        )

    # Empathy-weighted reflective probe
    if ew > 0.55:
        variants.append(
            f"{base} Before deciding, what would lower anxiety for the most exposed person?"
        )

    # Assumption challenge intensifier
    if ac > 0.6:
        variants.append(
            f"{base} Which single evidence would most quickly disprove your favored path?"
        )

    # Risk probe intensifier
    if rp > 0.6:
        variants.append(
            f"{base} Name a tripwire metric that would trigger an immediate rethink."
        )

    return variants[:5]


def meta_eval(predicted_cg_delta: float, actual_cg_delta: float) -> MetaEval:
    """Score how close the agent's prediction was to actual clarity change.

    meta_score ∈ [0,1], higher is better. Use a simple radial basis penalty.
    """
    err = abs(actual_cg_delta - predicted_cg_delta)
    # Soft accuracy: 0 error → 1.0, 0.3 error → ~0.37, 0.5 error → ~0.135
    meta_score = _clamp(pow(0.3, err * 5), 0.0, 1.0)
    return MetaEval(
        predicted_cg_delta=predicted_cg_delta,
        actual_cg_delta=actual_cg_delta,
        error=err,
        meta_score=meta_score,
    )


# -------------------------------
# Learning rule
# -------------------------------

def _predict_delta_simple(E: float, policy: Dict[str, float]) -> float:
    """A tiny, transparent predictor of expected clarity gain delta.

    This is deliberately simple: weighted sum of policy axes plus empathy.
    """
    p = _ensure_policy_keys(policy)
    score = (
        0.35 * p["risk_probe"]
        + 0.35 * p["assumption_challenge"]
        + 0.2 * p["empathy_weight"]
        + 0.1 * p["tone_warmth"]
        + 0.25 * E
    )
    # map to plausible cg_delta range [-0.1, 0.5]
    return _clamp((score - 0.5) * 1.2, -0.10, 0.50)


def learn(
    *,
    did: Optional[str],
    session_id: Optional[str],
    user_hash: Optional[str],
    context: ContextState,
    inputs_empathy: InputsEmpathy,
    inputs_clarity: InputsClarity,
    policy_before: Dict[str, float],
    belief_map_touch: Optional[List[str]] = None,
    dry_run: bool = False,
) -> Tuple[Dict[str, float], PolicyUpdate, MetaEval]:
    """Compute policy_after, update, and meta-eval from a single session outcome.

    Learning intuition:
    - If actual cg_delta > predicted, reinforce axes that likely helped (risk_probe,
      assumption_challenge, empathy_weight, tone_warmth), scaled by empathy E.
    - If actual < predicted, reduce pressure on the most aggressive axes first.
    - Steps are damped and clamped for stability.
    """
    E = _clamp(inputs_empathy.E, 0.0, 1.0)
    p0 = _ensure_policy_keys(policy_before)

    pred = _predict_delta_simple(E, p0)
    actual = inputs_clarity.cg_delta
    m = meta_eval(pred, actual)

    gap = actual - pred  # positive → we underpredicted (good), negative → overpredicted

    # Directional signals
    s_risk = 1.0 if gap > 0 else -1.0
    s_assump = 1.0 if gap > 0 else -1.0
    s_empathy = 1.0 if (gap > 0 and context.empathy_state.state != "OFF") else (-1.0)
    s_tone = 0.5 if gap > 0 else -0.5  # tone is gentler lever

    base_step = max(MIN_STEP, min(MAX_STEP, abs(gap) * (EMPATHY_WEIGHT_GAIN * (0.5 + E))))

    delta = {
        "risk_probe": _clamp(s_risk * base_step, -MAX_STEP, MAX_STEP),
        "assumption_challenge": _clamp(s_assump * base_step, -MAX_STEP, MAX_STEP),
        "empathy_weight": _clamp(s_empathy * base_step, -MAX_STEP, MAX_STEP),
        "tone_warmth": _clamp(s_tone * base_step * 0.7, -MAX_STEP, MAX_STEP),
    }

    # Apply decay to avoid oscillation if past deltas were similar. (No memory here; hook for future.)
    for k in delta:
        delta[k] *= DECAY

    p1 = dict(p0)
    changed_keys: List[str] = []
    for k, dv in delta.items():
        if abs(dv) < 1e-6:
            continue
        p1[k] = _clamp(p1[k] + dv, POLICY_MIN, POLICY_MAX)
        changed_keys.append(k)

    reason = (
        f"gap={gap:.3f} (pred={pred:.3f}, actual={actual:.3f}), E={E:.2f}; "
        f"reinforce={'yes' if gap>0 else 'no'}, empathy_state={context.empathy_state.state}"
    )

    update = PolicyUpdate(changed_keys=changed_keys, delta=delta, reason=reason)

    # Optionally log immediately (caller may also log)
    if not dry_run:
        log_learning_event(
            did=did,
            session_id=session_id,
            user_hash=user_hash,
            context=context,
            E=E,
            feedback=inputs_empathy.feedback or {},
            clarity=inputs_clarity,
            policy_before=p0,
            policy_after=p1,
            update=update,
            meta=m,
            belief_map_touch=belief_map_touch or [],
        )

    return p1, update, m


# -------------------------------
# Logging
# -------------------------------

def log_learning_event(
    *,
    did: Optional[str],
    session_id: Optional[str],
    user_hash: Optional[str],
    context: ContextState,
    E: float,
    feedback: dict,
    clarity: InputsClarity,
    policy_before: Dict[str, float],
    policy_after: Dict[str, float],
    update: PolicyUpdate,
    meta: MetaEval,
    belief_map_touch: List[str],
    safety_ok: bool = True,
    poc_signals: Optional[List[str]] = None,
    safety_notes: Optional[str] = None,
    notes: Optional[str] = None,
) -> None:
    """Append a Learning Agent record to runtime JSONL (schema-aligned)."""

    record = {
        "timestamp": _now_iso(),
        "agent_version": AGENT_VERSION,
        "intent": "post_session_adjustment",
        "ids": {
            "did": did,
            "session_id": session_id,
            "user_hash": user_hash,
        },
        "context_state": {
            "mode": context.mode,
            "principle": context.principle,
            "empathy_state": asdict(context.empathy_state),
        },
        "inputs": {
            "empathy": {"E": E, "feedback": feedback},
            "clarity": asdict(clarity),
        },
        "policy": {
            "before": _ensure_policy_keys(policy_before),
            "after": _ensure_policy_keys(policy_after),
        },
        "update": asdict(update),
        "meta_eval": asdict(meta),
        "belief_map_touch": list(belief_map_touch or []),
        "safety": {
            "ok": bool(safety_ok),
            "poc_signals": list(poc_signals or []),
            "notes": safety_notes or "",
        },
        "notes": notes or "",
    }

    RUNTIME_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNTIME_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print("[OK] Logged learning event →", RUNTIME_LOG)


# -------------------------------
# Quick CLI smoke (optional)
# -------------------------------
if __name__ == "__main__":
    # Minimal example run to verify end-to-end logging
    ctx = ContextState(
        mode="Decision",
        principle="Risk",
        empathy_state=EmpathyState(state="AUTO", intensity=0.7, rationale="stakes high + uncertainty"),
    )

    policy0 = {"risk_probe": 0.40, "assumption_challenge": 0.45, "empathy_weight": 0.55, "tone_warmth": 0.50}

    p1, upd, meta = learn(
        did="DID-2025-TEST",
        session_id="S-TEST-001",
        user_hash="u_demo",
        context=ctx,
        inputs_empathy=InputsEmpathy(E=0.72, feedback={"tone": "softened"}),
        inputs_clarity=InputsClarity(cg_pre=0.42, cg_post=0.56, cg_delta=0.14),
        policy_before=policy0,
        belief_map_touch=["risk_underestimation", "stakeholder_concern"],
        dry_run=False,
    )

    print("[OK] learn() complete; policy_after=", p1)
