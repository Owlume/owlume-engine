from __future__ import annotations  # must be first

import os, sys, inspect, traceback
from pathlib import Path

# Put project root on sys.path so `import src.elenx_engine` works
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Force L1 debug for this run
os.environ["ELENX_DEBUG_WEIGHTS"] = "1"

import src.elenx_engine as EE
print("[L1] smoke using engine file:", EE.__file__)

# (then the rest of your existing imports follow)

# Ensure Python can find the src/ folder (works locally and in CI)
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# UTF-8 for Windows consoles; harmless on Linux CI runners
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---- Samples (keep short so CI is fast) ----
SAMPLES = [
    "We have some notes from two users, but I’m unsure what to do next.",
    "Incentives are misaligned across sales and product; stakeholders are pressuring us and risk is rising.",
    "My co-founder seems distant lately. Tension is building with the team and I worry incentives are clashing.",
    "Let’s brainstorm a new approach. What if we imagine a lightweight prototype to explore novel possibilities?",
    "Looking back, I regret how we handled the first rollout. What patterns do we keep repeating and what lesson is here?",
    "I want to build a better habit around feedback and coaching. How can I evolve my mindset so improvement sticks?",
]

def _limit_samples(samples: list[str]) -> list[str]:
    """Allow CI to limit the number of samples via env var OWLUME_SMOKE_SAMPLES."""
    try:
        n = int(os.getenv("OWLUME_SMOKE_SAMPLES", "6"))
        n = max(1, min(n, len(samples)))
        return samples[:n]
    except Exception:
        return samples[:6]

def main() -> int:
    print("SMOKE: hybrid_fusion start")
    try:
        # Lazy imports after sys.path append so failures are clearer
        from elenx_engine import ElenxEngine
        from elenx_loader import load_packs
    except Exception as e:
        print(f"SMOKE: import_error: {e}")
        print(traceback.format_exc())
        return 1

    try:
        packs = load_packs()
    except Exception as e:
        print(f"SMOKE: load_packs_error: {e}")
        print(traceback.format_exc())
        return 1

    try:
        eng = ElenxEngine(packs)
    except Exception as e:
        print(f"SMOKE: engine_init_error: {e}")
        print(traceback.format_exc())
        return 1
    # --- DR sanity probe (temporary) ---
    try:
        sample = "We have a decision that because of evidence and criteria might be too linear; what alternatives could we explore with stakeholders?"
        det, qs = eng.analyze(sample)
        dr = None
        if hasattr(det, "dual_reasoning"):
            dr = det.dual_reasoning
        elif hasattr(det, "meta") and isinstance(det.meta, dict):
            dr = det.meta.get("dual_reasoning")
        print("[dbg] dual_reasoning:", dr)
    except Exception as e:
        print(f"[dbg] DR probe failed: {e}")
    # --- end DR probe ---

    failures = 0
    ran = 0
    for i, text in enumerate(_limit_samples(SAMPLES), start=1):
        try:
            det, qs = eng.analyze(text)
            dr = None
            if hasattr(det, "meta") and isinstance(det.meta, dict):
                dr = det.meta.get("dual_reasoning")
            elif hasattr(det, "dual_reasoning"):
                dr = det.dual_reasoning
            print("[dbg] dual_reasoning:", dr)

        except Exception as e:
            print(f"SMOKE: analyze_error sample={i}: {e}")
            print(traceback.format_exc())
            failures += 1
            continue

        # Minimal structural assertions (don’t overfit to exact values)
        missing = []
        for attr in ("mode", "principle", "confidence", "priors_used", "empathy_on", "tags"):
            if not hasattr(det, attr):
                missing.append(attr)
        if missing:
            print(f"SMOKE: invalid_detection sample={i}: missing {missing}")
            failures += 1
        else:
            # Log a compact, greppable line for CI
            conf = getattr(det, "confidence", 0.0)
            print(
                f"SMOKE: ok sample={i} "
                f"mode={det.mode} principle={det.principle} conf={conf:.2f} "
                f"priors={det.priors_used} empathy={det.empathy_on} tags={len(det.tags)} qs={len(qs)}"
            )
        ran += 1

    if failures > 0:
        print(f"SMOKE: FAIL ran={ran} failures={failures}")
        return 1

    print(f"SMOKE: PASS ran={ran} failures=0")
    return 0

if __name__ == "__main__":
    sys.exit(main())


