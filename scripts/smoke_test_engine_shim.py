# scripts/smoke_test_engine_shim.py
import json
from src.elenx_engine import ElenxEngine

SAMPLES = [
    "We’re sprinting to hit a date, but I’m not sure critical risks are surfaced or just ignored.",
    "Our plan assumes demand will appear once we launch — we haven’t pressure-tested alternatives.",
    "Stakeholders disagree on the goal; I might be treating a preference as a principle.",
    "I have evidence, but it’s cherry-picked; what would disconfirm my view?",
    "My co-founder seems distant; I might be missing relational motivations."
]

def main():
    engine = ElenxEngine()  # will auto-load packs via loader
    print("SMOKE TEST — Engine Shim (detectMode + detectPrinciple)")
    for i, text in enumerate(SAMPLES, 1):
        result, questions = engine.analyze(text, empathy_on=(i % 2 == 0))
        print(f"\n[{i}] {text}")
        print(json.dumps({
            "chosen": {"mode": result.mode, "principle": result.principle},
            "confidence": result.confidence,
            "priors_used": result.priors_used,
            "tags": result.tags,
            "empathy_on": result.empathy_on,
            "questions": questions
        }, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
