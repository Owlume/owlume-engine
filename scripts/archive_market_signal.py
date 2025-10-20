#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Move a resolved market-signal doc into /archive/market_signals/,
rename it with YYYYMMDD_..._resolved.md, and append a summary line
to /archive/market_signals/README.md.
"""
import argparse, re, shutil
from pathlib import Path
from datetime import datetime

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\s_-]+", "", s)
    s = re.sub(r"[\s-]+", "_", s)
    return s or "signal"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to the source market-signal Markdown file in /docs/")
    parser.add_argument("--name", required=True, help="Signal name (for archive row)")
    parser.add_argument("--category", required=True, help="Category (Competition / UX Trend / Behavioral Shift / Ecosystem / Technology)")
    parser.add_argument("--outcome", required=True, help="Outcome/Lesson short note for the archive table")
    args = parser.parse_args()

    # Resolve repo root (…/scripts -> repo)
    scripts_dir = Path(__file__).resolve().parent
    repo_root = scripts_dir.parent

    src_path = (repo_root / args.source).resolve()
    if not src_path.exists():
        raise SystemExit(f"Source not found: {src_path}")

    archive_dir = (repo_root / "archive" / "market_signals")
    archive_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    slug = slugify(args.name)
    dest_name = f"{today}_{slug}_resolved.md"
    dest_path = archive_dir / dest_name

    shutil.move(str(src_path), str(dest_path))

    # Update archive README table
    readme = archive_dir / "README.md"
    if not readme.exists():
        # minimal README if missing
        readme.write_text(
            "# Archived Market Signals\n\n"
            "## 🧾 Archived Index\n\n"
            "| Archived On | Signal Name | Category | Outcome / Lesson |\n"
            "|--------------|--------------|-----------|------------------|\n",
            encoding="utf-8"
        )

    archived_on = f"{today[:4]}-{today[4:6]}-{today[6:]}"
    row = f"| {archived_on} | {args.name} | {args.category} | {args.outcome} |\n"

    with readme.open("a", encoding="utf-8") as f:
        f.write(row)

    print("✅ Archived:")
    print(f"  Moved: {dest_path.name}")
    print(f"  Added row → archive/market_signals/README.md")
    print(f"  Row: {row.strip()}")

if __name__ == "__main__":
    main()
