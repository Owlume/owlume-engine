# src/pick_signal.py
from typing import List

# Simple, transparent mapping; you already have /data/proof_of_clarity_signals.json
# In T3, you’ll load weights & patterns. For T2, thresholds only.

def pick_delta_signals(cg_delta: float) -> List[str]:
    # Naive but useful: scale signals with delta
    if cg_delta >= 0.40:
        return ["Δ-Insight", "Pattern Reversal", "Perspective Shift"]
    if cg_delta >= 0.25:
        return ["Δ-Insight", "Perspective Shift"]
    if cg_delta >= 0.10:
        return ["Δ-Insight"]
    return []

def pick_insight_signals(text_before: str, text_after: str) -> List[str]:
    # Placeholder: T3 wires real NLP here. Keep a stub so schema stays consistent.
    return []
