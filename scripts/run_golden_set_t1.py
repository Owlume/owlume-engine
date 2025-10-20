# scripts/run_golden_set_t1.py
# Expects a small CSV/MD you already have with two columns: text, expected_mode(optional)
from src.elenx_loader import get_engine

GOLDEN = [
    {"text":"We either launch Friday or lose everything.", "expected_mode":"Trade-off"},
    {"text":"We assumed the supplier will agree to new terms.", "expected_mode":"Assumption"},
]

if __name__ == "__main__":
    eng = get_engine()
    hits = 0
    for row in GOLDEN:
        det, _ = eng.analyze(row["text"], empathy_on=False)
        ok = (row["expected_mode"] is None) or (det.mode == row["expected_mode"])
        hits += 1 if ok else 0
        print(f"{'PASS' if ok else 'FAIL'} | expected={row['expected_mode']} got={det.mode} × {det.principle} ({det.confidence})")
    print(f"\nAccuracy (mode only): {hits}/{len(GOLDEN)}")
