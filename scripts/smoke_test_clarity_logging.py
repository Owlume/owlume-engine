# scripts/smoke_test_clarity_logging.py
import os, sys, json, random, time
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# --- UTF-8 fix for Windows consoles ---
import sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")

from elenx_loader import load_packs
from elenx_engine import ElenxEngine
from clarity_logger import load_schema, validate_record, log_record, make_session_id
from pick_signal import pick_delta_signals, pick_insight_signals

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "schemas", "clarity_gain_record.schema.json")
THRESH_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "clarity_gain_thresholds.json")

SAMPLES = [
    "We have strong evidence from two customers, so the strategy is solid. Incentives are clashing across sales and product.",
    "My co-founder is distant. Tension is rising and I’m avoiding the hard talk.",
    "We keep shipping features without testing assumptions. Time pressure is distorting our choices."
]

def estimate_pre_clarity(text: str) -> float:
    base = 0.55 - min(0.25, len(text)/400.0)
    return round(max(0.05, min(0.9, base)), 2)

def simulate_post_clarity(pre: float) -> float:
    gain = random.choice([0.08, 0.12, 0.18, 0.26, 0.41])
    return round(min(1.0, pre + gain), 2)

def load_thresholds() -> dict:
    with open(THRESH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def tier_for_delta(delta: float, thresholds: dict) -> str:
    if delta >= thresholds.get("high", 0.4):
        return "high"
    if delta >= thresholds.get("medium", 0.25):
        return "medium"
    if delta >= thresholds.get("low", 0.1):
        return "low"
    return "none"

def round_opt(x, nd=2):
    return None if x is None else round(x, nd)

def main():
    packs = load_packs()
    eng = ElenxEngine(packs)
    schema = load_schema(SCHEMA_PATH)
    thresholds = load_thresholds()

    print("SMOKE — T2 logging (Engine → CG → Signals → JSONL)")
    print("thresholds:", thresholds)

    for i, text in enumerate(SAMPLES, 1):
        print(f"\n--- SAMPLE {i} ---")
        print("TEXT:", text)

        det, qs = eng.analyze(text)  # Engine result + generated questions
        print("MODE×PRINCIPLE:", f"{det.mode} × {det.principle} | conf={det.confidence:.2f} | priors_used={det.priors_used} | empathy={det.empathy_on}")

        # Safer ALT print
        if getattr(det, "alt_mode", None) or getattr(det, "alt_principle", None) or getattr(det, "alt_confidence", None) is not None:
            alt_c = getattr(det, "alt_confidence", None)
            alt_c_str = f"{alt_c:.2f}" if isinstance(alt_c, (int, float)) else "—"
            print("ALT:", f"{getattr(det, 'alt_mode', '-') } × {getattr(det, 'alt_principle','-')} | alt_conf={alt_c_str}")

        print("TAGS:", det.tags)

        # Clarity gain
        cg_pre = estimate_pre_clarity(text)
        cg_post = simulate_post_clarity(cg_pre)
        cg_delta = round(cg_post - cg_pre, 2)
        tier = tier_for_delta(cg_delta, thresholds)
        print(f"CG_pre={cg_pre}  CG_post={cg_post}  Δ={cg_delta} ({tier})")

        # Signals
        delta_signals = pick_delta_signals(cg_delta)
        insight_signals = pick_insight_signals(text, " | ".join(qs))
        signals = list(dict.fromkeys(delta_signals + insight_signals))
        print("Signals:", signals)

        # Record
        session_id = make_session_id()
        record = {
            "session_id": session_id,
            "user_text": text,
            "detected": {
                "mode": det.mode,
                "principle": det.principle,
                "drivers": det.tags.get("contexts", []),
                "empathy": det.empathy_on,
                "confidence": round(det.confidence, 2),
                "alt": {
                    "mode": getattr(det, "alt_mode", None),
                    "principle": getattr(det, "alt_principle", None),
                    "confidence": round_opt(getattr(det, "alt_confidence", None), 2)
                }
            },
            "voices": ["Peterson", "Feynman"],
            "clarity_gain": {"CG_pre": cg_pre, "CG_post": cg_post, "CG_delta": cg_delta},
            "proof_signals": signals,
            "share": {"status": "hidden"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
        }

        # Validate & persist
        validate_record(record, schema)
        out_path = log_record(record)
        print("Logged →", out_path)

    print("\nT2 smoke complete ✓")

if __name__ == "__main__":
    main()
