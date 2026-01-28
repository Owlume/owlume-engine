import json
from pathlib import Path

PATH = Path("data/logs/clarity_gain_202601.jsonl")

src = PATH.read_text(encoding="utf-8-sig").splitlines()
out_lines = []
changed = 0

for line in src:
    if not line.strip():
        continue
    obj = json.loads(line)

    if "judgment_terminal_state" in obj:
        obj.pop("judgment_terminal_state", None)
        changed += 1

    out_lines.append(json.dumps(obj, ensure_ascii=False))

backup = PATH.with_suffix(".jsonl.bak_rootjts")
backup.write_text("\n".join(src) + "\n", encoding="utf-8-sig")
PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8-sig")

print(f"OK: removed root judgment_terminal_state from {changed} record(s)")
print(f"Backup: {backup}")
