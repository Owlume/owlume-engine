"""
Extract a normalized bias signal vector (0..1 per bucket) from a reflection.
Input: reflection dict with optional diagnostics from elenx_engine:
  {
    "user": "local",
    "did": "DID-xxx",
    "timestamp": "...",
    "text": "...",                       # optional (not persisted by BSE)
    "cg_delta": 0.25,                    # from DilemmaNet event
    "diagnostics": {
        "fallacy_hits": ["F-FALSEDICH-1"],
        "context_hits": ["INCENTIVE-01"],
        "ambiguity_score": 0.6,          # 0..1
        "certainty_delta": -0.2          # -1..1 (positive => more certain)
    },
    "empathy_state": {"active": true}    # optional
  }
Output: {"evidence":x, "agency":x, ... "empathy":x}  all in [0,1]
"""
from __future__ import annotations
from typing import Dict, Any
import json
import os

DEFAULT_BUCKETS = ["evidence","agency","risk","conflict","identity","ambiguity","fallacy","context","empathy"]

def _clip01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x

def _bool01(flag: bool) -> float:
    return 1.0 if flag else 0.0

def _safe_get(d: Dict[str, Any], path: str, default=None):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

def extract_signals(reflection: Dict[str, Any]) -> Dict[str, float]:
    diag = reflection.get("diagnostics", {}) or {}
    cg_delta = reflection.get("cg_delta", 0.0) or 0.0

    # Heuristics (lightweight & replaceable later)
    fallacy_hits = diag.get("fallacy_hits", []) or []
    context_hits = diag.get("context_hits", []) or []
    ambiguity = float(diag.get("ambiguity_score", 0.0) or 0.0)         # 0..1
    certainty_delta = float(diag.get("certainty_delta", 0.0) or 0.0)   # -1..1
    empathy_active = bool(_safe_get(reflection, "empathy_state.active", False))

    # Map to buckets
    signals = {
        "evidence":  _clip01(max(0.0, 0.5 + cg_delta)),          # more clarity gain => stronger evidence discipline
        "agency":    _clip01(0.5 + certainty_delta/2.0),         # rising certainty => stronger agency
        "risk":      _clip01(0.4 + (1.0 - abs(certainty_delta))/2.0), # extreme certainty shifts imply risk myopia
        "conflict":  _clip01(0.3 + (len(context_hits) > 0)*0.4), # any context pressure present
        "identity":  _clip01(0.2 + (len(context_hits) >= 2)*0.5),# multiple context hits often identity-protective
        "ambiguity": _clip01(ambiguity),                          # direct
        "fallacy":   _clip01(min(1.0, 0.3 + 0.2*len(fallacy_hits))),
        "context":   _clip01(min(1.0, 0.2 + 0.2*len(context_hits))),
        "empathy":   _clip01(0.3 + 0.4*_bool01(empathy_active))
    }

    # Ensure all buckets exist
    for b in DEFAULT_BUCKETS:
        signals.setdefault(b, 0.0)

    return signals

def load_weights(path: str) -> Dict[str, float]:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg["weights"]
