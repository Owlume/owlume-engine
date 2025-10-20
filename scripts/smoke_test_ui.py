# scripts/smoke_test_ui.py
from src.elenx_engine import ElenxEngine
from src.question_renderer import render_question_pack
from src.ui_utils import print_pack_console

def main():
    engine = ElenxEngine()
    sample = "We’re debating trade-offs between speed and quality, and I’m unsure if assumptions are tested."
    result, questions = engine.analyze(sample, empathy_on=True)

    pack = render_question_pack(
        mode_label=result.mode,
        principle_label=result.principle,
        questions=questions,
        confidence=result.confidence,
        empathy_on=result.empathy_on,
        tags=result.tags
    )

    print_pack_console(pack)

if __name__ == "__main__":
    main()
