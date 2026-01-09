#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

RISK_BEFORE = re.compile(r"Risk before:\s*([0-9.]+)")
RISK_AFTER  = re.compile(r"Risk after\s*:\s*([0-9.]+)")
IMPROVED    = re.compile(r"Improved\s*:\s*(True|False)")
INTERV      = re.compile(r"^\s*-\s*(.+)$", re.M)

def utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def write_reports(repo_root: Path, run_id: str, input_path: Path, payload: dict) -> tuple[Path, Path]:
    reports = repo_root / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    stem = input_path.stem
    json_path = reports / f"trial_{run_id}__{stem}.json"
    md_path   = reports / f"trial_{run_id}__{stem}.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = []
    md.append(f"# Owlume Trial Run — {run_id}\n")
    md.append(f"- Input: `{input_path}`")
    md.append(f"- Engine: `{payload.get('engine_used')}`")
    md.append(f"- Status: `{payload.get('status')}`\n")

    md.append("## Summary")
    md.append(f"- Frame risk (before): `{payload.get('before_score')}`")
    md.append(f"- Frame risk (after):  `{payload.get('after_score')}`")
    md.append(f"- Improved: `{payload.get('improved')}`\n")

    md.append("## Interventions")
    ints = payload.get("interventions") or []
    if ints:
        for it in ints:
            md.append(f"- {it}")
    else:
        md.append("- (none captured)")
    md.append("")

    if payload.get("error"):
        md.append("## Error")
        md.append("```")
        md.append(payload["error"])
        md.append("```")
        md.append("")

    md.append("## Privacy posture")
    md.append("- All outputs are written locally to `/reports/`.")
    md.append("- No prompts or outputs are transmitted off-machine.\n")

    md_path.write_text("\n".join(md), encoding="utf-8")
    return md_path, json_path

def parse_stdout(out: str) -> dict:
    parsed = {
        "before_score": None,
        "after_score": None,
        "improved": None,
        "interventions": [],
        "stdout_excerpt": out[-4000:] if len(out) > 4000 else out,
    }
    m = RISK_BEFORE.search(out)
    if m:
        parsed["before_score"] = float(m.group(1))
    m = RISK_AFTER.search(out)
    if m:
        parsed["after_score"] = float(m.group(1))
    m = IMPROVED.search(out)
    if m:
        parsed["improved"] = (m.group(1) == "True")

    # Keep only likely intervention lines (contain "->")
    ints = [ln.strip() for ln in INTERV.findall(out)]
    parsed["interventions"] = [x for x in ints if "->" in x]
    return parsed

def main():
    ap = argparse.ArgumentParser(description="Owlume Trial Kit — One-command run (Objective 6)")
    ap.add_argument("--input", required=True, help="Path to .txt prompt (relative to repo root or absolute)")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = (repo_root / input_path).resolve()

    rid = utc_run_id()

    payload = {
        "status": "ok",
        "run_id": rid,
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "repo_root": str(repo_root),
        "input_file": str(input_path),
        "engine_used": "scripts/stage11/run_pipeline_on_samples.py (subprocess)",
        "before_score": None,
        "after_score": None,
        "improved": None,
        "interventions": [],
        "stdout_excerpt": None,
        "error": None,
    }

    try:
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # IMPORTANT: Stage11 runner expects its own sample set; Objective 6 uses your prompt as a standalone sample.
        # We create a temporary one-sample JSON for the pipeline runner.
        tmp_dir = repo_root / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        sample_json = tmp_dir / f"trial_sample_{rid}.json"
        sample_json.write_text(json.dumps([{"id": rid, "text": input_path.read_text(encoding="utf-8")}], indent=2), encoding="utf-8")

        # Call Stage11 pipeline runner and capture stdout
        cmd = [sys.executable, str(repo_root / "scripts" / "stage11" / "run_pipeline_on_samples.py"), "--samples", str(sample_json)]
        proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)

        out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        payload.update(parse_stdout(out))
        payload["stdout_excerpt"] = (out[-4000:] if len(out) > 4000 else out)

        if proc.returncode != 0:
            payload["status"] = "error"
            payload["error"] = f"Stage11 runner exited non-zero ({proc.returncode}). See stdout_excerpt."

    except Exception as e:
        payload["status"] = "error"
        payload["error"] = "".join(traceback.format_exception(type(e), e, e.__traceback__))

    md_path, json_path = write_reports(repo_root, rid, input_path, payload)
    tag = "OK" if payload["status"] == "ok" else "ERROR"
    print(f"[{tag}] Wrote: {md_path}")
    print(f"[{tag}] Wrote: {json_path}")
    sys.exit(0 if payload["status"] == "ok" else 1)

if __name__ == "__main__":
    main()
