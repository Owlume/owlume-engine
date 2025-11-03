#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock 2-way clarity transfer between a partner system and Owlume SDK Stub.
- Builds a request that validates against /schemas/owlume_sdk_stub.schema.json
- Simulates Elenx processing to produce questions + vectors
- Simulates partner returning learning/outcomes back to DilemmaNet
- Writes JSONL traces to:
    data/contracts/mock_requests.jsonl
    data/contracts/mock_responses.jsonl
    data/contracts/mock_learning.jsonl
"""
import argparse, json, os, random, time
from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256

SCHEMA_REF = "https://owlume/schemas/owlume_sdk_stub.schema.json"

OUTDIR = Path("data/contracts")
OUTDIR.mkdir(parents=True, exist_ok=True)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def hash_alias(user_id: str, salt: str) -> str:
    return "u_" + sha256((salt + ":" + user_id).encode("utf-8")).hexdigest()[:8]

def mock_elenx(text: str):
    """Lightweight stand-in for real processing."""
    # Heuristic: detect false dichotomy if 'either' and 'or' appear close.
    lowered = text.lower()
    fd = 1.0 if ("either" in lowered and " or " in lowered) else 0.0

    # Pick a plausible mode/principle combo and confidence
    if fd >= 1.0:
        mode, principle, conf = "Decision", "Alternatives", 0.72
        fallacies = [{"id": "F-FALSEDICH-1", "label": "False Dichotomy", "score": 1.0}]
        qs = [
            "What viable third options are you excluding?",
            "Which risks are reversible vs. irreversible here?"
        ]
    else:
        mode, principle, conf = "Analytical", "Evidence", 0.60
        fallacies = []
        qs = [
            "What evidence would change your mind?",
            "Which assumptions deserve a quick test?"
        ]

    # Context drivers (toy)
    ctx = [{"id": "C-INCENTIVE-1", "label": "Incentive Pressure", "score": round(random.uniform(0.3, 0.7), 2)}]

    # Empathy overlay
    empathy_activation = random.choice(["LOW", "MEDIUM", "HIGH"])
    empathy_bias = round(random.uniform(-0.2, 0.2), 3)

    # Clarity deltas (toy)
    cg_pre = round(random.uniform(0.3, 0.6), 2)
    cg_post = min(1.0, round(cg_pre + random.uniform(0.15, 0.35), 2))
    cg_delta = round(cg_post - cg_pre, 2)

    # Bias vector snapshot (BSE-style)
    vec = {
        "evidence": round(random.uniform(0.4, 0.9), 3),
        "agency": round(random.uniform(0.3, 0.8), 3),
        "risk": round(random.uniform(0.5, 0.95), 3),
        "conflict": round(random.uniform(0.2, 0.6), 3),
        "identity": round(random.uniform(0.1, 0.5), 3),
        "ambiguity": round(random.uniform(0.3, 0.7), 3),
    }

    return dict(
        mode=mode, principle=principle, confidence=conf,
        questions=qs, fallacies=fallacies, context_drivers=ctx,
        empathy_state={"activation": empathy_activation, "bias": empathy_bias},
        clarity={"cg_pre": cg_pre, "cg_post": cg_post, "cg_delta": cg_delta},
        vectors={"bias_vector": vec, "clarity_vector": {"alternatives": 0.82 if fd else 0.55}}
    )

def write_jsonl(path: Path, obj: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def main():
    ap = argparse.ArgumentParser(description="Simulate partner ↔ Owlume clarity exchange.")
    ap.add_argument("--partner", default="acme-hr")
    ap.add_argument("--user", default="candidate-42")
    ap.add_argument("--salt", default="salt-01")
    ap.add_argument("--text", default="Either we pivot now or the company dies.")
    ap.add_argument("--terms", default="2025-10-01")
    ap.add_argument("--rounds", type=int, default=1)
    args = ap.parse_args()

    req_log = OUTDIR / "mock_requests.jsonl"
    rsp_log = OUTDIR / "mock_responses.jsonl"
    lrn_log = OUTDIR / "mock_learning.jsonl"

    for i in range(args.rounds):
        reciprocity_id = f"RCP-{int(time.time()*1000)%10_000_000:07d}-{i}"
        user_hint = hash_alias(args.user, args.salt)

        # Build request
        request = {
            "$schema": SCHEMA_REF,
            "spec": { "version": "v0.1", "channel": "sdk-stub", "partner_id": args.partner },
            "trust": {
                "consent": { "terms_version": args.terms, "scope": ["process_reflection","return_learning"], "consent_token": "cn-demo" },
                "anonymization": { "enabled": True, "hash_salt_id": args.salt },
                "audit": { "log_level": "summary", "retention_days": 90 }
            },
            "reciprocity": { "return_url": "https://partner.example/feedback", "ack_required": True },
            "input": {
                "reciprocity_id": reciprocity_id,
                "user_hint": user_hint,
                "timestamp": now_iso(),
                "usage_context": "WORK",
                "source": "api",
                "text": args.text,
                "metadata": { "language": "en", "partner_tags": ["demo"] }
            }
        }
        write_jsonl(req_log, request)

        # Simulate Elenx processing
        processed = mock_elenx(args.text)

        response = {
            "$schema": SCHEMA_REF,
            "spec": { "version": "v0.1", "channel": "sdk-stub", "partner_id": args.partner },
            "trust": request["trust"],
            "output": {
                "reciprocity_id": reciprocity_id,
                "did": f"DID-{sha256(reciprocity_id.encode()).hexdigest()[:6]}",
                **processed,
                "audit": { "anonymized": True, "hash_id": user_hint, "log_ref": f"DLN-{datetime.now().strftime('%Y%m%d-%H%M%S')}" }
            }
        }
        write_jsonl(rsp_log, response)

        # Simulate partner returning learning
        learning = {
            "$schema": SCHEMA_REF,
            "spec": { "version": "v0.1", "channel": "sdk-stub", "partner_id": args.partner },
            "trust": request["trust"],
            "output": {
                "reciprocity_id": reciprocity_id,
                "did": response["output"]["did"],
                "learning": {
                    "outcome": random.choice(["IMPROVED_DECISION","STATUS_QUO","DEFERRED"]),
                    "helpfulness": random.randint(3,5),
                    "comment": "The questions exposed a third option.",
                    "label": random.choice(["Hired","Not Hired"]),
                    "cg_pre_ext": round(random.uniform(0.30, 0.55), 2),
                    "cg_post_ext": round(random.uniform(0.60, 0.85), 2)
                }
            }
        }
        write_jsonl(lrn_log, learning)

    print("[MOCK] Wrote:")
    print(f" - {req_log}")
    print(f" - {rsp_log}")
    print(f" - {lrn_log}")
    print("[MOCK] Done.")

if __name__ == "__main__":
    main()
