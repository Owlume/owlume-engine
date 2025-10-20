# scripts/smoke_test_engine_fusion.py
import os, sys
# Ensure Python can find the src/ folder
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from elenx_engine import ElenxEngine
from elenx_loader import load_packs  # uses your real loader

# --- Fix Windows console encoding (UTF-8 support for → etc.) ---
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# --- Sample texts for quick sanity checks ---
SAMPLES = [
    # 1) Analytical — unsure / next step (no priors)
    "We have some notes from two users, but I’m unsure what to do next.",

    # 2) Critical — incentives / stakeholder pressure (priors likely)
    "Incentives are misaligned across sales and product; stakeholders are pressuring us and risk is rising.",

    # 3) Critical + Empathy — relationship conflict
    "My co-founder seems distant lately. Tension is building with the team and I worry incentives are clashing.",

    # 4) Creative — ideation / new approach
    "Let’s brainstorm a new approach. What if we imagine a lightweight prototype to explore novel possibilities?",

    # 5) Reflective — hindsight / lessons
    "Looking back, I regret how we handled the first rollout. What patterns do we keep repeating and what lesson is here?",

    # 6) Growth — mindset / feedback / improvement
    "I want to build a better habit around feedback and coaching. How can I evolve my mindset so improvement sticks?",
]


def main():
    # Load all validated packs (Matrix, Voices, Fallacies, Context Drivers)
    packs = load_packs()
    eng = ElenxEngine(packs)

    print("\nHYBRID FUSION — SMOKE TEST\n")

    for i, text in enumerate(SAMPLES, start=1):
        print(f"--- SAMPLE {i} ---")
        print("TEXT:", text)

        det, qs = eng.analyze(text)

        print(
            "MODE×PRINCIPLE:",
            f"{det.mode} × {det.principle} | conf={det.confidence:.2f} "
            f"| priors_used={det.priors_used} | empathy={det.empathy_on}"
        )

        if det.alt_mode or det.alt_principle:
            print(
                "ALT:",
                f"{det.alt_mode or '-'} × {det.alt_principle or '-'} "
                f"| alt_conf={det.alt_confidence:.2f}",
            )

        print("TAGS:", det.tags)
        for q in qs:
            print("Q:", q)
        print()

    print("Hybrid Fusion smoke test completed ✓")

if __name__ == "__main__":
    main()
