#!/usr/bin/env python3
"""
Owlume — T-3 Adaptive Empathy Weights Learner

Usage:
  python -u scripts/learn_empathy_weights.py \
    --logs data/logs/clarity_gain_samples.jsonl \
    --weights data/weights/empathy_weights.json \
    --out data/weights/empathy_weights.json \
    --dry_run  # optional, prints a summary without writing

What it does:
- Reads Clarity Gain records (JSONL).
- Computes incremental updates to empathy weights per Mode × Principle cell.
- Preserves `adaptive_rules` from the weights file; writes updated weights back.
- Compatible with:
  v0.1  empathy_state: "ON"/"OFF"
  v0.2  empathy_state: { active: bool, strength?: float, ... }
  v0.2+ empathy_feedback: { strength?: float, rating?: float, helpful?: bool, notes?: str }

Schema-friendly:
- Requires `adaptive_rules` at top level.
- Writes only: { "spec", "adaptive_rules", "weights" }.
"""

import argparse, json, os, sys
from collections import defaultdict
from typing import Dict, Tuple, Any, Iterable

# ---------- Defaults (safe starting points) ----------
DEFAULT_SPEC = "owlume/empathy-weights:v0.2"

DEFAULT_RULES = {
    # Base learning rate (η)
    "learning_rate": 0.05,
    # Optional per-update multiplicative decay applied after each batch (close to 1.0)
    "decay": 1.0,
    # Clip weights into [min, max] after each update to avoid runaway growth
    "clip": [-0.75, 0.75],
    # Minimum eligibility (if you wish to damp weak activations)
    "elig_floor": 0.0,
    # Ignore updates if absolute cg_delta is too tiny (noise filter)
    "cg_epsilon": 0.0
}

# ---------- Helpers ----------
def make_cell(mode: str, principle: str) -> str:
    return f"{mode} × {principle}"

def is_truthy(x: Any) -> bool:
    return bool(x) and str(x).lower() not in {"false", "0", "off", "none", "null"}

def read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                # Skip malformed lines but continue processing
                continue

def load_weights(path: str) -> Tuple[Dict[str, float], Dict[str, Any], str]:
    if not os.path.exists(path):
        # create a minimal pack from scratch
        return {}, DEFAULT_RULES.copy(), DEFAULT_SPEC
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    spec = data.get("spec", DEFAULT_SPEC)
    rules = data.get("adaptive_rules", {}).copy()
    if not rules:
        # If missing, fall back to defaults (stays schema-compliant)
        rules = DEFAULT_RULES.copy()

    weights = data.get("weights", {}).copy()
    # Ensure float
    for k, v in list(weights.items()):
        try:
            weights[k] = float(v)
        except Exception:
            weights[k] = 0.0
    return weights, rules, spec

def save_weights(path: str, spec: str, rules: Dict[str, Any], weights: Dict[str, float]) -> None:
    out = {
        "spec": spec or DEFAULT_SPEC,
        "adaptive_rules": rules,
        "weights": {k: float(v) for k, v in sorted(weights.items())},
    }
    # IMPORTANT: do not include extraneous fields (e.g., updated_at) to avoid schema errors
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

def extract_empathy_feedback(rec: Dict[str, Any]) -> Tuple[float, bool]:
    """
    Returns:
      (feedback_strength in [0,1], empathy_active: bool)

    Compatible with:
      - empathy_state: "ON"/"OFF"
      - empathy_state: { active: bool, strength?: float }
      - empathy_feedback: { strength?: float, rating?: float in [0,1] or [1..5], helpful?: bool }
    """
    empathy_active = False
    strength = 0.0

    # 1) empathy_state (legacy or object)
    es = rec.get("empathy_state")
    if isinstance(es, str):
        empathy_active = es.upper() == "ON"
    elif isinstance(es, dict):
        empathy_active = bool(es.get("active", es.get("on", False)))
        strength = max(0.0, min(1.0, float(es.get("strength", strength))))  # optional

    # 2) empathy_feedback object
    ef = rec.get("empathy_feedback") or {}
    if isinstance(ef, dict):
        # Prefer explicit strength if present
        if "strength" in ef:
            try:
                strength = float(ef["strength"])
            except Exception:
                pass
        # If rating provided (either 0..1 or 1..5), map to 0..1
        rating = ef.get("rating")
        if rating is not None:
            try:
                r = float(rating)
                if r > 1.0:
                    r = max(0.0, min(1.0, (r - 1.0) / 4.0))  # map 1..5 → 0..1
                strength = max(strength, r)
            except Exception:
                pass
        # If helpful flag provided, nudge strength
        if ef.get("helpful") is True:
            strength = max(strength, 0.6)
        elif ef.get("helpful") is False:
            strength = min(strength, 0.2)

    # Final clamps
    strength = max(0.0, min(1.0, strength))
    # If empathy was not active at all, zero out strength
    if not empathy_active:
        strength = 0.0
    return strength, empathy_active

def get_cell_and_eligibility(rec: Dict[str, Any], elig_floor: float) -> Tuple[str, float]:
    """
    Returns:
      (cell_name, eligibility in [0,1])

    For now: 1.0 eligibility for the detected Mode × Principle.
    If you later carry top-2 predictions, distribute here.
    """
    mode = rec.get("mode_detected") or rec.get("mode") or "Unknown"
    principle = rec.get("principle_detected") or rec.get("principle") or "Unknown"
    cell = make_cell(str(mode), str(principle))
    elig = 1.0
    return cell, max(elig, float(elig_floor))

def sign_clip(x: float, lo: float, hi: float) -> float:
    return min(hi, max(lo, x))

# ---------- Main learner ----------
def apply_updates(
    weights: Dict[str, float],
    records: Iterable[Dict[str, Any]],
    rules: Dict[str, Any]
) -> Dict[str, float]:
    lr = float(rules.get("learning_rate", DEFAULT_RULES["learning_rate"]))
    decay = float(rules.get("decay", DEFAULT_RULES["decay"]))
    clip_lo, clip_hi = rules.get("clip", DEFAULT_RULES["clip"])
    elig_floor = float(rules.get("elig_floor", DEFAULT_RULES["elig_floor"]))
    cg_eps = float(rules.get("cg_epsilon", DEFAULT_RULES["cg_epsilon"]))

    updates = defaultdict(float)
    n_updates = 0

    for rec in records:
        try:
            cg_delta = float(rec.get("cg_delta", rec.get("CG_delta", 0.0)))
        except Exception:
            cg_delta = 0.0
        if abs(cg_delta) < cg_eps:
            continue

        e_strength, e_active = extract_empathy_feedback(rec)
        if e_strength <= 0.0:
            # If empathy inactive or zero strength, no empathy-based learning
            continue

        cell, elig = get_cell_and_eligibility(rec, elig_floor)

        step = lr * cg_delta * e_strength * elig
        updates[cell] += step
        n_updates += 1

    # Apply aggregated updates
    for cell, delta in updates.items():
        weights[cell] = sign_clip(weights.get(cell, 0.0) + delta, clip_lo, clip_hi)

    # Optional global decay (very light by default)
    if decay and decay != 1.0:
        for k in list(weights.keys()):
            weights[k] *= decay
            weights[k] = sign_clip(weights[k], clip_lo, clip_hi)

    return weights

# ---------- CLI ----------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--logs", required=True, help="Path to clarity_gain JSONL")
    p.add_argument("--weights", required=True, help="Path to existing empathy_weights.json")
    p.add_argument("--out", required=True, help="Path to write updated weights (can be same as --weights)")
    p.add_argument("--dry_run", action="store_true", help="Do not write; print summary only")
    return p.parse_args()

def main():
    args = parse_args()

    weights, rules, spec = load_weights(args.weights)
    before = dict(weights)

    records = list(read_jsonl(args.logs))
    weights = apply_updates(weights, records, rules)

    # Summary
    changed = {k: (before.get(k, 0.0), weights.get(k, 0.0)) for k in set(before) | set(weights) if abs(before.get(k,0.0) - weights.get(k,0.0)) > 1e-12}
    print(f"[T-3] processed_records={len(records)} changed_cells={len(changed)}")
    sample = list(sorted(changed.items()))[:12]
    for cell, (w0, w1) in sample:
        print(f"  - {cell}: {w0:.6f} → {w1:.6f}")

    if args.dry_run:
        print("[T-3] dry_run: no file written")
        return

    save_weights(args.out, spec, rules, weights)
    print(f"[T-3] weights saved → {args.out}")

if __name__ == "__main__":
    main()
