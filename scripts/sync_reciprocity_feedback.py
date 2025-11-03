#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S7-S5 — Ecosystem Insight Sync → Reciprocity Feedback Learning

Purpose
-------
Close the adaptive learning loop by consuming reciprocity metrics/events and
projecting them back into Owlume's internal learners:
  • Clarity weights (runtime multipliers) for the Elenx engine
  • Bias Signature Embedding (BSE) vectors (EMA updates)

This is a scaffold/skeleton: wire the TODOs to your actual runtime files
and schema utilities. Keep it small, safe, and observable.

Usage
-----
python -u scripts/sync_reciprocity_feedback.py --once \
    --alpha 0.20 --user local --dry-run

python -u scripts/sync_reciprocity_feedback.py --watch --poll 15 \
    --alpha 0.20 --user local

Notes
-----
• Uses timezone-aware datetimes to avoid utcnow deprecation.
• Writes a lightweight sync event log for transparency.
• If target files don't exist yet, creates runtime variants.

"""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from glob import glob
from typing import Any, Dict, Iterable, List, Optional, Tuple

# -------------------------------
# Config — adjust paths as needed
# -------------------------------
ROOT = Path(__file__).resolve().parents[1]  # repo root assumed: scripts/ -> repo
DATA = ROOT / "data"
LOGS = DATA / "logs"
METRICS = DATA / "metrics"
BSE_DIR = DATA / "bse"
WEIGHTS_DIR = DATA / "weights"
RUNTIME_DIR = DATA / "runtime"
REPORTS_DIR = ROOT / "reports"

# Inputs
RECIPROCITY_EVENTS = LOGS / "reciprocity_events.jsonl"
AGG_BALANCE_GLOB = str(METRICS / "aggregates_balance_*.json")

# Outputs
SYNC_EVENTS = RUNTIME_DIR / "reciprocity_sync_events.jsonl"
RUNTIME_WEIGHTS = WEIGHTS_DIR / "runtime_clarity_weights.json"  # created if missing
BSE_VECTORS = BSE_DIR / "bias_vectors.jsonl"  # append-only log of vectors
BSE_EVENTS = BSE_DIR / "bias_events.jsonl"    # optional: append events for audit
SNAPSHOT = REPORTS_DIR / "S7-S5_sync_snapshot.md"

# -------------------------------
# Helpers
# -------------------------------

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    for p in (LOGS, METRICS, BSE_DIR, WEIGHTS_DIR, RUNTIME_DIR, REPORTS_DIR):
        p.mkdir(parents=True, exist_ok=True)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # Be forgiving in skeleton; log and skip
                print(f"[WARN] bad JSONL line in {path}: {line[:120]}…")
    return out


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_latest_balance() -> Optional[Dict[str, Any]]:
    files = sorted(glob(AGG_BALANCE_GLOB))
    if not files:
        return None

    for path in reversed(files):
        p = Path(path)
        try:
            name = p.name
            if "YYYYMMDD_HHMSS" in name:
                continue  # ignore template stub
            if not p.exists() or p.stat().st_size < 2:
                continue

            raw = p.read_text(encoding="utf-8", errors="ignore").lstrip()
            if not raw or raw[0] not in "[{":
                continue

            data = json.loads(raw)

            # Shape 1: dict with 'vitals' or direct keys
            if isinstance(data, dict):
                return data.get("vitals", data)

            # Shape 2: array
            if isinstance(data, list):
                # Case 2a: list of {label, value} dicts → collapse to a dict
                kv = {}
                had_label_value = False
                for el in data:
                    if isinstance(el, dict) and "label" in el and "value" in el:
                        had_label_value = True
                        kv[str(el["label"])] = el["value"]
                if had_label_value and kv:
                    return kv

                # Case 2b: pick last dict element (best-effort)
                for el in reversed(data):
                    if isinstance(el, dict):
                        return el
                continue

        except Exception as e:
            print(f"[WARN] failed to read {p}: {e}")
            continue

    return None

    # Walk newest→oldest, ignore template/empty/non-JSON files
    for path in reversed(files):
        p = Path(path)
        try:
            name = p.name
            if "YYYYMMDD_HHMSS" in name:
                continue  # ignore template stub
            if not p.exists() or p.stat().st_size < 2:
                continue
            head = p.read_text(encoding="utf-8", errors="ignore").lstrip()[:1]
            if head != "{":
                continue
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print(f"[WARN] failed to read {p}: {e}")
            continue
    return None
    # Walk newest→oldest, ignore template/empty/non-JSON files
    for path in reversed(files):
        p = Path(path)
        try:
            name = p.name
            if "YYYYMMDD_HHMSS" in name:
                continue  # ignore template stub
            if not p.exists() or p.stat().st_size < 2:
                continue
            head = p.read_text(encoding="utf-8", errors="ignore").lstrip()[:1]
            if head != "{":
                continue
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
                # simple sanity: must be a dict with at least one Reciprocity key
                if not isinstance(data, dict):
                    continue
                if not any(k.startswith("Reciprocity ") for k in data.keys()):
                    # still accept but warn
                    print(f"[WARN] balance file {p} has no 'Reciprocity ' keys; using anyway")
                return data
        except Exception as e:
            print(f"[WARN] failed to read {p}: {e}")
            continue
    return None
    # Walk newest→oldest and return the first valid, non-empty JSON file
    for path in reversed(files):
        p = Path(path)
        try:
            if not p.exists() or p.stat().st_size == 0:
                continue
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] failed to read {p}: {e}")
            continue
    return None

# -------------------------------
# Domain: reciprocity → signals
# -------------------------------

def collect_reciprocity_signals(user: str) -> Dict[str, Any]:
    """Summarize recent reciprocity events for a (single) user.

    Expected fields in reciprocity_events.jsonl (loose contract):
      - reciprocity_id, did, learning/outcome, helpfulness, comment
      - clarity_effect (0..1), empathy_response (0..100 or 0..1)
      - usage_context, resulting_action, timestamp

    This function is defensive and will compute safe aggregates when
    fields are missing.
    """
    events = load_jsonl(RECIPROCITY_EVENTS)
    my = [e for e in events if e.get("user", user) == user]
    if not my:
        return {
            "count": 0,
            "avg_clarity_effect": 0.0,
            "avg_empathy_response": 0.0,
            "last_ts": None,
            "by_context": {},
            "by_action": {},
        }

    ce_vals: List[float] = []
    er_vals: List[float] = []
    by_ctx: Dict[str, int] = {}
    by_act: Dict[str, int] = {}
    last_ts: Optional[str] = None

    for e in my:
        try:
            ce = float(e.get("clarity_effect", 0.0))
            er = float(e.get("empathy_response", 0.0))
        except Exception:
            ce, er = 0.0, 0.0
        ce_vals.append(ce)
        er_vals.append(er)
        by_ctx[e.get("usage_context", "UNKNOWN")] = by_ctx.get(e.get("usage_context", "UNKNOWN"), 0) + 1
        by_act[e.get("resulting_action", "UNKNOWN")] = by_act.get(e.get("resulting_action", "UNKNOWN"), 0) + 1
        ts = e.get("timestamp")
        if ts:
            # keep the max lexicographically (ISO8601 safe)
            last_ts = ts if (last_ts is None or ts > last_ts) else last_ts

    avg_ce = sum(ce_vals) / max(1, len(ce_vals))
    avg_er = sum(er_vals) / max(1, len(er_vals))

    return {
        "count": len(my),
        "avg_clarity_effect": round(avg_ce, 6),
        "avg_empathy_response": round(avg_er, 6),
        "last_ts": last_ts,
        "by_context": by_ctx,
        "by_action": by_act,
    }


# -------------------------------
# Projections: weights & BSE
# -------------------------------
def extract_balance_metrics(bal: Any) -> Tuple[Optional[float], Optional[float]]:
    """Flexible extraction from dict or list[{label,value}] or nested 'vitals'."""
    if isinstance(bal, list):
        # Look for {label,value}
        ce = er = None
        for el in bal:
            if isinstance(el, dict) and "label" in el and "value" in el:
                lab = str(el["label"]).lower()
                val = _coerce_float(el["value"], None)
                if val is None:
                    continue
                if ce is None and "clarity" in lab and ("Δ" in el["label"] or "delta" in lab or "change" in lab or "effect" in lab):
                    ce = val
                if er is None and "empathy" in lab:
                    er = val
        return ce, er

    if not isinstance(bal, dict):
        return None, None

    # Search spaces: top-level + optional 'vitals'
    spaces = [bal]
    if isinstance(bal.get("vitals"), dict):
        spaces.append(bal["vitals"])

    # Exact keys first
    ce = er = None
    exact = [
        ("Reciprocity ClarityΔ", "clarity"),
        ("ClarityΔ", "clarity"),
        ("ClarityDelta", "clarity"),
        ("Clarity_Delta", "clarity"),
        ("Reciprocity Empathy", "empathy"),
        ("Empathy", "empathy"),
        ("EmpathyLevel", "empathy"),
        ("Empathy_Response", "empathy"),
    ]
    for sp in spaces:
        for k, kind in exact:
            if k in sp:
                v = _coerce_float(sp[k], None)
                if v is None:
                    continue
                if kind == "clarity" and ce is None:
                    ce = v
                elif kind == "empathy" and er is None:
                    er = v

    # Fuzzy fallback
    if ce is None or er is None:
        for sp in spaces:
            for k, v in sp.items():
                fv = _coerce_float(v, None)
                if fv is None:
                    continue
                kl = str(k).lower()
                if ce is None and ("clarity" in kl) and ("Δ" in k or "delta" in kl or "change" in kl or "effect" in kl):
                    ce = fv
                if er is None and ("empathy" in kl):
                    er = fv

    return ce, er

def _coerce_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def _extract_balance_metrics(bal: Any) -> Tuple[Optional[float], Optional[float]]:
    """Flexible extraction from dict or list[{label,value}] or nested 'vitals'.

    Returns (clarity_delta, empathy_level). Empathy may be None if not present.
    """
    # List of {label,value} support (unchanged)
    if isinstance(bal, list):
        ce = er = None
        for el in bal:
            if isinstance(el, dict) and "label" in el and "value" in el:
                lab = str(el["label"]).lower()
                val = _coerce_float(el["value"])
                if val is None:
                    continue
                if ce is None and "clarity" in lab and ("Δ" in el["label"] or "delta" in lab or "change" in lab or "effect" in lab):
                    ce = val
                if er is None and "empathy" in lab:
                    er = val
        return ce, er

    if not isinstance(bal, dict):
        return None, None

    # Search spaces: top-level + optional 'vitals'
    spaces = [bal]
    if isinstance(bal.get("vitals"), dict):
        spaces.append(bal["vitals"])

    ce = er = None

    # 1) Exact-ish keys as before
    exact = [
        ("Reciprocity ClarityΔ", "clarity"),
        ("ClarityΔ", "clarity"),
        ("ClarityDelta", "clarity"),
        ("Clarity_Delta", "clarity"),
        ("Reciprocity Empathy", "empathy"),
        ("Empathy", "empathy"),
        ("EmpathyLevel", "empathy"),
        ("Empathy_Response", "empathy"),
    ]
    for sp in spaces:
        for k, kind in exact:
            if k in sp:
                v = _coerce_float(sp[k])
                if v is None:
                    continue
                if kind == "clarity" and ce is None:
                    ce = v
                elif kind == "empathy" and er is None:
                    er = v

    # 2) NEW: Owlume Stage-7 keys → map to clarity proxy
    # Prefer 'balance_index' if present; otherwise use 1 - max(drift,tunnel) as a rough clarity proxy.
    if ce is None:
        for sp in spaces:
            if "balance_index" in sp:
                v = _coerce_float(sp["balance_index"])
                if v is not None:
                    ce = v
                    break
        if ce is None:
            for sp in spaces:
                drift = _coerce_float(sp.get("drift_index"))
                tunnel = _coerce_float(sp.get("tunnel_index"))
                if drift is not None or tunnel is not None:
                    # higher drift/tunnel ⇒ lower clarity
                    worst = max(drift or 0.0, tunnel or 0.0)
                    ce = max(0.0, min(1.0, 1.0 - worst))
                    break

        # As a last resort, average depth/breadth if they look like 0..1 or 0..100
        if ce is None:
            for sp in spaces:
                depth = _coerce_float(sp.get("depth_score"))
                breadth = _coerce_float(sp.get("breadth_score"))
                if depth is not None and breadth is not None:
                    # normalize if likely 0..100
                    if depth > 1.0 or breadth > 1.0:
                        depth /= 100.0
                        breadth /= 100.0
                    ce = max(0.0, min(1.0, 0.5 * (depth + breadth)))
                    break

    # 3) Fuzzy empathy (may remain None if not in aggregates)
    if er is None:
        for sp in spaces:
            for k, v in sp.items():
                fv = _coerce_float(v)
                if fv is None:
                    continue
                if "empathy" in str(k).lower():
                    er = fv
                    break

    return ce, er

def load_runtime_weights() -> Dict[str, Any]:
    if not RUNTIME_WEIGHTS.exists():
        return {"$schema": "https://owlume/schemas/runtime_clarity_weights.schema.json", "spec": {"version": "v0.1"}, "multipliers": {"global": 1.0, "empathy": 1.0}}
    with RUNTIME_WEIGHTS.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_runtime_weights(weights: Dict[str, Any]) -> None:
    with RUNTIME_WEIGHTS.open("w", encoding="utf-8") as f:
        json.dump(weights, f, ensure_ascii=False, indent=2)


def derive_weight_updates(signals: Dict[str, Any]) -> Dict[str, float]:
    """
    Translate reciprocity signals → small nudges for weights.

    Preference order:
      1) Use latest balance aggregates if present (flexible shape)
      2) Fall back to event-level averages (avg_clarity_effect / avg_empathy_response)

    Always returns a dict like {"global": float, "empathy": float}.
    """
    def _cf(x, d=None):
        try:
            return float(x)
        except Exception:
            return d

    bal = signals.get("_balance")

    # ---- extract clarity (ce) and empathy (er) robustly ----
    ce = er = None

    # Case A: balance is a list of {label,value}
    if isinstance(bal, list):
        for el in bal:
            if isinstance(el, dict) and "label" in el and "value" in el:
                lab = str(el["label"]).lower()
                val = _cf(el["value"])
                if val is None:
                    continue
                if ce is None and "clarity" in lab and any(t in lab or "Δ" in el["label"] for t in ("delta","change","effect")):
                    ce = val
                if er is None and "empathy" in lab:
                    er = val

    # Case B: balance is a dict (possibly with nested 'vitals')
    elif isinstance(bal, dict):
        spaces = [bal]
        if isinstance(bal.get("vitals"), dict):
            spaces.append(bal["vitals"])

        # exact-ish
        exact = [
            ("Reciprocity ClarityΔ", "clarity"),
            ("ClarityΔ", "clarity"),
            ("ClarityDelta", "clarity"),
            ("Clarity_Delta", "clarity"),
            ("Reciprocity Empathy", "empathy"),
            ("Empathy", "empathy"),
            ("EmpathyLevel", "empathy"),
            ("Empathy_Response", "empathy"),
        ]
        for sp in spaces:
            for k, kind in exact:
                if k in sp:
                    v = _cf(sp[k])
                    if v is None:
                        continue
                    if kind == "clarity" and ce is None:
                        ce = v
                    elif kind == "empathy" and er is None:
                        er = v

        # Stage-7 proxy keys (your current file): balance_index / drift_index / tunnel_index
        if ce is None:
            for sp in spaces:
                v = _cf(sp.get("balance_index"))
                if v is not None:
                    ce = v
                    break
        if ce is None:
            for sp in spaces:
                drift = _cf(sp.get("drift_index"), 0.0)
                tunnel = _cf(sp.get("tunnel_index"), 0.0)
                worst = max(drift or 0.0, tunnel or 0.0)
                ce = max(0.0, min(1.0, 1.0 - worst))
                break

        # Treat missing/zero-signal empathy as None (neutral)
        if er is None or er == 0.0 or signals.get("count", 0) == 0:
            er = None

        # depth/breadth fallback
        if ce is None:
            for sp in spaces:
                depth = _cf(sp.get("depth_score"))
                breadth = _cf(sp.get("breadth_score"))
                if depth is not None and breadth is not None:
                    if depth > 1.0 or breadth > 1.0:
                        depth /= 100.0
                        breadth /= 100.0
                    ce = max(0.0, min(1.0, 0.5 * (depth + breadth)))
                    break

        # fuzzy empathy
        if er is None:
            for sp in spaces:
                for k, v in sp.items():
                    fv = _cf(v)
                    if fv is None:
                        continue
                    if "empathy" in str(k).lower():
                        er = fv
                        break

    # Fallbacks to event-level if still missing
    if ce is None:
        ce = _cf(signals.get("avg_clarity_effect"), 0.0)
    if er is None:
        er = _cf(signals.get("avg_empathy_response"), None)  # empathy may legitimately be absent

    # --- normalize / neutralize empathy ---
    # Treat missing/zero empathy as neutral (no change)
    if er is None or er == 0.0 or signals.get("count", 0) == 0:
        er = None

    # Normalize 0..1 → 0..100 only if we actually have a value
    if er is not None and er <= 1.0:
        er *= 100.0

    # --- nudge rules ---
    nudge_global  = 0.02 if (ce is not None and ce >= 0.25) else (-0.01 if (ce is not None and ce < 0.10) else 0.0)
    nudge_empathy = 0.0 if er is None else (0.02 if er >= 60 else (-0.01 if er < 30 else 0.0))

    return {"global": nudge_global, "empathy": nudge_empathy}


def apply_weight_nudges(nudges: Dict[str, float], dry_run: bool = False) -> Dict[str, Any]:
    weights = load_runtime_weights()
    multipliers = weights.setdefault("multipliers", {})
    before = dict(multipliers)

    for k, dv in nudges.items():
        old = float(multipliers.get(k, 1.0))
        new = round(old + dv, 3)
        # Clamp for safety: keep within 0.8–1.2 range
        new = max(0.8, min(1.2, new))
        multipliers[k] = new

    weights["updated_at"] = utcnow_iso()

    if not dry_run:
        ensure_dirs()
        save_runtime_weights(weights)

    return {"before": before, "after": multipliers}

def apply_weight_nudges(nudges: Dict[str, float], dry_run: bool = False) -> Dict[str, Any]:
    weights = load_runtime_weights()
    multipliers = weights.setdefault("multipliers", {})
    before = dict(multipliers)

    for k, dv in nudges.items():
        old = float(multipliers.get(k, 1.0))
        newv = max(0.50, min(1.50, round(old + dv, 3)))  # clamp for safety
        multipliers[k] = newv

    weights["updated_at"] = utcnow_iso()

    if not dry_run:
        ensure_dirs()
        save_runtime_weights(weights)
        
    return {"before": before, "after": multipliers}


def read_last_bse_vector(user: str) -> Optional[Dict[str, Any]]:
    vecs = load_jsonl(BSE_VECTORS)
    for rec in reversed(vecs):
        if rec.get("user") == user and isinstance(rec.get("vector"), dict):
            return rec
    return None


def derive_bse_delta_from_signals(signals: Dict[str, Any]) -> Dict[str, float]:
    """
    Map reciprocity signals to a light BSE delta.
    Always returns a dict with keys at least: risk, conflict, identity.
    Empathy-absent → identity delta = 0.0 (neutral).
    """
    def _cf(x, d=None):
        try:
            return float(x)
        except Exception:
            return d

    # Prefer balance metrics (any dict/list shape), else event averages
    bal = signals.get("_balance")
    ce = er = None

    # list of {label,value}
    if isinstance(bal, list):
        for el in bal:
            if isinstance(el, dict) and "label" in el and "value" in el:
                lab = str(el["label"]).lower()
                val = _cf(el["value"])
                if val is None:
                    continue
                if ce is None and "clarity" in lab and any(t in lab or "Δ" in el["label"] for t in ("delta","change","effect")):
                    ce = val
                if er is None and "empathy" in lab:
                    er = val

    # dict (optionally with 'vitals')
    elif isinstance(bal, dict):
        spaces = [bal]
        if isinstance(bal.get("vitals"), dict):
            spaces.append(bal["vitals"])

        # exact-ish clarity/empathy
        exact = [
            ("Reciprocity ClarityΔ", "clarity"),
            ("ClarityΔ", "clarity"),
            ("ClarityDelta", "clarity"),
            ("Clarity_Delta", "clarity"),
            ("Reciprocity Empathy", "empathy"),
            ("Empathy", "empathy"),
            ("EmpathyLevel", "empathy"),
            ("Empathy_Response", "empathy"),
        ]
        for sp in spaces:
            for k, kind in exact:
                if k in sp:
                    v = _cf(sp[k])
                    if v is None:
                        continue
                    if kind == "clarity" and ce is None:
                        ce = v
                    elif kind == "empathy" and er is None:
                        er = v

        # Stage-7 keys → clarity proxy
        if ce is None:
            for sp in spaces:
                v = _cf(sp.get("balance_index"))
                if v is not None:
                    ce = v
                    break
        if ce is None:
            for sp in spaces:
                drift = _cf(sp.get("drift_index"), 0.0)
                tunnel = _cf(sp.get("tunnel_index"), 0.0)
                worst = max(drift or 0.0, tunnel or 0.0)
                ce = max(0.0, min(1.0, 1.0 - worst))
                break

    # fallback to event-level if still missing
    if ce is None:
        ce = _cf(signals.get("avg_clarity_effect"), 0.0)
    if er is None:
        er = _cf(signals.get("avg_empathy_response"), None)  # may remain None

    # normalize empathy if 0..1
    if er is not None and er <= 1.0:
        er *= 100.0

    # compute deltas (neutral if metric missing)
    identity_delta = 0.0 if er is None else (-0.04 if er >= 60 else (0.02 if er < 30 else 0.0))
    delta = {
        "risk":    -0.05 if (ce is not None and ce >= 0.25) else (0.02 if (ce is not None and ce < 0.10) else 0.0),
        "conflict":-0.03 if (ce is not None and ce >= 0.25) else (0.01 if (ce is not None and ce < 0.10) else 0.0),
        "identity": identity_delta,
    }
    return delta

def ema_update_bse(user: str, alpha: float, delta: Dict[str, float], dry_run: bool = False) -> Dict[str, Any]:
    """EMA update for Bias Signature Embedding.

    v_new = (1 - alpha) * v_old + alpha * (v_old + delta) = v_old + alpha * delta
    If no prior vector exists, bootstrap with mid-range values and apply delta.
    """
    last = read_last_bse_vector(user)
    if last is None:
        base = {
            "evidence": 0.5, "agency": 0.5, "risk": 0.5, "conflict": 0.5,
            "identity": 0.5, "ambiguity": 0.5, "fallacy": 0.5, "context": 0.5, "empathy": 0.5,
        }
        prev = base
        spec = {"version": "v0.1", "alpha": alpha}
    else:
        prev = dict(last.get("vector", {}))
        spec = last.get("spec", {"version": "v0.1", "alpha": alpha})

    updated = dict(prev)
    for k, dv in delta.items():
        old = float(updated.get(k, 0.5))
        updated[k] = float(min(1.0, max(0.0, old + alpha * dv)))

    record = {
        "$schema": "https://owlume/schemas/bias_signature.schema.json",
        "user": user,
        "spec": {"version": spec.get("version", "v0.1"), "alpha": alpha},
        "vector": updated,
        "ts": utcnow_iso(),
        "_meta": {"source": "S7-S5_sync", "delta": delta},
    }

    if not dry_run:
        ensure_dirs()
        append_jsonl(BSE_VECTORS, record)
        append_jsonl(BSE_EVENTS, {"type": "BSE_EMA_UPDATE", "user": user, "alpha": alpha, "delta": delta, "ts": record["ts"]})

    return {"before": prev, "after": updated}


# -------------------------------
# Snapshots & audit
# -------------------------------

def write_snapshot(signals: Dict[str, Any], weight_diff: Dict[str, Any], bse_diff: Dict[str, Any]) -> None:
    ensure_dirs()
    lines = []
    lines.append("# S7-S5 — Reciprocity Sync Snapshot\n")
    lines.append(f"Generated: {utcnow_iso()}\n")
    lines.append("\n## Signals\n")
    lines.append(json.dumps(signals, indent=2))
    lines.append("\n\n## Weights\n")
    lines.append(json.dumps(weight_diff, indent=2))
    lines.append("\n\n## BSE\n")
    lines.append(json.dumps(bse_diff, indent=2))
    SNAPSHOT.write_text("\n".join(lines), encoding="utf-8")


def log_sync_event(payload: Dict[str, Any]) -> None:
    ensure_dirs()
    rec = {"ts": utcnow_iso(), **payload}
    append_jsonl(SYNC_EVENTS, rec)


# -------------------------------
# Main
# -------------------------------

def run_once(user: str, alpha: float, dry_run: bool, debug: bool=False) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    # 1) Inputs → signals
    signals = collect_reciprocity_signals(user)
    # Optional balance metrics (if present)
    balance = read_latest_balance() or {}
    if balance:
        signals["_balance"] = balance

    # 2) Project to clarity weights
    nudges = derive_weight_updates(signals) or {"global": 0.0, "empathy": 0.0}
    weights_diff = apply_weight_nudges(nudges, dry_run=dry_run)

    # 3) Project to BSE via EMA
    delta = derive_bse_delta_from_signals(signals) or {"risk": 0.0, "conflict": 0.0, "identity": 0.0}
    bse_diff = ema_update_bse(user=user, alpha=alpha, delta=delta, dry_run=dry_run)

    # 4) Debug (after both nudges & delta are ready)
    if debug:
        bal = signals.get("_balance")
        ce_b, er_b = _extract_balance_metrics(bal) if bal is not None else (None, None)
        keys = list(bal.keys()) if isinstance(bal, dict) else type(bal).__name__ if bal is not None else None
        print("[DEBUG] balance keys:", (list(bal.keys()) if isinstance(bal, dict) else type(bal).__name__) if bal is not None else None)
        print("[DEBUG] extracted from balance:", {"ClarityΔ": ce_b, "Empathy": er_b})
        print("[DEBUG] event avgs:", {
            "avg_clarity_effect": signals.get("avg_clarity_effect"),
            "avg_empathy_response": signals.get("avg_empathy_response")
    })
    print("[DEBUG] nudges:", nudges, "BSE delta:", delta)

    # 4) Emit audit artifacts
    write_snapshot(signals, weights_diff, bse_diff)
    log_sync_event({
        "type": "RECIPROCITY_SYNC",
        "user": user,
        "alpha": alpha,
        "nudges": nudges,
        "dry_run": dry_run,
        "counts": {"events": signals.get("count", 0)},
    })

    return signals, weights_diff, bse_diff

def main() -> None:
    parser = argparse.ArgumentParser(description="S7-S5 — Sync reciprocity feedback into runtime learners")
    parser.add_argument("--user", default="local", help="User id to sync (default: local)")
    parser.add_argument("--alpha", type=float, default=0.20, help="EMA alpha for BSE updates")
    parser.add_argument("--once", action="store_true", help="Run one sync iteration and exit")
    parser.add_argument("--watch", action="store_true", help="Continuously watch and sync")
    parser.add_argument("--poll", type=int, default=20, help="Polling interval seconds for watch mode")
    parser.add_argument("--dry-run", action="store_true", help="Do not write weights/BSE (emit snapshot + logs only)")
    parser.add_argument("--debug", action="store_true", help="Print internal signal sources and nudges")
    args = parser.parse_args()

    ensure_dirs()

    # -----------------------------------------------
    # Run mode control: once or watch
    # -----------------------------------------------
    if args.once and args.watch:
        print("[WARN] Both --once and --watch provided; defaulting to --once")
        args.watch = False

    # --- Single-run mode ---
    if args.once or not args.watch:
        print("[S7-S5] sync (once) …")
        signals, weights_diff, bse_diff = run_once(args.user, args.alpha, args.dry_run, debug=args.debug)
        print(f"[S7-S5] events={signals.get('count', 0)} weights→ {weights_diff['after']}  "
              f"BSE[risk]={bse_diff['after'].get('risk'):.3f}")
        return  # <-- stop after one run

    # --- Watch mode ---
    print(f"[S7-S5] watch mode — polling every {args.poll}s (Ctrl+C to stop)…")
    last_seen_ts = None
    try:
        while True:
            # Force debug OFF in watch mode to avoid spam
            signals, weights_diff, bse_diff = run_once(args.user, args.alpha, args.dry_run, debug=False)
            if signals.get("last_ts") != last_seen_ts:
                last_seen_ts = signals.get("last_ts")
                print(f"[S7-S5] new events: {signals.get('count', 0)} | "
                      f"weights→ {weights_diff['after']} | risk={bse_diff['after'].get('risk'):.3f}")
            import time
            time.sleep(max(2, int(args.poll)))
    except KeyboardInterrupt:
        print("[S7-S5] stopped.")


if __name__ == "__main__":
    main()




