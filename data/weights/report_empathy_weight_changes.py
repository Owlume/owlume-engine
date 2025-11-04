#!/usr/bin/env python3
"""
Owlume — Empathy Weights Diff Reporter (v0.1 pack format)

Compares two v0.1 empathy_weights.json files (arrays of moves) and reports:
- New cells created (Mode × Principle)
- New moves added (by move_id)
- Score changes per move (sorted by absolute delta)
- n / mean changes (optional summary)

Usage:
  python -u scripts/report_empathy_weight_changes.py \
    --before data/weights/empathy_weights_backup.json \
    --after  data/weights/empathy_weights.json \
    [--top 20] [--min_delta 0.0]

Tip: Make a quick snapshot BEFORE you run the learner:
  copy data\\weights\\empathy_weights.json data\\weights\\empathy_weights_backup.json
"""

import argparse, json
from typing import Dict, Tuple, List

def load_moves(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    arr = data.get("weights", [])
    if not isinstance(arr, list):
        raise ValueError(f"{path} does not look like a v0.1 weights pack (weights must be an array)")
    return arr

def key(move: dict) -> Tuple[str, str, str]:
    return (str(move.get("mode","")), str(move.get("principle","")), str(move.get("move_id","")))

def cell(move: dict) -> str:
    return f"{move.get('mode','')} × {move.get('principle','')}"

def index_by_key(moves: List[dict]) -> Dict[Tuple[str,str,str], dict]:
    return { key(m): m for m in moves }

def collect_cells(moves: List[dict]) -> set:
    return { (m.get("mode",""), m.get("principle","")) for m in moves }

def fmt(x, nd=6):
    return f"{x:.{nd}f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--top", type=int, default=20, help="Show top-N score deltas")
    ap.add_argument("--min_delta", type=float, default=0.0, help="Only list changes with |delta| >= this")
    args = ap.parse_args()

    before = load_moves(args.before)
    after  = load_moves(args.after)

    idx_b = index_by_key(before)
    idx_a = index_by_key(after)

    cells_b = collect_cells(before)
    cells_a = collect_cells(after)

    # 1) New cells
    new_cells = sorted(cells_a - cells_b)
    if new_cells:
        print("NEW CELLS CREATED:")
        for (mode, principle) in new_cells:
            print(f"  - {mode} × {principle}")
        print()
    else:
        print("No new cells.\n")

    # 2) New moves
    new_moves = sorted([k for k in idx_a.keys() if k not in idx_b])
    if new_moves:
        print("NEW MOVES ADDED:")
        for (mode, principle, move_id) in new_moves:
            print(f"  - {move_id} @ {mode} × {principle}")
        print()
    else:
        print("No new moves.\n")

    # 3) Score changes for existing moves
    changes = []
    for k in idx_a.keys():
        a = idx_a[k]
        b = idx_b.get(k)
        if not b:
            continue
        s0 = float(b.get("score", 0.0))
        s1 = float(a.get("score", 0.0))
        d  = s1 - s0
        if abs(d) >= args.min_delta:
            changes.append((abs(d), d, s0, s1, a.get("move_id",""), cell(a)))

    changes.sort(reverse=True, key=lambda t: t[0])

    if changes:
        print(f"SCORE CHANGES (|delta| >= {args.min_delta}):")
        for i, (ad, d, s0, s1, move_id, cell_name) in enumerate(changes[:args.top], 1):
            sign = "+" if d >= 0 else "−"
            print(f"{i:>2}. {cell_name} • {move_id}: {fmt(s0)} → {fmt(s1)}  ({sign}{fmt(abs(d))})")
        print()
    else:
        print("No score changes meeting the threshold.\n")

    # 4) Optional: summary of n/mean changes per cell
    # (useful to see where learning evidence accumulated)
    summary = {}
    for k in idx_a.keys():
        a = idx_a[k]
        b = idx_b.get(k)
        if not b:
            continue
        c = cell(a)
        summary.setdefault(c, {"dn":0, "dmean":0.0, "count":0})
        summary[c]["dn"]    += int(a.get("n",0)) - int(b.get("n",0))
        summary[c]["dmean"] += float(a.get("mean",0.0)) - float(b.get("mean",0.0))
        summary[c]["count"] += 1

    if summary:
        print("EVIDENCE ACCUMULATION SUMMARY (Δn, avg Δmean) per cell:")
        for c, agg in summary.items():
            avg_dmean = (agg["dmean"] / max(1, agg["count"]))
            print(f"  - {c}: Δn={agg['dn']}, avg Δmean={fmt(avg_dmean)}")
    else:
        print("No overlapping cells to summarize.")

if __name__ == "__main__":
    main()
