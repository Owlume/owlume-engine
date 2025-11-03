# src/feedback_bridge.py
from __future__ import annotations
import json, os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, Iterable

INBOX = "data/runtime/feedback_events.jsonl"
DID_LOG = "data/logs/clarity_gain_samples.jsonl"
INSIGHTS = "data/runtime/insight_events.jsonl"
APPLIED_IDS = "data/runtime/bridge_applied_ids.jsonl"

# Conservative micro-bumps
BUMPS = {
    "REPLY": 0.03,
    "NUDGE_CLICK": 0.04,
    "RATING_5": 0.05,
    "RATING_4": 0.02,
    "FOLLOW_UP_REFLECTION": 0.06,
}

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

@dataclass
class Event:
    event_id: str
    did: str
    type: str
    ts: str
    payload: Dict[str, Any]
    meta: Dict[str, Any]

class FeedbackBridge:
    def __init__(self):
        self._ensure_files()

    def _seen(self, eid: str) -> bool:
        """Check if an event_id was already processed."""
        if not os.path.exists(APPLIED_IDS):
            return False
        with open(APPLIED_IDS, "r", encoding="utf-8") as f:
            return any(line.strip() == eid for line in f)

    def _mark_seen(self, eid: str):
        """Mark an event_id as processed."""
        with open(APPLIED_IDS, "a", encoding="utf-8") as f:
            f.write(eid + "\n")
   

    def _ensure_files(self):
        os.makedirs("data/runtime", exist_ok=True)
        os.makedirs("data/runtime/archive", exist_ok=True)
        os.makedirs("data/metrics", exist_ok=True)
        os.makedirs("data/logs", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        for p in [INBOX, INSIGHTS]:
            if not os.path.exists(p):
                open(p, "a", encoding="utf-8").close()

    def _emit_insight(self, type_: str, obj: Dict[str, Any]):
        with open(INSIGHTS, "a", encoding="utf-8") as f:
            rec = {"type": type_, "timestamp": _now_iso(), **obj}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def _load_did_records(self) -> Dict[str, Dict[str, Any]]:
        idx: Dict[str, Dict[str, Any]] = {}
        if not os.path.exists(DID_LOG):
            return idx
        with open(DID_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    did = d.get("did")
                    if did:
                        idx[did] = d
                except Exception:
                    continue
        return idx

    def _save_did_record(self, rec: Dict[str, Any]):
        with open(DID_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def _bump_policy(self, ev: Event) -> float:
        if ev.type == "RATING":
            stars = int(_safe_float(ev.payload.get("stars", 0)))
            return BUMPS.get(f"RATING_{stars}", 0.0)
        return BUMPS.get(ev.type, 0.0)

    def _apply_event(self, rec: Dict[str, Any], ev: Event) -> Dict[str, Any]:
        cg_live = rec.setdefault(
            "cg_live",
            {
                "last_feedback_ts": None,
                "replies": 0,
                "shares": 0,
                "signals": {"views": 0, "likes": 0, "bookmarks": 0, "nudges_clicked": 0, "followups": 0},
                "cg_adjust": 0.0,
            },
        )
        cg_live["last_feedback_ts"] = ev.ts

        if ev.type == "REPLY":
            cg_live["replies"] += 1
        elif ev.type == "SHARE_CREATE":
            cg_live["shares"] += 1
            self._emit_insight("SHARE_CREATED", {"did": ev.did})
        elif ev.type == "SHARE_CANCEL":
            cg_live["shares"] = max(0, cg_live["shares"] - 1)
        elif ev.type == "CARD_VIEW":
            cg_live["signals"]["views"] += 1
        elif ev.type == "LIKE":
            cg_live["signals"]["likes"] += 1
        elif ev.type == "BOOKMARK":
            cg_live["signals"]["bookmarks"] += 1
        elif ev.type == "NUDGE_CLICK":
            cg_live["signals"]["nudges_clicked"] += 1
            self._emit_insight("NUDGE_EFFECTIVE", {"did": ev.did})
        elif ev.type == "FOLLOW_UP_REFLECTION":
            cg_live["signals"]["followups"] += 1

        cg_live["cg_adjust"] = round(_safe_float(cg_live.get("cg_adjust", 0.0)) + self._bump_policy(ev), 4)
        # Clamp within sane bounds
        cg_live["cg_adjust"] = max(-0.10, min(0.15, _safe_float(cg_live["cg_adjust"])))
        return rec

    def run_once(self) -> int:
        processed = 0

        # 1) Atomically archive the current inbox (if any)
        if (not os.path.exists(INBOX)) or (os.path.getsize(INBOX) == 0):
            return 0
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join("data/runtime/archive", f"feedback_events_{ts}.jsonl")
        os.replace(INBOX, archive_path)  # move current inbox out; creates a fresh empty INBOX

        # 2) Load DID index once
        did_idx = self._load_did_records()

        # 3) Process the archived batch
        with open(archive_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                ev = Event(   
                    event_id=d["event_id"],
                    did=d["did"],
                    type=d["type"],
                    ts=d["ts"],
                    payload=d.get("payload", {}),
                    meta=d.get("meta", {}),
                )
                # Skip if this event_id was already processed
                if self._seen(ev.event_id):
                    continue

                rec = did_idx.get(ev.did)
                if not rec:
                    self._emit_insight("BRIDGE_SKIPPED_UNKNOWN_DID", {"did": ev.did, "event_id": ev.event_id})
                    continue
                
                updated = self._apply_event(rec, ev)
                self._save_did_record(updated)
                # Mark event as processed
                self._mark_seen(ev.event_id)

                processed += 1

        if processed:
            self._emit_insight("BRIDGE_APPLIED", {"count": processed, "at": _now_iso(), "batch": os.path.basename(archive_path)})
        return processed



