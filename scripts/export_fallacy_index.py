#!/usr/bin/env python3
"""
Builds a compact alias/keyword/phrase index for Fallacies v2.
Input : data/fallacies_v2.json
Output: data/indices/fallacy_alias_index.json
"""
import json
from pathlib import Path

IN_PATH  = Path("data/fallacies_v2.json")
OUT_DIR  = Path("data/indices")
OUT_PATH = OUT_DIR / "fallacy_alias_index.json"

def main():
    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    alias_index = {}       # token -> set(variant_id)
    variant_meta = {}      # variant_id -> {root_id, principles, drivers, severity}

    for grp in data.get("fallacy_groups", []):
        root = grp["root"]
        root_id = root["id"]
        for v in grp.get("variants", []):
            vid = v["id"]
            variant_meta[vid] = {
                "root_id": root_id,
                "principles": v.get("principles", []) or root.get("principles", []),
                "drivers": v.get("drivers", []) or root.get("drivers", []),
                "severity": v.get("severity", root.get("severity", "medium"))
            }
            aliases = (v.get("aliases") or [])
            cues = v.get("cues") or {}
            tokens = (
                [a.strip().lower() for a in aliases] +
                [k.strip().lower() for k in (cues.get("keywords") or [])] +
                [p.strip().lower() for p in (cues.get("phrases") or [])]
            )
            for t in tokens:
                if not t:
                    continue
                alias_index.setdefault(t, set()).add(vid)

    # serialize sets as lists
    alias_index_json = {k: sorted(list(vs)) for k, vs in alias_index.items()}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({
        "spec": "owlume.fallacy_alias_index.v1",
        "version": "1.0.0",
        "built_from": str(IN_PATH),
        "count_tokens": len(alias_index_json),
        "count_variants": len(variant_meta),
        "alias_index": alias_index_json,
        "variant_meta": variant_meta
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[EXPORT] tokens={len(alias_index_json)} variants={len(variant_meta)} → {OUT_PATH}")

if __name__ == "__main__":
    main()
