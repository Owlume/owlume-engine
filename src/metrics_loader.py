# src/metrics_loader.py
from typing import List, Dict, Any, Tuple
import os
import json
import glob
import re
from datetime import datetime

# ------------------ helpers ------------------

def _parse_ts(s: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y%m%d_%H%M%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    digits = "".join(c for c in s if c.isdigit())
    if len(digits) >= 14:
        return datetime.strptime(digits[:14], "%Y%m%d%H%M%S")
    return datetime.fromtimestamp(0)

def _walk(obj: Any, path: Tuple[str, ...] = ()):
    """Yield (path_tuple, key, value) for all leaf dict items and list items."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, path + (str(k),))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, path + (str(i),))
    else:
        yield (path[:-1], path[-1] if path else "", obj)

def _best_number(candidates: List[Tuple[Tuple[str, ...], str, Any]], prefer_keys: Tuple[str, ...]) -> float:
    """
    Pick the most relevant numeric value among candidates by key priority.
    prefer_keys are substrings (lowercased) we prefer in the path/key.
    """
    scored = []
    for p, k, v in candidates:
        try:
            x = float(v)
        except Exception:
            continue
        pk = "/".join(p + (k,))
        lpk = pk.lower()
        score = 0
        for i, pref in enumerate(prefer_keys):
            if pref in lpk:
                score += (len(prefer_keys) - i) * 10
        # light bias for shorter paths (more specific)
        score += max(0, 8 - len(p))
        scored.append((score, x))
    if not scored:
        return 0.0
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[0][1]

def _extract_mp_counts(obj: Any) -> Dict[str, int]:
    """
    Find Mode×Principle counts from:
      - a dict named 'mode_principle_counts' (preferred)
      - any dict whose keys look like 'Mode × Principle' → int
      - any list of {'label': <str>, 'count'| 'value': <int>}
    """
    def norm_label(s: str) -> str:
        # normalize " x " or bare x to the pretty '×'
        return re.sub(r"\b[xX]\b", "×", s)

    out: Dict[str, int] = {}

    def merge_counts(d: Dict[str, Any]):
        for kk, vv in d.items():
            if not isinstance(kk, str):
                continue
            if ("×" in kk) or re.search(r"\b[xX]\b", kk):
                try:
                    out[norm_label(kk)] = out.get(norm_label(kk), 0) + int(vv)
                except Exception:
                    pass

    def walk(node: Any):
        # preferred field first
        if isinstance(node, dict):
            if "mode_principle_counts" in node and isinstance(node["mode_principle_counts"], dict):
                merge_counts(node["mode_principle_counts"])
            # generic dict-of-× keys
            merge_counts(node)
            # recurse values
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                # list of {label,count}
                if isinstance(item, dict):
                    label = item.get("label") or item.get("name")
                    count = item.get("count") or item.get("value")
                    if isinstance(label, str) and (("×" in label) or re.search(r"\b[xX]\b", label)):
                        try:
                            out[norm_label(label)] = out.get(norm_label(label), 0) + int(count)
                        except Exception:
                            pass
                walk(item)

    walk(obj)
    return out

# ------------------ main loader ------------------

def _coalesce_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    When both an original and an _aug.json exist for the same timestamp,
    keep the richer one (prefers empathy_rate > 0 and non-empty mp_counts).
    """
    from collections import defaultdict
    buckets = defaultdict(list)
    for r in records:
        key = r["ts"]
        buckets[key].append(r)

    def quality(r):
        mp_nz = len([k for k in r.get("mp_counts", {}) if k.strip() and k.strip() != "- × -"])
        return (
            (1 if r.get("empathy_rate", 0) > 0 else 0) * 1000
            + mp_nz * 10
            + (1 if r.get("avg_delta", 0) != 0 else 0)
            + (1 if str(r.get("source_file","")).endswith("_aug.json") else 0)  # gentle preference
        )

    picked = []
    for ts, items in buckets.items():
        items.sort(key=quality, reverse=True)
        picked.append(items[0])
    picked.sort(key=lambda r: r["ts"])
    return picked

def load_aggregate_records(metrics_dir: str = None) -> List[Dict[str, Any]]:
    """
    Loads all /data/metrics/aggregates_*.json and returns a list of records:
      {
        "ts": datetime,
        "avg_delta": float,        # clarity gain delta (e.g., totals.avg.cg_delta)
        "empathy_rate": float,     # e.g., ... empathy_activation_rate
        "mp_counts": { "Mode × Principle": int, ... },
        "source_file": str,
      }
    Works with both structured JSON and (as fallback) pretty-printed text reports.
    """
    root = os.path.dirname(os.path.dirname(__file__))
    metrics_dir = metrics_dir or os.path.join(root, "data", "metrics")
    paths = sorted(glob.glob(os.path.join(metrics_dir, "aggregates_*.json")))
    records: List[Dict[str, Any]] = []

    for p in paths:
        # default timestamp from filename
        fname = os.path.basename(p)
        ts_part = fname.replace("aggregates_", "").replace(".json", "")
        ts = _parse_ts(ts_part)

        avg_delta = 0.0
        empathy_rate = 0.0
        mp_counts: Dict[str, int] = {}

        parsed = False
        # ---------- try structured JSON ----------
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            parsed = True
        except Exception:
            data = None

        if parsed and isinstance(data, (dict, list)):
            # prefer generated_at if available
            gen = None
            for _, k, v in _walk(data):
                if isinstance(v, str) and k.lower() in ("generated_at", "timestamp", "ts"):
                    gen = v
                    break
            if gen:
                try:
                    ts = _parse_ts(gen.replace("Z", "Z"))  # safe
                except Exception:
                    pass

            # collect number candidates
            delta_candidates = []
            empathy_candidates = []

            for path, key, val in _walk(data):
                lkey = key.lower()
                # delta candidates: cg_delta first; also any '*delta' keys
                if isinstance(val, (int, float, str)):
                    if lkey.endswith("cg_delta") or lkey == "cg_delta":
                        delta_candidates.append((path, key, val))
                    elif lkey.endswith("delta") or lkey in ("avg_delta", "Δ", "delta"):
                        delta_candidates.append((path, key, val))
                    # empathy * rate
                    if ("empathy" in lkey) and ("rate" in lkey):
                        empathy_candidates.append((path, key, val))

            avg_delta = _best_number(delta_candidates, ("cg_delta", "avg/delta", "delta"))
            empathy_rate = _best_number(empathy_candidates, ("empathy_activation_rate", "empathy/rate", "rate"))

            # mp counts
            mp_counts = _extract_mp_counts(data)

        # ---------- fallback: pretty-printed text ----------
        if (avg_delta == 0.0 and empathy_rate == 0.0 and not mp_counts):
            try:
                with open(p, "rb") as f:
                    raw = f.read()
                text = None
                for enc in ("utf-8", "utf-16", "utf-16-le", "cp1252"):
                    try:
                        cand = raw.decode(enc)
                        if cand and cand.strip():
                            text = cand
                            break
                    except Exception:
                        continue
                if text:
                    text = text.replace("\u00A0", " ").replace("\u2009", " ").replace("\u202F", " ")
                    # AVG line -> last number
                    for line in text.splitlines():
                        if line.strip().startswith("AVG:"):
                            nums = re.findall(r"[+\-]?\d+(?:\.\d+)?", line)
                            if nums:
                                try:
                                    avg_delta = float(nums[-1])
                                except Exception:
                                    pass
                            break
                    # empathy line
                    for line in text.splitlines():
                        if re.search(r"Empathy\s+activation\s+rate\s*:", line, re.I):
                            m = re.search(r"([+\-]?\d+(?:\.\d+)?)", line)
                            if m:
                                try:
                                    empathy_rate = float(m.group(1))
                                except Exception:
                                    pass
                            break
                    # MP counts
                    for raw_line in text.splitlines():
                        line = raw_line.strip()
                        if not line or line.startswith(">"):
                            continue
                        m = re.match(r"^(?:[-*]\s*)?(.+?)\s+(\d+)$", line)
                        if not m:
                            continue
                        label = m.group(1).strip()
                        if ("×" in label) or re.search(r"\b[xX]\b", label):
                            try:
                                count = int(m.group(2))
                                label = re.sub(r"\b[xX]\b", "×", label)
                                mp_counts[label] = mp_counts.get(label, 0) + count
                            except Exception:
                                pass
            except Exception:
                pass

        records.append({
            "ts": ts,
            "avg_delta": float(avg_delta or 0.0),
            "empathy_rate": float(empathy_rate or 0.0),
            "mp_counts": mp_counts or {},
            "source_file": p,
        })

    records.sort(key=lambda r: r["ts"])
    records = _coalesce_records(records)
    return records


