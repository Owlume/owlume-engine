"""
Backward-compatible façade.

Stage 11 canonical intervention selection lives in:
    src/frame_audit/intervention_policy.py
"""
from .intervention_policy import rank_interventions, select_primary_intervention

__all__ = ["select_primary_intervention", "rank_interventions"]

