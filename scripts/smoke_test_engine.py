# scripts/smoke_test_engine.py
# Owlume — Elenx Engine Smoke Test (Stage 3 · T1 Step 2)
# Tests detectMode + detectPrinciple + priors + empathy overlay + top-2 carry.

from src.elenx_loader import get_engine

# Sample reflections to test engine behavior
samples = [
    ("We only looked at two customer surveys and assumed the rest feel the same. Budget is tight.", False),
    ("Because our campaign leads to more signups, we should double spend. What could go wrong?", True),
    ("Either we launch next week or we miss the entire market. It's obvious.", True),
    ("Our data clearly proves the product is superior, so further testing isn’t needed.", False),
]

if __name__ == "__main__":
    eng = get_engine()
    print("\n🧠  OWLUME — ELENX ENGINE SMOKE TEST (TOP-2 MODE × PRINCIPLE)\n")

    for text, empathy in samples:
        print("───────────────────────────────────────────────")
        print("TEXT:", text)
        det, qs = eng.analyze(text, empathy_on=empathy)

        # Primary detection
        print(f"MODE×PRINCIPLE: {det.mode} × {det.principle}")
        print(f"CONFIDENCE: {det.confidence:.2f} | priors_used={det.priors_used} | empathy={det.empathy_on}")

        # Runner-up (top-2 carry)
        if det.alt_mode or det.alt_principle:
            print(f"ALT PATH: {det.alt_mode or '-'} × {det.alt_principle or '-'} | alt_conf={det.alt_confidence}")

        # Tags (priors found)
        f_tags = ', '.join(det.tags.get('fallacies', [])) or '-'
        c_tags = ', '.join(det.tags.get('contexts', [])) or '-'
        print(f"FALLACIES: {f_tags}")
        print(f"CONTEXT DRIVERS: {c_tags}")

        # Generated blind-spot questions
        print("\nGenerated Questions:")
        for i, q in enumerate(qs, 1):
            print(f"  {i}. {q}")
        print("───────────────────────────────────────────────\n")

    print("✅  Smoke test complete — verify Mode × Principle predictions and empathy tone.\n")
