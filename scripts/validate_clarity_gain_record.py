import json
from jsonschema import Draft7Validator

# --- Load schema file ---
with open("schemas/clarity_gain_record.schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

print("Validating schema structure...")
Draft7Validator.check_schema(schema)
print("✓ Schema itself is valid\n")

validator = Draft7Validator(schema)

# --- Test cases ---
valid_opt_in = {
    "session_id": "DLM-2025-10-18-084522",
    "user_text": "My co-founder is distant. Tension is rising and I’m avoiding the hard talk.",
    "detected": {
        "mode": "Critical",
        "principle": "Assumption",
        "drivers": ["Stakeholder (generic)"],
        "empathy": True,
        "confidence": 0.64,
        "alt": {"mode": "Risk & Second-Order", "principle": "Test Assumptions", "confidence": 0.41}
    },
    "voices": ["Peterson", "Feynman"],
    "clarity_gain": {"CG_pre": 0.42, "CG_post": 0.81, "CG_delta": 0.39},
    "proof_signals": ["Δ-Insight"],
    "share": {
        "status": "opt_in",
        "channel": "markdown",
        "consent": True,
        "timestamp": "2025-10-18T14:55:00Z"
    },
    "timestamp": "2025-10-18T08:45:22+11:00"
}

valid_skipped = {
    "session_id": "DLM-2025-10-18-084523",
    "user_text": "We have two customers; strategy seems solid but pressure is high.",
    "detected": {
        "mode": "Decision",
        "principle": "Evidence",
        "drivers": [],
        "empathy": False,
        "confidence": 0.58,
        "alt": {"mode": None, "principle": None, "confidence": None}
    },
    "voices": ["Thiel"],
    "clarity_gain": {"CG_pre": 0.55, "CG_post": 0.74, "CG_delta": 0.19},
    "proof_signals": ["Depth Bump"],
    "share": {"status": "skipped"},
    "timestamp": "2025-10-18T09:02:10+11:00"
}

invalid_missing_consent = {
    "session_id": "DLM-2025-10-18-084524",
    "user_text": "Testing invalid share.",
    "detected": {
        "mode": "Decision",
        "principle": "Evidence",
        "drivers": [],
        "empathy": False,
        "confidence": 0.58,
        "alt": {"mode": None, "principle": None, "confidence": None}
    },
    "voices": ["Thiel"],
    "clarity_gain": {"CG_pre": 0.55, "CG_post": 0.74, "CG_delta": 0.19},
    "proof_signals": ["Depth Bump"],
    "share": {
        "status": "opt_in",
        "channel": "markdown",
        "timestamp": "2025-10-18T14:55:00Z"
    },
    "timestamp": "2025-10-18T09:02:10+11:00"
}

def test_record(name, record):
    errors = sorted(validator.iter_errors(record), key=lambda e: e.path)
    if not errors:
        print(f"✓ {name}: valid")
    else:
        print(f"✗ {name}: INVALID")
        for e in errors:
            print("  →", "/".join([str(p) for p in e.path]), "-", e.message)
    print()

# --- Run tests ---
test_record("valid_opt_in", valid_opt_in)
test_record("valid_skipped", valid_skipped)
test_record("invalid_missing_consent", invalid_missing_consent)
