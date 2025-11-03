import json, re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# --- Paths ---
DATA_DIR = Path("data")
FALLACY_V2_PATH = DATA_DIR / "fallacies_v2.json"
FALLACY_INDEX_PATH = DATA_DIR / "indices" / "fallacy_alias_index.json"  # fixed typo

# --- helpers ---
def _read_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))

def load_fallacies_v2(path: Path) -> Dict[str, Any]:
    """
    Load v2 fallacies and build an index in-memory:
      - root_by_id
      - variant_by_id
      - alias_index: token -> set(variant_id)
    Returns {"data": <raw>, "index": <idx>}
    """
    data = _read_json(path)
    idx: Dict[str, Any] = {
        "root_by_id": {},
        "variant_by_id": {},
        "alias_index": {}
    }
    for grp in data.get("fallacy_groups", []):
        root = grp["root"]
        idx["root_by_id"][root["id"]] = root
        for v in grp.get("variants", []):
            vid = v["id"]
            idx["variant_by_id"][vid] = v
            # aliases
            for a in (v.get("aliases") or []):
                idx["alias_index"].setdefault(a.lower(), set()).add(vid)
            # cues.keywords
            for kw in (v.get("cues", {}).get("keywords") or []):
                idx["alias_index"].setdefault(kw.lower(), set()).add(vid)
            # cues.phrases
            for phr in (v.get("cues", {}).get("phrases") or []):
                idx["alias_index"].setdefault(phr.lower(), set()).add(vid)
    return {"data": data, "index": idx}

def load_fallacy_alias_index(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load the prebuilt alias index produced by scripts/export_fallacy_index.py
    Expected keys: alias_index, variant_meta (optional for our matcher)
    """
    if not path.exists():
        return None
    try:
        idx = _read_json(path)
        if "alias_index" in idx:
            print("[Loader] Loaded fallacy_alias_index.json")
            return idx
    except Exception as e:
        print(f"[Loader] fallacy_alias_index.json failed to load: {e}")
    return None

# --- Initialize global index (prefer prebuilt, else build from v2, else None) ---
FALLACY_IDX: Optional[Dict[str, Any]] = None

# 1) Prefer the compact, prebuilt alias index
idx_json = load_fallacy_alias_index(FALLACY_INDEX_PATH)
if idx_json is not None:
    # Normalize shape to what matcher expects
    FALLACY_IDX = {
        "alias_index": idx_json["alias_index"],           # token -> [variant_id, ...]
        "variant_by_id": idx_json.get("variant_meta", {}) # may include principles, drivers
    }
else:
    # 2) If no prebuilt index, try to build from fallacies_v2.json
    if FALLACY_V2_PATH.exists():
        try:
            v2 = load_fallacies_v2(FALLACY_V2_PATH)
            FALLACY_IDX = {
                "alias_index": {k: list(v) for k, v in v2["index"]["alias_index"].items()},  # convert sets -> lists
                "variant_by_id": v2["index"]["variant_by_id"]
            }
            print("[Loader] Built alias index from fallacies_v2.json")
        except Exception as e:
            print(f"[Loader] Could not build v2 alias index: {e}")
            FALLACY_IDX = None
    else:
        print("[Loader] No fallacy index found; cue matching disabled")
        FALLACY_IDX = None

def match_fallacy_variants(text: str, idx: Optional[Dict[str, Any]], k: int = 3) -> List[Tuple[str, float]]:
    """
    Return top-k (variant_id, normalized_score) based on:
      1) alias/keyword/phrase literal hits (fast path)
      2) minimal regex heuristics for common patterns (e.g., either ... or)
    Works with shape: {"alias_index": {token:[vid,...]}, "variant_by_id": {...}}
    """
    if not idx:
        return []

    t = (text or "").lower()
    # light normalization: collapse whitespace
    t = re.sub(r"\s+", " ", t)

    alias_index = idx.get("alias_index", {})
    scores: Dict[str, float] = {}

    # --- 1) literal token hits (existing fast path) ---
    for token, vids in alias_index.items():
        tok = token.lower().strip()
        if not tok:
            continue
        if tok in t:
            w = 1.0 + (0.25 if " " in tok else 0.0)  # boost multi-word phrases
            for vid in vids:
                scores[vid] = scores.get(vid, 0.0) + w

    # --- 2) minimal regex heuristics (pattern-level) ---
    # (a) False Dichotomy: "either ... or"
    try:
        if re.search(r"\beither\b.*\bor\b", t):
            # find a variant under root_id == 'F-FALSEDICH'
            for vid, meta in idx.get("variant_by_id", {}).items():
                # meta may be the variant_meta from export_fallacy_index.py
                root_id = meta.get("root_id") or meta.get("root") or ""
                if root_id == "F-FALSEDICH":
                    scores[vid] = scores.get(vid, 0.0) + 1.25  # strong nudge for classic pattern
                    break
    except Exception:
        pass

    if not scores:
        return []

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    total = sum(s for _, s in ranked) or 1.0
    return [(vid, s / total) for vid, s in ranked[:k]]

