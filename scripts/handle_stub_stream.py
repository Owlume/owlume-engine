#!/usr/bin/env python3
# scripts/handle_stub_stream.py
from __future__ import annotations

# --- path bootstrap (must be first) ---
import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent  # .../owlume-engine
sys.path.insert(0, str(repo_root / "src"))
# --------------------------------------

import json
from hashlib import sha256
from adapters.owlume_sdk_stub_handler import OwlumeSDKHandler
from adapters.elenx_processor import process_with_elenx  # <-- use real Elenx adapter


IN_PATH = Path("data/contracts/mock_requests.jsonl")
OUT_PATH = Path("data/contracts/handled_responses.jsonl")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def demo_processor(text: str):
    """Swap in real Elenx later; shape matches schema.processing_output minus id fields."""
    t = text.lower()
    is_fd = ("either" in t and " or " in t)

    if is_fd:
        mode, principle, conf = "Decision", "Alternatives", 0.72
        fallacies = [{"id": "F-FALSEDICH-1", "label": "False Dichotomy", "score": 1.0}]
        qs = [
            "What viable third options are you excluding?",
            "Which risks are reversible vs. irreversible here?"
        ]
        clarity_vec = {"alternatives": 0.82}
    else:
        mode, principle, conf = "Analytical", "Evidence", 0.60
        fallacies = []
        qs = [
            "What evidence would change your mind?",
            "Which assumptions deserve a quick test?"
        ]
        clarity_vec = {"alternatives": 0.55}

    ctx = [{"id": "C-INCENTIVE-1", "label": "Incentive Pressure", "score": round(random.uniform(0.3, 0.7), 2)}]
    empathy = {"activation": random.choice(["LOW","MEDIUM","HIGH"]), "bias": round(random.uniform(-0.2, 0.2), 3)}
    cg_pre = round(random.uniform(0.3, 0.6), 2)
    cg_post = min(1.0, round(cg_pre + random.uniform(0.15, 0.35), 2))
    vec = {
        "evidence": round(random.uniform(0.4, 0.9), 3),
        "agency": round(random.uniform(0.3, 0.8), 3),
        "risk": round(random.uniform(0.5, 0.95), 3),
        "conflict": round(random.uniform(0.2, 0.6), 3),
        "identity": round(random.uniform(0.1, 0.5), 3),
        "ambiguity": round(random.uniform(0.3, 0.7), 3),
    }

    return {
        "mode": mode,
        "principle": principle,
        "confidence": conf,
        "questions": qs,
        "fallacies": fallacies,
        "context_drivers": ctx,
        "empathy_state": empathy,
        "clarity": {"cg_pre": cg_pre, "cg_post": cg_post, "cg_delta": round(cg_post - cg_pre, 2)},
        "vectors": {"bias_vector": vec, "clarity_vector": clarity_vec},
        "audit": {"anonymized": True, "hash_id": "demo", "log_ref": "DLN-demo"}
    }

def did_factory(reciprocity_id: str) -> str:
    return "DID-" + sha256(reciprocity_id.encode()).hexdigest()[:8]


def main():
    handler = OwlumeSDKHandler(partner_id="sdk-handler")
    count = 0
    with IN_PATH.open("r", encoding="utf-8") as fi, OUT_PATH.open("w", encoding="utf-8") as fo:
        for line in fi:
            if not line.strip():
                continue
            env = json.loads(line)
            # Only process envelopes that follow the Owlume SDK schema and have input
            if env.get("$schema") != "https://owlume/schemas/owlume_sdk_stub.schema.json" or "input" not in env:
                continue

            # ✅ Use the real Elenx processor now
            resp = handler.process_input(env, process_with_elenx, did_factory)
            fo.write(json.dumps(resp, ensure_ascii=False) + "\n")
            count += 1

    print(f"[HANDLER] processed {count} request(s) → {OUT_PATH}")


if __name__ == "__main__":
    main()