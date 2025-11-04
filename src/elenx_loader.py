# src/elenx_loader.py
import json
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    import jsonschema  # type: ignore
    HAS_JSONSCHEMA = True
except Exception:
    HAS_JSONSCHEMA = False

    # Canonical sets for Questioncraft Matrix (Tightened)
VALID_MODES = {
    "Analytical",
    "Critical",
    "Creative",
    "Reflective",
    "Growth"
}

VALID_PRINCIPLES = {
    "Assumption",
    "Evidence",
    "Risk",
    "Clarity",
    "Efficiency",
    "Action"
}

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCHEMA_DIR = ROOT / "schemas"

FILES = {
    "matrix": ("matrix.json", "matrix.schema.json"),
    "voices": ("voices.json", "voices.schema.json"),
    "fallacies": ("fallacies.json", "fallacies.schema.json"),
    "context_drivers": ("context_drivers.json", "context_drivers.schema.json"),
}

class LoadError(RuntimeError):
    pass

def _read_json(path: Path) -> Any:
    if not path.exists():
        raise LoadError(f"Missing file: {path}")
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise LoadError(f"JSON parse error in {path}: {e}") from e

def _validate(name: str, data: Any, schema_path: Path) -> None:
    if not HAS_JSONSCHEMA:
        return  # validation skipped if jsonschema not installed
    if not schema_path.exists():
        return  # schema optional
    schema = _read_json(schema_path)
    try:
        jsonschema.validate(instance=data, schema=schema)
    except Exception as e:
        raise LoadError(f"Schema validation failed for {name} ({schema_path.name}): {e}") from e

def load_pack(name: str) -> Tuple[Any, Path]:
    data_fname, schema_fname = FILES[name]
    data_path = DATA_DIR / data_fname
    schema_path = SCHEMA_DIR / schema_fname
    data = _read_json(data_path)
    _validate(name, data, schema_path)
    return data, data_path

def load_all() -> Dict[str, Any]:
    loaded: Dict[str, Any] = {}
    for key in FILES:
        data, _ = load_pack(key)
        loaded[key] = data
    return loaded

def summary(loaded: Dict[str, Any]) -> str:
    # compact human check
    parts = []
    m = loaded.get("matrix", {})
    v = loaded.get("voices", {})
    f = loaded.get("fallacies", {})
    c = loaded.get("context_drivers", {})
    # heuristics for counts
    def count_matrix_nodes(mat: Dict[str, Any]) -> Tuple[int, int]:
        modes = len(mat) if isinstance(mat, dict) else 0
        principles = 0
        if isinstance(mat, dict):
            for mode in mat.values():
                if isinstance(mode, dict):
                    principles += len(mode)
        return modes, principles
    modes_cnt, principles_cnt = count_matrix_nodes(m)
    parts.append(f"matrix: modes={modes_cnt}, principles~={principles_cnt}")
    parts.append(f"voices: {len(v.get('voices', [])) if isinstance(v, dict) else 0}")
    parts.append(f"fallacies: {len(f.get('fallacies', [])) if isinstance(f, dict) else 0}")
    parts.append(f"context_drivers: {len(c.get('drivers', [])) if isinstance(c, dict) else 0}")
    return " | ".join(parts)

if __name__ == "__main__":
    loaded = load_all()
    print("Elenx loader ✓ loaded packs")
    print(summary(loaded))

# --- Convenience wrapper for full pack loading ---
def load_packs() -> dict:
    """Loads all four core Elenx data packs at once."""
    return {
        "matrix": load_pack("matrix"),
        "voices": load_pack("voices"),
        "fallacies": load_pack("fallacies"),
        "context_drivers": load_pack("context_drivers"),
    }
# --- Clarity Gain signal picker (shim) ---
# Provides a stable API for smoke_test_clarity_gain.py
# Reads thresholds if available; otherwise uses sane defaults.

import json
import os
from typing import Dict

def _load_thresholds(defaults: Dict[str, float] = None) -> Dict[str, float]:
    if defaults is None:
        defaults = {"LOW_MAX": 0.20, "MED_MAX": 0.35}  # HIGH = > MED_MAX
    path = os.path.join(os.path.dirname(__file__), "..", "data", "clarity_gain_thresholds.json")
    path = os.path.normpath(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Accept either flat or nested formats; fall back safely
        low_max = cfg.get("LOW_MAX") or cfg.get("thresholds", {}).get("LOW_MAX") or defaults["LOW_MAX"]
        med_max = cfg.get("MED_MAX") or cfg.get("thresholds", {}).get("MED_MAX") or defaults["MED_MAX"]
        return {"LOW_MAX": float(low_max), "MED_MAX": float(med_max)}
    except Exception:
        return defaults

def pick_signal(delta: float) -> Dict[str, str]:
    """
    Returns a simple signal dict for the given clarity delta.
    Example: {"tier": "MED", "label": "Moderate clarity gain"}
    """
    th = _load_thresholds()
    if delta is None:
        delta = 0.0
    try:
        d = float(delta)
    except Exception:
        d = 0.0

    if d <= 0.0:
        tier = "NONE"
        label = "No clarity gain yet"
    elif d <= th["LOW_MAX"]:
        tier = "LOW"
        label = "Slight clarity gain"
    elif d <= th["MED_MAX"]:
        tier = "MED"
        label = "Moderate clarity gain"
    else:
        tier = "HIGH"
        label = "Strong clarity jump"

    return {"tier": tier, "label": label}
