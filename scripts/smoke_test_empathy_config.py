import json, sys, pathlib

cfg_path = pathlib.Path("config/empathy_config.json")

try:
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
except Exception as e:
    print(f"[x] Failed to read {cfg_path}: {e}")
    sys.exit(1)

# --- 1. schema pointer check ---
schema_ok = str(data.get("$schema", "")).endswith("/empathy_weights.schema.json")
if not schema_ok:
    print("[x] Missing or incorrect $schema pointer")
    sys.exit(2)

# --- 2. required empathy modes ---
weights = data.get("weights", {})
required = ("relational", "moral", "contextual")
missing = [k for k in required if k not in weights]
if missing:
    print(f"[x] Missing weights for: {', '.join(missing)}")
    sys.exit(3)

# --- 3. clarity-gain linkage check ---
link_ok = all(
    weights[k].get("link_to") in ("cg_delta", "clarity_gain_delta")
    for k in required
)
if not link_ok:
    print("[x] Each empathy subtype must have link_to set to cg_delta or clarity_gain_delta")
    sys.exit(4)

print("[✓] empathy_config.json validated successfully")
print("[✓] Linkage check: clarity_gain_delta → empathy_weight.ok")
print("[✓] All empathy modes registered (relational, moral, contextual)")
