# src/policy_utils.py
import json
from pathlib import Path

POLICY_PATH = Path("data/runtime/agent_policy.json")

DEFAULT_POLICY = {
    "risk_probe": 0.50,
    "assumption_challenge": 0.50,
    "empathy_weight": 0.55,
    "tone_warmth": 0.50,
}

def load_current_policy():
    if POLICY_PATH.exists():
        try:
            return json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_POLICY.copy()
