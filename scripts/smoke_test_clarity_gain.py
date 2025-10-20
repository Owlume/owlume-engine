# scripts/smoke_test_clarity_gain.py
import sys
from pathlib import Path

# Make src importable when run from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from elenx_loader import pick_signal  # noqa: E402


def demo(delta: int):
    sig = pick_signal(delta)
    print(f"Δ={delta} → [{sig.get('id')}] {sig.get('user_message')}")
    coach = sig.get("coach_nudge")
    if coach:
        print(f"  Coach: {coach}")


def main():
    # Try three representative deltas
    for d in (1, 4, 7):
        demo(d)


if __name__ == "__main__":
    main()

