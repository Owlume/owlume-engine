# T3‑S4 — Share Card UX Polish & Integration (Final v2)

## 🎯 Objectives

* Make sharing feel deliberate, minimal, and classy.
* Keep privacy‑first: only show/share when `status=="opt_in"`.
* Add a tiny visual lift (icon + label) without clutter.
* Provide one‑click scripts/tasks to simulate the full flow end‑to‑end.

---

## A) Renderer Polish (icons + footer)

### A1) Add channel icon utilities

**File:** `src/ui_utils.py` — append at end

```python
# --- T3-S4: Share UI helpers ---
CHANNEL_ICONS = {
    "markdown": "📝",
    "image": "🖼️",
}

def format_share_footer(share: dict) -> str:
    if not share or share.get("status") != "opt_in":
        return ""
    ch = (share.get("channel") or "markdown").lower()
    icon = CHANNEL_ICONS.get(ch, "📤")
    ts = share.get("timestamp") or ""
    label = ch.capitalize()
    return f"\n_{icon} Shared via {label} • {ts}_"
```

### A2) Use in renderer demo

**File:** `scripts/demo_render_cards.py` — replace footer block

```python
# T3-S4: improved footer
from ui_utils import format_share_footer  # add near other imports

# ...
footer = format_share_footer(record)
if footer:
    card_md = f"{card_md}\n{footer}"
```

**Acceptance:**

* Markdown → `_📝 Shared via Markdown • 2025‑10‑18T14:55:00Z_`
* Image → `_🖼️ Shared via Image • …_`
* Skipped → no footer

---

## B) Share Action CLI (simulate opt‑in)

### B1) Create CLI

**File:** `scripts/share_card_cli.py`

```python
import json, sys, datetime, argparse

def iso_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def main():
    ap = argparse.ArgumentParser(description="T3-S4: mark record as shared (opt-in)")
    ap.add_argument("jsonl", help="path to JSONL (e.g., data/logs/clarity_gain_samples.jsonl)")
    ap.add_argument("--did", required=True, help="record id (e.g., DID-2025-0014)")
    ap.add_argument("--channel", choices=["markdown", "image"], default="markdown")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    updated, found = [], False
    with open(args.jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("did") == args.did:
                obj["share"] = {
                    "status": "opt_in",
                    "channel": args.channel,
                    "consent": True,
                    "timestamp": iso_now()
                }
                found = True
            updated.append(json.dumps(obj, ensure_ascii=False))

    if not found:
        print(f"[WARN] did={args.did} not found in {args.jsonl}")
    if args.dry:
        print("\n".join(updated))
    else:
        with open(args.jsonl, "w", encoding="utf-8") as w:
            w.write("\n".join(updated) + "\n")
        print(f"[OK] updated {args.jsonl} (did={args.did}, channel={args.channel})")

if __name__ == "__main__":
    main()
```

**Usage:**

```bash
python -u scripts/share_card_cli.py data/logs/clarity_gain_samples.jsonl --did DID-2025-0014 --channel markdown
python -u scripts/demo_render_cards.py
```

---

## C) Validator Guardrail

### C1) Create one‑shot validator

**File:** `scripts/validate_clarity_jsonl.py`

```python
import json, sys
from jsonschema import Draft7Validator

SCHEMA_PATH = "schemas/clarity_gain_record.schema.json"

def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/validate_clarity_jsonl.py <jsonl_path>")
        sys.exit(1)
    jsonl = sys.argv[1]
    schema = json.load(open(SCHEMA_PATH, "r", encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    v = Draft7Validator(schema)
    errs = n = 0

    with open(jsonl, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            obj = json.loads(line); n += 1
            e = list(v.iter_errors(obj))
            if e:
                errs += 1
                print(f"[INVALID] line {i}:")
                for ee in e:
                    path = "/".join(map(str, ee.path)) or "<root>"
                    print(f"  → {path} - {ee.message}")

    if errs == 0:
        print(f"[OK] {jsonl}: all {n} records valid")
    else:
        print(f"[FAIL] {jsonl}: {errs} invalid of {n}")
        sys.exit(2)

if __name__ == "__main__":
    main()
```

**Run:**

```bash
python -u scripts/validate_clarity_jsonl.py data/logs/clarity_gain_samples.jsonl
```

---

## D) VS Code Tasks (one‑click)

Append to `.vscode/tasks.json`:

```json
{
  "label": "Run: Share Card (opt-in, markdown)",
  "type": "shell",
  "command": "python",
  "args": ["-u", "scripts/share_card_cli.py", "data/logs/clarity_gain_samples.jsonl", "--did", "DID-2025-0014", "--channel", "markdown"],
  "presentation": {"reveal": "always", "panel": "dedicated", "clear": true}
},
{
  "label": "Run: Validate JSONL",
  "type": "shell",
  "command": "python",
  "args": ["-u", "scripts/validate_clarity_jsonl.py", "data/logs/clarity_gain_samples.jsonl"],
  "group": {"kind": "test", "isDefault": false},
  "presentation": {"reveal": "always", "panel": "dedicated", "clear": true}
},
{
  "label": "Run: Demo Render Cards",
  "type": "shell",
  "command": "python",
  "args": ["-u", "scripts/demo_render_cards.py"],
  "presentation": {"reveal": "always", "panel": "dedicated", "clear": true}
}
```

**Flow:**
1️⃣ Run: Share Card → mark opt‑in
2️⃣ Run: Validate JSONL → should pass
3️⃣ Run: Demo Render Cards → footer visible with 📝 icon

---

## E) Acceptance Tests

| Case                 | Expectation                                     |
| -------------------- | ----------------------------------------------- |
| Opt‑in               | Footer shows correct icon + label; validator OK |
| Skipped              | No footer; validator OK                         |
| Invalid (no consent) | Validator FAIL (privacy guard)                  |
| Unknown channel      | Schema enum reject → validator FAIL             |

---

## F) Commit & Tag

```bash
git add src/ui_utils.py scripts/share_card_cli.py scripts/validate_clarity_jsonl.py scripts/demo_render_cards.py .vscode/tasks.json
git commit -m "feat(T3-S4): share footer icons + CLI + validator + tasks"
git tag -a T3-S4-final -m "T3-S4 final: share UX polish & integration"
```

---

## G) Documentation Note

**/docs/way_forward.md** — append:

```md
### T3‑S4 — Share Card UX Polish (Final)
- Footer now shows channel icon/label when `share.status=="opt_in"` (📝 Markdown, 🖼️ Image)
- Added `scripts/share_card_cli.py` to mark records as shared (opt‑in)
- Added `scripts/validate_clarity_jsonl.py` to enforce schema integrity
- VS Code tasks for one‑click flow: Share → Validate → Render
- Privacy enforced via consent=true requirement
```

---

## ✅ Outcome

By end of **T3‑S4**, Owlume has:

* Polished Clarity Card UX with share icons
* CLI + validator + tasks for reproducible share flow
* Schema‑aligned logging and opt‑in enforcement
* Ready handoff to **T4 – Instrumentation & Dashboard**.
