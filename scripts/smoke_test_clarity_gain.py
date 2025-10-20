# scripts/smoke_test_clarity_gain.py
# UTF-8 safety on Windows terminals
import sys
import os   # <-- this line must be present!

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure we can import from src/
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src")))

from elenx_loader import pick_signal  # returns {"tier": ..., "label": ...}

def show(delta):
    sig = pick_signal(delta) or {}
    tier = sig.get("tier", "NONE")
    label = sig.get("label", "No clarity gain yet")
    print(f"Δ={delta} → [{tier}] {label}")

def main():
    print("CLARITY GAIN — SMOKE TEST")
    # canonical probes
    for d in [0.0, 0.05, 0.28, 0.42, 1, 4, 7]:
        show(d)

    # simple invariants
    assert pick_signal(0.0)["tier"] in {"NONE", "LOW"}, "Zero delta should not be MED/HIGH"
    assert pick_signal(1)["tier"] == "HIGH", "Large delta should be HIGH"

    print("Clarity gain smoke test completed ✓")

if __name__ == "__main__":
    main()


