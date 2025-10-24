#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, glob, json, math, os, sys, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "metrics"
SCHEMAS = ROOT / "schemas"
LEARNED = DATA / "learned_weights.json"

# ---------- Tunables (keep simple & visible) ----------
ALPHA = 0.20         # EWMA learning rate (0.1–0.35 sensible)
CLAMP = (0.90, 1.60)   # Hard bounds for weights
MIN_CHANGE = 0.02    # Skip commit if max change below this
EMPATHY_GAIN = 0.50   # How much Δ influences empathy multiplier
EMPATHY_RATE_SWEET = (0.15, 0.35)  # target activation band
SOFTMAX_TEMPERATURE = 0.25         # lower → more peaky normalization

# ---------- Label hygiene ----------
ALLOWED_MODES = {"Analytical", "Critical", "Creative", "Reflective", "Growth"}

PRINCIPLE_ALIASES = {
    "-": None,
    "Evidence": "Evidence & Validation",
    "Clarity": "Evidence & Validation",
    "Stakeholders": "Stakeholder",
    # add more synonyms here if your logs produce them:
    "RootCause": "Root Cause",
    "Action": "Evidence & Validation",
    "Evidence & Validation": "Evidence & Validation",  # idempotent
}

def _alias_principle(name: str) -> str | None:
    if name is None:
        return None
    return PRINCIPLE_ALIASES.get(name, name)

def _sanitize_counts(counts: dict, *, kind: str) -> dict:
    """Drop placeholders and normalize labels."""
    out = {}
    if not isinstance(counts, dict):
        return out
    for k, v in counts.items():
        if not k or k == "-":
            continue
        if kind == "mode":
            if k in ALLOWED_MODES:
                out[k] = out.get(k, 0) + int(v)
        else:  # principle
            norm = _alias_principle(k)
            if norm:
                out[norm] = out.get(norm, 0) + int(v)
    return out

# ---------- Helpers ----------
def softmax_norm(weights: dict, temperature: float) -> dict:
    # Normalize to mean≈1 while preserving relative ratios via tempered softmax
    keys = list(weights.keys())
    vals = [weights[k] for k in keys]
    m = sum(vals) / max(1, len(vals))
    centered = [v / (m if m else 1.0) for v in vals]
    exps = [math.exp(v / max(1e-6, temperature)) for v in centered]
    s = sum(exps)
    norm = [e / s for e in exps]
    # rescale so average = 1.0
    scale = len(norm)
    scaled = [n * scale for n in norm]
    return {k: v for k, v in zip(keys, scaled)}

def clamp(v, lo, hi): return max(lo, min(hi, v))

def latest_aggregate_file():
    cand = sorted(DATA.glob("aggregates_*.json"))
    return cand[-1] if cand else None

def load_json(p): 
    with open(p, "r", encoding="utf-8") as f: 
        return json.load(f)

def save_json(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def roundish(d):
    return {k: (round(v, 4) if isinstance(v, (int,float)) else v) for k, v in d.items()}

# ---------- Signal extraction ----------
def extract_signals(agg):
    """Extract usable learning signals from an aggregate file."""
    # start from a clean signals dict
    signals = {}

    # pull top_counts safely
    tc = agg.get("top_counts", {})
    signals["top_counts"] = {
        "mode": _sanitize_counts(tc.get("mode", {}), kind="mode"),
        "principle": _sanitize_counts(tc.get("principle", {}), kind="principle"),
    }

    # copy basic stats
    signals["avg_delta"] = agg.get("avg_delta", 0)
    signals["n_records"] = agg.get("n_records", 0)
    signals["empathy_rate"] = agg.get("empathy_rate", 0)

    return signals
    
    # Expect keys from your existing aggregator
    avg_pre = agg.get("avg_pre", 0.0)
    avg_post = agg.get("avg_post", 0.0)
    avg_delta = agg.get("avg_delta", agg.get("AVG_delta", 0.0))  # aliases
    empathy_rate = agg.get("empathy_activation_rate", agg.get("empathy_rate", 0.0))
    top_counts = agg.get("top_mode_principle_counts", {})
    n_records = agg.get("n_records", agg.get("count", 0))
    return {
        "avg_pre": avg_pre,
        "avg_post": avg_post,
        "avg_delta": avg_delta,
        "empathy_rate": empathy_rate,
        "top_counts": top_counts,
        "n_records": n_records
    }

# ---------- Update logic ----------
def ewma(prev, signal, alpha=ALPHA):
    return (1 - alpha) * prev + alpha * signal

def update_block(prev_block: dict, signals: dict, keyspace: set, name: str):
    """
    Produce a new weight dict for 'mode' or 'principle' by nudging prior weights
    toward recent performance, with a neutral base of 1.0 for unseen keys and
    hard clamps via CLAMP.
    """
    lo, hi = CLAMP

    # counts come from signals["top_counts"]["mode" | "principle"]
    counts = ((signals.get("top_counts", {}) or {}).get(name, {}) or {})

    # compute a mean count to form a simple relative performance proxy
    ks = sorted(keyspace) if keyspace else sorted(prev_block.keys())
    if not ks:
        ks = sorted(counts.keys())

    total = sum(float(counts.get(k, 0.0)) for k in ks)
    mean = (total / max(1, len(ks))) if ks else 0.0

    avg_delta = float(signals.get("avg_delta", 0.0))
    avg_delta = max(0.0, avg_delta)  # only reward positive movement

    new: dict = {}
    for k in ks:
        prev = float(prev_block.get(k, 1.0))  # neutral default for unseen keys
        c = float(counts.get(k, 0.0))
        rel = (c / mean) if mean > 0 else 1.0  # relative frequency vs mean
        # performance proxy: higher than 1.0 ⇒ above average
        perf = rel * (1.0 + avg_delta)

        # multiplicative nudge toward performance; ALPHA governs strength
        mult = 1.0 + ALPHA * (perf - 1.0)
        proposed = prev * mult

        # hard clamp and round for stability
        val = max(lo, min(hi, proposed))
        new[k] = round(val, 4)

    return new

def update_empathy(prev_emp: dict, signals: dict):
    bias = prev_emp.get("bias", 0.0)
    mult = prev_emp.get("multiplier", 1.0)

    # If avg clarity Δ is positive, nudge multiplier up; negative → down
    mult_signal = 1.0 + EMPATHY_GAIN * signals["avg_delta"]
    mult_new = clamp(ewma(mult, mult_signal), 0.6, 1.6)

    # Keep activation rate inside sweet band by bias nudging
    lo, hi = EMPATHY_RATE_SWEET
    rate = signals["empathy_rate"]
    if rate < lo: bias_new = clamp(ewma(bias, +0.2), -1.0, +1.0)
    elif rate > hi: bias_new = clamp(ewma(bias, -0.2), -1.0, +1.0)
    else: bias_new = ewma(bias, 0.0)

    return {"bias": round(bias_new, 4), "multiplier": round(mult_new, 4)}

def detect_keyspace_from_learned(learned, signals=None):
    """Union of learned + (sanitized) aggregate keys; modes restricted to ALLOWED_MODES."""
    # learned
    modes = set(learned.get("weights", {}).get("mode", {}).keys()) & ALLOWED_MODES
    # normalize learned principle names too
    learned_principles_raw = set(learned.get("weights", {}).get("principle", {}).keys())
    principles = set(filter(None, (_alias_principle(p) for p in learned_principles_raw)))

    # aggregates (sanitized)
    if signals:
        tc = signals.get("top_counts", {})
        modes |= set(_sanitize_counts(tc.get("mode", {}), kind="mode").keys())
        principles |= set(_sanitize_counts(tc.get("principle", {}), kind="principle").keys())

    return modes, principles

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--aggregate", help="Path to a specific aggregates_*.json")
    args = parser.parse_args()

    agg_file = Path(args.aggregate) if args.aggregate else latest_aggregate_file()
    if not agg_file or not agg_file.exists():
        print("[L1] No aggregates file found. Run scripts/aggregate_metrics.py first.")
        return 0

    learned = load_json(LEARNED) if LEARNED.exists() else {
        "spec": {"version": "1.0", "updated_utc": "1970-01-01T00:00:00Z"},
        "weights": {"mode": {}, "principle": {}, "empathy": {"bias": 0.0, "multiplier": 1.0}},
        "history": []
    }
    # ensure sub-objects exist
    learned.setdefault("weights", {})
    learned["weights"].setdefault("mode", {})
    learned["weights"].setdefault("principle", {})
    learned["weights"].setdefault("empathy", {"bias": 0.0, "multiplier": 1.0})

    agg = load_json(agg_file)
    signals = extract_signals(agg)
    modes, principles = detect_keyspace_from_learned(learned, signals)

    new_mode = update_block(learned["weights"]["mode"], signals, modes, "mode")
    new_prin = update_block(learned["weights"]["principle"], signals, principles, "principle")
    new_emp = update_empathy(learned["weights"]["empathy"], signals)

    # ensure final keysets are clean
    new_mode = {k: v for k, v in new_mode.items() if k in ALLOWED_MODES}
    new_prin = {k: v for k, v in new_prin.items() if _alias_principle(k)}
    # also normalize principle keys in learned before writing (merge if aliases collapse)
    collapsed_prin = {}
    for k, v in new_prin.items():
        nk = _alias_principle(k)
        if nk:
            collapsed_prin[nk] = max(collapsed_prin.get(nk, 0.0), v)  # or += if you prefer
    new_prin = collapsed_prin

    # Compute deltas to decide if worth committing
    deltas_mode = {k: new_mode[k] - learned["weights"]["mode"].get(k, 1.0) for k in new_mode}
    deltas_prin = {k: new_prin[k] - learned["weights"]["principle"].get(k, 1.0) for k in new_prin}
    delta_emp = {
        "bias": new_emp["bias"] - learned["weights"]["empathy"].get("bias", 0.0),
        "multiplier": new_emp["multiplier"] - learned["weights"]["empathy"].get("multiplier", 1.0)
    }
    max_change = max(
        [abs(v) for v in deltas_mode.values()] + 
        [abs(v) for v in deltas_prin.values()] + 
        [abs(delta_emp["bias"]), abs(delta_emp["multiplier"])]
    ) if (deltas_mode or deltas_prin) else 0.0

    # Update learned
    learned["weights"]["mode"] = roundish(new_mode)
    learned["weights"]["principle"] = roundish(new_prin)
    learned["weights"]["empathy"] = new_emp
    learned["spec"]["updated_utc"] = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    learned.setdefault("history", []).append({
        "timestamp_utc": learned["spec"]["updated_utc"],
        "source": agg_file.name,
        "deltas": {
            "mode": roundish(deltas_mode),
            "principle": roundish(deltas_prin),
            "empathy": roundish(delta_emp)
        },
        "stats": {
            "avg_delta": round(signals["avg_delta"], 4),
            "n_records": int(signals["n_records"]),
            "empathy_rate": round(signals["empathy_rate"], 4)
        }
    })

    if args.dry_run:
        print("[L1] Dry run. Proposed updates (max change = %.4f):" % max_change)
        print(json.dumps(learned, indent=2))
        return 0

    if max_change < MIN_CHANGE:
        print(f"[L1] Skipping write: max change {max_change:.4f} < threshold {MIN_CHANGE:.2f}")
        return 0

    save_json(LEARNED, learned)
    print(f"[L1] Updated learned weights → {LEARNED}")
    print(f"[L1] Max change: {max_change:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
