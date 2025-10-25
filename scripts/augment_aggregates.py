# scripts/augment_aggregates.py
"""
Augment aggregates_*.json with:
  - empathy_activation_rate
  - mode_principle_counts
Outputs: aggregates_YYYYmmdd_HHMMSS_aug.json (non-destructive).
"""

import os, sys, json, glob

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(__file__))
METRICS_DIR = os.path.join(ROOT, "data", "metrics")

def _bool_from_any(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        s = v.strip().lower()
        return s in ("true", "on", "yes", "y", "1")
    return False

def _read_jsonl(path):
    # yields dicts from a jsonl file; tolerant to blank lines/commas
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip().rstrip(",")
            if not s:
                continue
            try:
                yield json.loads(s)
            except Exception:
                continue

def _label_from_record(rec):
    """
    Build 'Mode × Principle' using best-available keys.
    Tries: (mode_detected/principle_detected), (mode/principle),
           or a combined 'mode_principle' string.
    """
    # combined?
    for k in ("mode_principle", "mode×principle", "mode_x_principle"):
        if k in rec and isinstance(rec[k], str):
            label = rec[k].strip()
            if " x " in label and "×" not in label:
                label = label.replace(" x ", " × ")
            return label

    # separate keys
    mode = rec.get("mode_detected") or rec.get("mode") or rec.get("Mode") or rec.get("MODE")
    principle = (
        rec.get("principle_detected")
        or rec.get("principle")
        or rec.get("Principle")
        or rec.get("PRINCIPLE")
    )
    if isinstance(mode, str) and isinstance(principle, str) and mode.strip() and principle.strip():
        return f"{mode.strip()} × {principle.strip()}"

    # fallback: not available
    return None

def augment_one(agg_path):
    with open(agg_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_files = data.get("source_files") or []
    if not isinstance(source_files, list) or not source_files:
        print(f"- Skipping (no source_files): {agg_path}")
        return

    n = 0
    empathy_on = 0
    mp_counts = {}

    for src in source_files:
        # Resolve relative paths if any
        p = src
        if not os.path.isabs(p):
            p = os.path.join(ROOT, p)
        if not os.path.exists(p):
            # Also try under data/logs relative
            alt = os.path.join(ROOT, "data", "logs", os.path.basename(p))
            if os.path.exists(alt):
                p = alt
            else:
                print(f"  ! Missing log: {src}")
                continue

        for rec in _read_jsonl(p):
            n += 1

            # empathy detection — try multiple keys/encodings
            e = (
                rec.get("empathy_on")
                or rec.get("empathy")
                or rec.get("empathy_state")
                or rec.get("Empathy")
                or rec.get("EmpathyOn")
            )
            if _bool_from_any(e):
                empathy_on += 1

            # mode × principle label
            label = _label_from_record(rec)
            if label:
                mp_counts[label] = mp_counts.get(label, 0) + 1

    # compute empathy rate if we saw any records
    if n > 0:
        empathy_rate = empathy_on / n
    else:
        empathy_rate = 0.0

    # attach new fields (non-destructive)
    data["empathy_activation_rate"] = round(float(empathy_rate), 6)
    data["mode_principle_counts"] = dict(sorted(mp_counts.items(), key=lambda kv: (-kv[1], kv[0])))

    # write augmented file next to original
    base = os.path.basename(agg_path).replace(".json", "")
    out_path = os.path.join(METRICS_DIR, base + "_aug.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ Augmented → {out_path}  (records={n}, empathy_on={empathy_on})")

# --- replace the main() function at the bottom with this ---
def main():
    paths = sorted(glob.glob(os.path.join(METRICS_DIR, "aggregates_*.json")))
    # ⛔ ignore already-augmented files
    paths = [p for p in paths if not p.endswith("_aug.json")]
    if not paths:
        print("No base aggregates_*.json files found in data/metrics/. Run T4-S2 first.")
        return
    for p in paths:
        augment_one(p)

if __name__ == "__main__":
    main()

