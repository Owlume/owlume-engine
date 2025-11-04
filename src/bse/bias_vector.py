"""
EMA updates for per-user bias vector + cosine delta.
"""
from __future__ import annotations
from typing import Dict
import math
import json
from datetime import datetime, timezone

BUCKETS = ["evidence","agency","risk","conflict","identity","ambiguity","fallacy","context","empathy"]

def l2_norm(vec: Dict[str, float]) -> float:
    return math.sqrt(sum(float(vec.get(k,0.0))**2 for k in BUCKETS))

def cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    num = sum(float(a.get(k,0.0))*float(b.get(k,0.0)) for k in BUCKETS)
    den = (l2_norm(a) * l2_norm(b)) or 1e-9
    return max(-1.0, min(1.0, num/den))

def ema_update(prev: Dict[str, float], signal: Dict[str, float], alpha: float) -> Dict[str, float]:
    out = {}
    for k in BUCKETS:
        out[k] = alpha*float(signal.get(k,0.0)) + (1.0-alpha)*float(prev.get(k,0.0))
    return out

def empty_vector() -> Dict[str, float]:
    return {k: 0.0 for k in BUCKETS}

def snapshot(user: str, vec: Dict[str, float], alpha: float, source: str = "runtime", did: str | None = None, delta_cosine: float | None = None) -> Dict:
    snap = {
        "$schema": "https://owlume/schemas/bias_signature.schema.json",
        "user": user,
        "spec": {"version": "v0.1", "alpha": alpha},
        "vector": vec,
        "norm": l2_norm(vec),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "meta": {"source": source}
    }
    if did: snap["meta"]["did"] = did
    if delta_cosine is not None: snap["meta"]["delta_cosine"] = delta_cosine
    return snap

def save_jsonl(path: str, rec: Dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
