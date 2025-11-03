"""
Bias Insight Card generator (optional).
Emits a tiny dict when |cosine_delta| exceeds threshold.
"""
from __future__ import annotations
from typing import Dict
from .bias_vector import cosine

def render_bias_insight(prev: Dict[str,float], new: Dict[str,float], did: str, threshold: float = 0.15) -> Dict | None:
    delta = 1.0 - max(-1.0, min(1.0, cosine(prev, new)))
    if delta < threshold:
        return None
    # Find top movers
    movers = sorted(((k, abs(new.get(k,0.0)-prev.get(k,0.0))) for k in new.keys()), key=lambda x: x[1], reverse=True)[:3]
    summary = ", ".join(f"{k} (Δ={v:.2f})" for k,v in movers)
    return {
        "type": "BIAS_INSIGHT",
        "did": did,
        "summary": f"Your bias signature shifted: {summary}",
        "movers": movers,
        "delta": round(delta, 3)
    }
