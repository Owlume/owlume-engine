# scripts/demo_ui_message.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from elenx_loader import pick_signal  # noqa: E402
from ui_utils import format_clarity_message, as_payload  # noqa: E402

def demo(delta: int):
    sig = pick_signal(delta)
    print(f"Δ={delta}")
    print(format_clarity_message(sig))
    print("Payload:", as_payload(delta, sig))
    print("-" * 60)

if __name__ == "__main__":
    for d in (1, 4, 7):
        demo(d)
