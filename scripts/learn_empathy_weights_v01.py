#!/usr/bin/env python3
"""
Owlume — L4 T-3 Adaptive Empathy Weights Learner (v0.1 pack format)
Auto-creates moves for unseen Mode × Principle cells based on existing move_id templates.

INPUTS
  --logs     JSONL of clarity sessions (one JSON per line)
  --weights  v0.1 empathy_weights.json (array under "weights")
  --out      path to write updated v0.1 weights (can equal --weights)
  --no_timestamp  (optional) do not write updated_at (use if your schema forbids it)
  --learning_rate, --clip_lo, --clip_hi (optional tuning)

BEHAVIOR
- Δ = η * cg_delta * E_strength * eligibility  (distributed equally across moves in the cell)
- Maintains running stats (n, mean, m2) on effective_delta = cg_delta * E_strength
- 95% CI via mean ± 1.96 * SE (Welford; n>1)
- If a cell is missing, auto-creates moves using the set of move_id's already present in the pack.

SCHEMA COMPAT
- Keeps your v0.1 structure: weights: [ { move_id, mode, principle, score, n, mean, m2, ci_low, ci_high }, ... ]
- Preserves $schema and spec fields.
"""

import argparse, json, os, sys, math, datetime
from typing import Dict, Any, Iterable, List, Tuple, Set

DEFAULT_RULES = {
    "learning_rate": 0.05,
    "clip": [-0.75, 0.75],
    "elig_floor": 0.0,
    "cg_epsilon": 0.0,
}

def read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def extract_empathy(rec: Dict[str, Any]) -> Tuple[float, bool]:
    # Returns (strength in [0,1], active)
    active = False
    strength = 0.0
    es = rec.get("empathy_state")
    if isinstance(es, str):
        active = es.upper() == "ON"
    elif isinstance(es, dict):
        active = bool(es.get("active", es.get("on", False)))
        if "strength" in es:
            try: strength = float(es["strength"])
            except: pass

    ef = rec.get("empathy_feedback") or {}
    if isinstance(ef, dict):
        if "strength" in ef:
            try: strength = max(strength, float(ef["strength"]))
            except: pass
        if "rating" in ef:
            try:
                r = float(ef["rating"])
                if r > 1.0: r = (r - 1.0) / 4.0  # map 1..5 → 0..1
                strength = max(strength, r)
            except: pass
        if ef.get("helpful") is True:
            strength = max(strength, 0.6)
        elif ef.get("helpful") is False:
            strength = min(strength, 0.2)

    strength = max(0.0, min(1.0, strength))
    if not active:
        strength = 0.0
    return strength, active

def cell_key(mode: str, principle: str) -> str:
    return f"{mode} × {principle}"

def welford_update(n: int, mean: float, m2: float, x: float) -> Tuple[int, float, float]:
    n_new = n + 1
    delta = x - mean
    mean_new = mean + delta / max(1, n_new)
    m2_new = m2 + delta * (x - mean_new)
    return n_new, mean_new, m2_new

def ci95(mean: float, n: int, m2: float) -> Tuple[float, float]:
    if n <= 1:
        return (mean, mean)
    var = m2 / (n - 1)
    se = math.sqrt(max(0.0, var)) / math.sqrt(n)
    margin = 1.96 * se
    return (mean - margin, mean + margin)

def load_weights_v01(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "weights" not in data or not isinstance(data["weights"], list):
        raise ValueError("weights pack must have a 'weights' array (v0.1)")
    return data

def index_moves_by_cell(weights_arr: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    idx = {}
    for i, move in enumerate(weights_arr):
        mode = str(move.get("mode", "Unknown"))
        principle = str(move.get("principle", "Unknown"))
        cell = cell_key(mode, principle)
        idx.setdefault(cell, []).append(i)
    return idx

def collect_move_ids(weights_arr: List[Dict[str, Any]]) -> List[str]:
    """Return stable list of unique move_id values already present in the pack."""
    seen: Set[str] = set()
    order: List[str] = []
    for move in weights_arr:
        mid = str(move.get("move_id", "E_AUTO"))
        if mid not in seen:
            seen.add(mid)
            order.append(mid)
    if not order:
        order = ["E_AUTO"]
    return order

def make_move_template(move_id: str, mode: str, principle: str) -> Dict[str, Any]:
    return {
        "move_id": move_id,
        "mode": mode,
        "principle": principle,
        "score": 0.0,
        "n": 0,
        "mean": 0.0,
        "m2": 0.0,
        "ci_low": 0.0,
        "ci_high": 0.0
    }

def ensure_cell_moves(weights_arr: List[Dict[str, Any]],
                      idx: Dict[str, List[int]],
                      move_ids: List[str],
                      mode: str,
                      principle: str) -> List[int]:
    """
    Ensure the pack contains moves for (mode, principle).
    If missing, create one move per existing move_id template.
    Return the indices of moves for this cell.
    """
    cell = cell_key(mode, principle)
    if cell in idx and idx[cell]:
        return idx[cell]

    # Create moves
    start_len = len(weights_arr)
    for mid in move_ids:
        weights_arr.append(make_move_template(mid, mode, principle))
    # Update index
    new_idxs = list(range(start_len, len(weights_arr)))
    idx[cell] = new_idxs
    return new_idxs

def apply_updates(
    weights_arr: List[Dict[str, Any]],
    records: Iterable[Dict[str, Any]],
    rules: Dict[str, Any]
) -> int:
    lr = float(rules.get("learning_rate", DEFAULT_RULES["learning_rate"]))
    clip_lo, clip_hi = rules.get("clip", DEFAULT_RULES["clip"])
    elig_floor = float(rules.get("elig_floor", DEFAULT_RULES["elig_floor"]))
    cg_eps = float(rules.get("cg_epsilon", DEFAULT_RULES["cg_epsilon"]))

    idx = index_moves_by_cell(weights_arr)
    move_ids_template = collect_move_ids(weights_arr)
    changed = 0

    for rec in records:
        try:
            cg_delta = float(rec.get("cg_delta", rec.get("CG_delta", 0.0)))
        except Exception:
            cg_delta = 0.0
        if abs(cg_delta) < cg_eps:
            continue

        e_strength, active = extract_empathy(rec)
        if e_strength <= 0.0:
            continue

        mode = str(rec.get("mode_detected") or rec.get("mode") or "Unknown")
        principle = str(rec.get("principle_detected") or rec.get("principle") or "Unknown")
        elig = max(1.0, float(elig_floor))  # all-or-nothing for v0.1

        # Ensure the cell exists; create if missing
        move_idxs = ensure_cell_moves(weights_arr, idx, move_ids_template, mode, principle)

        # Distribute the update equally across moves in this cell
        step_total = lr * cg_delta * e_strength * elig
        step_each = step_total / max(1, len(move_idxs))

        # Track stats on effective_delta
        x = cg_delta * e_strength

        for i in move_idxs:
            move = weights_arr[i]
            score = float(move.get("score", 0.0))
            score = min(clip_hi, max(clip_lo, score + step_each))
            move["score"] = score

            # Running stats
            n = int(move.get("n", 0))
            mean = float(move.get("mean", 0.0))
            m2 = float(move.get("m2", 0.0))
            n, mean, m2 = welford_update(n, mean, m2, x)
            move["n"] = n
            move["mean"] = mean
            move["m2"] = m2
            low, high = ci95(mean, n, m2)
            move["ci_low"] = low
            move["ci_high"] = high

            changed += 1

    return changed

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--logs", required=True)
    p.add_argument("--weights", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--no_timestamp", action="store_true")
    # Optional light tuning without changing code
    p.add_argument("--learning_rate", type=float, default=DEFAULT_RULES["learning_rate"])
    p.add_argument("--clip_lo", type=float, default=DEFAULT_RULES["clip"][0])
    p.add_argument("--clip_hi", type=float, default=DEFAULT_RULES["clip"][1])
    return p.parse_args()

def main():
    args = parse_args()

    pack = load_weights_v01(args.weights)
    weights_arr = pack.get("weights", [])

    # Allow quick tuning from CLI
    rules = {
        "learning_rate": args.learning_rate,
        "clip": [args.clip_lo, args.clip_hi],
        "elig_floor": DEFAULT_RULES["elig_floor"],
        "cg_epsilon": DEFAULT_RULES["cg_epsilon"],
    }

    records = list(read_jsonl(args.logs))
    changed = apply_updates(weights_arr, records, rules)

    # Update timestamp unless forbidden (timezone-aware; Python 3.12-safe)
    if not args.no_timestamp:
        pack["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    elif "updated_at" in pack:
        del pack["updated_at"]

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False, indent=2)

    print(f"[T-3 v0.1] processed_records={len(records)} moves_updated={changed}")
    print(f"[T-3 v0.1] saved → {args.out}")

if __name__ == "__main__":
    main()
