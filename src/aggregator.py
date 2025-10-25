# src/aggregator.py
from __future__ import annotations
import json, os, math, datetime as dt
from typing import Dict, Any, Iterable, Tuple, List, Optional, DefaultDict
from collections import defaultdict, Counter

def _parse_iso(ts: str) -> dt.datetime:
    # Accepts "...Z" or timezone-naive ISO; normalizes to UTC-naive for bucketing.
    ts = ts.strip().replace("Z","")
    try:
        return dt.datetime.fromisoformat(ts)
    except ValueError:
        # Fallbacks for common formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try: return dt.datetime.strptime(ts, fmt)
            except ValueError: pass
        raise

def _tier_for_delta(delta: float) -> str:
    # Keep in sync with /data/clarity_gain_thresholds.json if you’ve customized it.
    # Defaults: LOW < 0.20, 0.20–0.35 = MED, ≥0.35 = HIGH
    if delta < 0.20: return "LOW"
    if delta < 0.35: return "MED"
    return "HIGH"

class Aggregator:
    """
    Reads DilemmaNet logs (JSONL) and aggregates Clarity metrics.
    Expected minimal fields per record:
      - cg_pre (float 0..1), cg_post (float 0..1), cg_delta (float -1..1)
      - mode_detected (str), principle_detected (str)
      - empathy_state (str: "ON"|"OFF")
      - timestamp (ISO)
      - did (string id)
    Optional:
      - tags.contexts: [str], tags.fallacies: [str]
    """
    def __init__(self, log_files: Iterable[str]) -> None:
        self.log_files = list(log_files)
        self.rows: List[Dict[str, Any]] = []

    def load(self) -> int:
        count = 0
        for path in self.log_files:
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        rec = json.loads(line)
                        self.rows.append(rec)
                        count += 1
                    except json.JSONDecodeError:
                        # Skip bad lines; in T4 we log and continue
                        continue
        return count

    def _iter_valid(self) -> Iterable[Dict[str, Any]]:
        for r in self.rows:
            try:
                _ = float(r.get("cg_delta", 0.0))
                _ = float(r.get("cg_pre", 0.0))
                _ = float(r.get("cg_post", 0.0))
                _ = str(r.get("mode_detected", ""))
                _ = str(r.get("principle_detected", ""))
                _ = str(r.get("empathy_state", "OFF"))
                _ = _parse_iso(str(r.get("timestamp", "") or ""))
                yield r
            except Exception:
                # Skip incomplete/bad records
                continue

    def aggregate(self, tz: Optional[str]=None) -> Dict[str, Any]:
        # Collectors
        count = 0
        sum_pre = sum_post = sum_delta = 0.0
        pos = neg = zero = 0

        tiers = Counter()
        empathy_on = empathy_off = 0
        mode_counts = Counter()
        principle_counts = Counter()
        mxp_counts = Counter()  # Mode × Principle
        fallacy_counts = Counter()
        context_counts = Counter()

        # Time buckets
        by_day: DefaultDict[str, Dict[str, Any]] = defaultdict(lambda: {"n":0,"avg_delta":0.0})
        by_week: DefaultDict[str, Dict[str, Any]] = defaultdict(lambda: {"n":0,"avg_delta":0.0})

        for r in self._iter_valid():
            count += 1
            pre  = float(r.get("cg_pre", 0.0))
            post = float(r.get("cg_post", 0.0))
            d    = float(r.get("cg_delta", post - pre))
            sum_pre  += pre
            sum_post += post
            sum_delta+= d

            if d > 0: pos += 1
            elif d < 0: neg += 1
            else: zero += 1
            tiers[_tier_for_delta(d)] += 1

            emp = str(r.get("empathy_state","OFF")).upper().strip()
            if emp == "ON": empathy_on += 1
            else: empathy_off += 1

            mode = str(r.get("mode_detected","")).strip() or "-"
            prin = str(r.get("principle_detected","")).strip() or "-"
            mode_counts[mode] += 1
            principle_counts[prin] += 1
            mxp_counts[f"{mode} × {prin}"] += 1

            tags = r.get("tags") or {}
            for fa in tags.get("fallacies",[]) or []:
                fallacy_counts[str(fa)] += 1
            for cx in tags.get("contexts",[]) or []:
                context_counts[str(cx)] += 1

            # Time bucketing
            t = _parse_iso(str(r.get("timestamp")))
            day_key  = t.strftime("%Y-%m-%d")
            week_key = f"{t.year}-W{t.isocalendar().week:02d}"

            # Online mean update
            for bucket, store in ((day_key, by_day),(week_key, by_week)):
                dct = store[bucket]
                n = dct["n"] + 1
                dct["avg_delta"] = dct["avg_delta"] + (d - dct["avg_delta"]) * (1.0/n)
                dct["n"] = n

        avg_pre  = (sum_pre / count)  if count else 0.0
        avg_post = (sum_post / count) if count else 0.0
        avg_delta= (sum_delta/ count) if count else 0.0
        empathy_rate = (empathy_on / count) if count else 0.0
        positive_rate= (pos / count) if count else 0.0
        negative_rate= (neg / count) if count else 0.0
        zero_rate    = (zero/ count) if count else 0.0

        def _top_k(c: Counter, k=10):
            return [{"label": k_, "count": v} for k_,v in c.most_common(k)]

        return {
            "spec": "owlume.aggregates.v1",
            "generated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_files": self.log_files,
            "totals": {
                "n_records": count,
                "avg": {"cg_pre": round(avg_pre,3), "cg_post": round(avg_post,3), "cg_delta": round(avg_delta,3)},
                "distribution": {
                    "positive_rate": round(positive_rate,3),
                    "negative_rate": round(negative_rate,3),
                    "zero_rate": round(zero_rate,3),
                    "tiers": dict(tiers),
                },
                "empathy": {
                    "on": empathy_on,
                    "off": empathy_off,
                    "activation_rate": round(empathy_rate,3)
                }
            },
            "top": {
                "modes": _top_k(mode_counts),
                "principles": _top_k(principle_counts),
                "mode_x_principle": _top_k(mxp_counts),
                "fallacies": _top_k(fallacy_counts),
                "contexts": _top_k(context_counts),
            },
            "timeseries": {
                "by_day": [{"day":k,"n":v["n"],"avg_delta":round(v["avg_delta"],3)} for k,v in sorted(by_day.items())],
                "by_week":[{"week":k,"n":v["n"],"avg_delta":round(v["avg_delta"],3)} for k,v in sorted(by_week.items())],
            }
        }
