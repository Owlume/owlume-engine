# scripts/smoke_test_renderer.py
import json
from src.elenx_engine import ElenxEngine
from src.question_renderer import render_question_pack

def main():
    engine = ElenxEngine()  # auto-loads packs via your loader
    sample = (
        "We’re rushing to hit a deadline; I fear we’re ignoring key risks and "
        "assuming demand appears at launch without strong evidence."
    )
    result, questions = engine.analyze(sample, empathy_on=True)
    pack = render_question_pack(
        mode_label=result.mode,
        principle_label=result.principle,
        questions=questions,
        confidence=result.confidence,
        empathy_on=result.empathy_on,
        tags=result.tags
    )
    print("SMOKE TEST — Question Renderer")
    print(json.dumps(pack.to_dict(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
