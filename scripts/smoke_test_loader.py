# scripts/smoke_test_loader.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from elenx_loader import load_all, summary  # noqa: E402

def main():
    loaded = load_all()
    print("SMOKE TEST — Elenx loader")
    print(summary(loaded))
    # minimal sanity checks (raise if broken)
    assert "matrix" in loaded and loaded["matrix"], "matrix missing/empty"
    assert "voices" in loaded and loaded["voices"], "voices missing/empty"
    assert "fallacies" in loaded and loaded["fallacies"], "fallacies missing/empty"
    assert "context_drivers" in loaded and loaded["context_drivers"], "context_drivers missing/empty"
    print("All core packs present ✓")

if __name__ == "__main__":
    main()
