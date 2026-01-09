# Owlume Trial Kit — Quickstart (Objective 6)

Goal: a non-technical user can run Owlume locally with one command and see outputs in `/reports/`.

## What happens
- You provide a plain-text prompt (`.txt`).
- Owlume runs the Stage 11 “Frame Audit + Intervention” pipeline locally.
- Owlume writes:
  - a human-readable Markdown report
  - a machine-readable JSON result

Nothing is sent off-machine.

---

## Requirements
- Python 3.11+ (recommended: 3.12/3.13)
- Git (to clone)

---

## Install (Windows)
PowerShell:

```powershell
git clone <REPO_URL>
cd owlume-engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
# If requirements exist in your repo:
# pip install -r requirements.txt
