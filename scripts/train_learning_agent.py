"""
Owlume — Stage 4 · L5 · T3
File: scripts/train_learning_agent.py

Replays recent agent learning events to update a persistent policy vector.
- Input: data/reports/agent_memory_snapshot.json (preferred) or runtime JSONL
- Output: data/runtime/agent_policy.json
Usage:
    python -u scripts/train_learning_agent.py --source snapshot
    python -u scripts/train_learning_agent.py --source runtime
"""
import json, argparse
from pathlib import Path
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.agent_core import (
    ContextState, EmpathyState,
    InputsEmpathy, InputsClarity,
    learn
)

SNAPSHOT = Path("data/reports/agent_memory_snapshot.json")
RUNTIME_JSONL = Path("data/runtime/agent_memory.jsonl")
POLICY_PATH = Path("data/runtime/agent_policy.json")

DEFAULT_POLICY = {
    "risk_probe": 0.50,
    "assumption_challenge": 0.50,
    "empathy_weight": 0.55,
    "tone_warmth": 0.50,
}

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def load_policy():
    if POLICY_PATH.exists():
        with open(POLICY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_POLICY.copy()

def save_policy(policy):
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(POLICY_PATH, "w", encoding="utf-8") as f:
        json.dump(policy, f, indent=2, ensure_ascii=False)

def load_records_from_snapshot():
    if not SNAPSHOT.exists():
        print("[X] Snapshot not found:", SNAPSHOT)
        return []
    with open(SNAPSHOT, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return obj.get("records", [])

def load_records_from_runtime():
    if not RUNTIME_JSONL.exists():
        print("[X] Runtime JSONL not found:", RUNTIME_JSONL)
        return []
    records = []
    with open(RUNTIME_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                records.append(json.loads(s))
            except Exception:
                pass
    return records

def to_context(rec):
    cs = rec["context_state"]
    es = cs["empathy_state"]
    return ContextState(
        mode=cs["mode"],
        principle=cs["principle"],
        empathy_state=EmpathyState(state=es.get("state","AUTO"),
                                   intensity=es.get("intensity"),
                                   rationale=es.get("rationale"))
    )

def to_inputs(rec):
    emp = rec["inputs"]["empathy"]
    cla = rec["inputs"]["clarity"]
    return (
        InputsEmpathy(E=float(emp.get("E", 0.5)), feedback=emp.get("feedback", {})),
        InputsClarity(
            cg_pre=float(cla["cg_pre"]),
            cg_post=float(cla["cg_post"]),
            cg_delta=float(cla["cg_delta"])
        )
    )

def train(source: str):
    policy = load_policy()
    policy_before = policy.copy()

    if source == "snapshot":
        records = load_records_from_snapshot()
    else:
        records = load_records_from_runtime()

    if not records:
        print("[!] No records to train on.")
        return

    count = 0
    for rec in records:
        context = to_context(rec)
        inp_emp, inp_cla = to_inputs(rec)

        # Replay learning without logging a new event
        policy, update, meta = learn(
            did=(rec.get("ids") or {}).get("did"),
            session_id=(rec.get("ids") or {}).get("session_id"),
            user_hash=(rec.get("ids") or {}).get("user_hash"),
            context=context,
            inputs_empathy=inp_emp,
            inputs_clarity=inp_cla,
            policy_before=policy,
            belief_map_touch=rec.get("belief_map_touch", []),
            dry_run=True,
        )
        count += 1

    save_policy(policy)

    print("[OK] Training complete on", count, "records.")
    print("[OK] Policy before:", policy_before)
    print("[OK] Policy after :", policy)
    print("[OK] Saved →", POLICY_PATH)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["snapshot","runtime"], default="snapshot",
                    help="Train from aggregated snapshot (default) or raw runtime JSONL")
    args = ap.parse_args()
    train(args.source)
