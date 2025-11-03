#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingest partner → Owlume reciprocity learning into DilemmaNet.
- Input: data/contracts/mock_learning.jsonl (SDK-stub envelopes)
- Output: data/logs/reciprocity_events.jsonl (normalized events, dedup by reciprocity_id)
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone 

IN_PATH = Path("data/contracts/mock_learning.jsonl")
OUT_PATH = Path("data/logs/reciprocity_events.jsonl")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA_REF = "https://owlume/schemas/owlume_sdk_stub.schema.json"

def normalize(env: dict) -> dict | None:
    if not (isinstance(env, dict) and env.get("$schema") == SCHEMA_REF):
        return None
    out = env.get("output") or {}
    if "learning" not in out:
        return None
    return {
        "reciprocity_id": out.get("reciprocity_id"),
        "did": out.get("did"),
        "learning": out.get("learning"),
        "ts_ingested": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

def load_existing_ids(path: Path) -> set[str]:
    ids = set()
    if not path.exists():
        return ids
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                rid = obj.get("reciprocity_id")
                if rid:
                    ids.add(rid)
            except Exception:
                pass
    return ids

def main():
    if not IN_PATH.exists():
        print(f"[INGEST] No input: {IN_PATH}")
        return
    existing = load_existing_ids(OUT_PATH)
    written = 0
    with IN_PATH.open("r", encoding="utf-8") as fi, OUT_PATH.open("a", encoding="utf-8") as fo:
        for line in fi:
            if not line.strip():
                continue
            env = json.loads(line)
            norm = normalize(env)
            if not norm:
                continue
            rid = norm.get("reciprocity_id")
            if rid in existing:
                continue
            fo.write(json.dumps(norm, ensure_ascii=False) + "\n")
            existing.add(rid)
            written += 1
    print(f"[INGEST] wrote {written} new event(s) → {OUT_PATH}")

if __name__ == "__main__":
    main()
