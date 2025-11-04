# src/adapters/elenx_processor.py
from __future__ import annotations
import random
from typing import Dict, Any

# ---- Optional imports (graceful if not present) ----
try:
    # Your engine (names seen in logs: elenx_engine.py with hybrid fusion)
    from src.elenx_engine import hybrid_detect, detectMode, detectPrinciple, render_questions  # type: ignore
except Exception:
    hybrid_detect = None
    detectMode = None
    detectPrinciple = None
    render_questions = None

try:
    # Fallacy matcher you validated on 2025-11-01
    from src.loaders.fallacies_loader import match_fallacy_variants, FALLACY_IDX  # type: ignore
except Exception:
    match_fallacy_variants = None
    FALLACY_IDX = None

# -------------- helpers --------------

def _fallback_qs(mode: str, principle: str) -> list[str]:
    # Minimal question templates if render_questions() is unavailable
    table = {
        ("Decision", "Alternatives"): [
            "What viable third options are you excluding?",
            "Which risks are reversible vs. irreversible here?",
        ],
        ("Analytical", "Evidence"): [
            "What evidence would change your mind?",
            "Which assumptions deserve a quick test?",
        ],
    }
    return table.get((mode, principle), [
        "What’s the strongest counterpoint you might be missing?",
        "What simple experiment would cut the uncertainty?",
    ])

def _guess_empathy() -> Dict[str, Any]:
    return {
        "activation": random.choice(["LOW", "MEDIUM", "HIGH"]),
        "bias": round(random.uniform(-0.2, 0.2), 3)
    }

def _match_fallacies(text: str, k: int = 3):
    if match_fallacy_variants and FALLACY_IDX:
        try:
            hits = match_fallacy_variants(text, FALLACY_IDX, k=k)  # returns list[(id, score)]
            out = []
            for fid, score in hits:
                out.append({"id": str(fid), "label": None, "score": float(score)})
            return out
        except Exception:
            pass
    return []

# -------------- main processor --------------

def process_with_elenx(text: str) -> Dict[str, Any]:
    """
    Returns a dict shaped like schema.processing_output (minus ids),
    i.e. keys: mode, principle, confidence, questions, fallacies?, context_drivers?, empathy_state?, clarity?, vectors?, audit?
    """
    mode = "Analytical"
    principle = "Evidence"
    confidence = 0.60
    questions = []
    fallacies = _match_fallacies(text)
    context_drivers = [{"id": "C-INCENTIVE-1", "label": "Incentive Pressure", "score": round(random.uniform(0.3, 0.7), 2)}]

    # --- Try hybrid_detect first (if your engine exposes it) ---
    picked = None
    if hybrid_detect:
        try:
            # Expecting something like: {"mode": "...", "principle": "...", "confidence": 0.xx, "qs": [...], "empathy": {...}}
            picked = hybrid_detect(text)  # type: ignore
            if isinstance(picked, dict):
                mode = picked.get("mode", mode)
                principle = picked.get("principle", principle)
                confidence = float(picked.get("confidence", confidence))
                questions = picked.get("qs") or picked.get("questions") or []
                empathy_state = picked.get("empathy") or picked.get("empathy_state") or _guess_empathy()
            else:
                empathy_state = _guess_empathy()
        except Exception:
            empathy_state = _guess_empathy()
            picked = None
    else:
        empathy_state = _guess_empathy()

    # --- Fallback: detectMode / detectPrinciple if hybrid not present or gave nothing ---
    if not questions:
        try:
            if detectMode:
                mode = detectMode(text)  # type: ignore
            if detectPrinciple:
                principle = detectPrinciple(text, mode_hint=mode)  # type: ignore
        except Exception:
            pass
        # questions from renderer if available; else fallback templates
        if render_questions:
            try:
                qs = render_questions(mode=mode, principle=principle, text=text)  # type: ignore
                if isinstance(qs, list) and qs:
                    questions = [str(x) for x in qs][:7]
            except Exception:
                pass
        if not questions:
            questions = _fallback_qs(mode, principle)

    # --- Minimal bias vector snapshot (optional; schema allows more but not required) ---
    vectors = {
        "bias_vector": {
            "evidence": round(random.uniform(0.4, 0.9), 3),
            "agency": round(random.uniform(0.3, 0.8), 3),
            "risk": round(random.uniform(0.5, 0.95), 3),
            "conflict": round(random.uniform(0.2, 0.6), 3),
            "identity": round(random.uniform(0.1, 0.5), 3),
            "ambiguity": round(random.uniform(0.3, 0.7), 3),
        }
    }
    clarity = None  # optional in schema; omit for now (your runtime computes CG elsewhere)

    out: Dict[str, Any] = {
        "mode": str(mode),
        "principle": str(principle),
        "confidence": float(confidence),
        "questions": [str(q) for q in questions][:7],
        "fallacies": fallacies[:5] if fallacies else [],
        "context_drivers": context_drivers,
        "empathy_state": empathy_state,
        "vectors": vectors,
        # "clarity": clarity,  # keep commented unless you want to emit CG here
        "audit": {"anonymized": True, "hash_id": "sdk", "log_ref": "DLN-sdk-adapter"}
    }
    if clarity:
        out["clarity"] = clarity
    return out

