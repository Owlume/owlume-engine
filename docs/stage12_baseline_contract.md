# Stage 12 — Baseline Reproducibility Contract (v1)

## Purpose

Stage 12 establishes a *reproducibility contract* for Owlume’s Stage 11 baseline: the system must be able to re-run the Stage 11 pipeline and reproduce the baseline snapshot **byte-identically**, both locally and in CI.  

This contract exists to prevent “silent drift” — changes that appear harmless but subtly alter the evaluator, trace, scoring, or outputs.

---

## Contract: What must always remain true

### The invariant
Running the reproduction script must produce a snapshot that is **byte-identical** to the golden baseline:

- **Golden baseline:** `data/golden/stage11_baseline_snapshot.json`
- **Repro output:** `reports/stage12_repro_snapshot.json`

The script must end with an explicit success statement (or equivalent) confirming byte-identity.

### The canonical reproducer
- `scripts/stage11/reproduce_baseline.py`

This is the only approved “source of truth” for reproducing the baseline.

---

## CI enforcement

### Where CI enforces the contract
The baseline reproduction contract runs from:

- `.github/workflows/validate.yml`

Within that workflow, the contract step is labeled:

- `Stage 12 — Reproduce Stage 11 baseline (contract)`

and it executes:

- `PYTHONPATH="." python -u scripts/stage11/reproduce_baseline.py`

### What must be required for merges
Branch protection for `main` must require the CI check that contains the reproduction contract step.

In this repo, the job names in `validate.yml` are:

- **Validate JSON & Schemas** (contains the Stage 12 contract step)
- **Re-run Smoke Test (Elenx Fusion)**

At minimum, the required checks must include **Validate JSON & Schemas**.

---

## Local verification (one command)

Run from repo root:

```powershell
$env:PYTHONPATH="."
python scripts/stage11/reproduce_baseline.py
<paste the full markdown here>

Expected outcome:

script prints that it reproduced Stage 11 baseline snapshot exactly

it writes:

reports/stage12_repro_snapshot.json

and confirms it is byte-identical to:

data/golden/stage11_baseline_snapshot.json

This local check is the fastest “trust anchor” before any merge.

Merge policy (operational)
Default merge rule

No PR merges into main unless:

CI checks are green, AND

the baseline reproduction contract check has run and passed, AND

branch is up-to-date (no stale merge base)

Practical discipline

Before merging any meaningful change, run the local verification command above.
If it fails locally, do not “try to fix CI.” Fix the underlying drift first.

Forbidden actions (high-risk)

Do not do the following unless you are intentionally changing the baseline (see next section):

Do not manually edit:

data/golden/stage11_baseline_snapshot.json

Do not change baseline reproduction behavior casually:

scripts/stage11/reproduce_baseline.py

Do not weaken merge gates:

required checks, PR requirement, “up to date” requirement

Do not “fix” a failing repro by replacing the golden file without justification

These are the most common ways teams accidentally destroy reproducibility.

Intentional baseline update procedure (rare, controlled)

Baseline updates are allowed only when:

there is a deliberate evaluator / scoring / policy change, AND

you can explain why the old baseline is no longer correct, AND

you are prepared to defend the change with evidence.

Step-by-step procedure

Create a branch

git checkout -b chore/update-stage11-baseline


Run the reproducer

$env:PYTHONPATH="."
python scripts/stage11/reproduce_baseline.py


If repro differs, confirm it is intentional

Identify what changed and why it should change.

Capture evidence (logs, report diffs, risk deltas) as needed.

Update baseline only via controlled file replacement

If the new snapshot is the intended baseline, replace the golden file using a deliberate copy action:

Copy-Item reports\stage12_repro_snapshot.json data\golden\stage11_baseline_snapshot.json


Re-run repro to confirm new baseline is stable

python scripts/stage11/reproduce_baseline.py


Commit with an explicit message

Message must include rationale:

what changed

why baseline needed updating

what evidence supports it

Open PR

PR description must include:

reason for baseline update

link to CI run

any supporting reports/diffs

Hard rule

If you cannot explain why the baseline changed, you are not allowed to update it.

Troubleshooting (common failure modes)
“Byte-identical” fails locally

Check that you are on the intended branch and up to date:

git status
git pull


Confirm Python path is set as expected:

$env:PYTHONPATH="."


Re-run:

python scripts/stage11/reproduce_baseline.py

CI passes but baseline contract wasn’t enforced

This indicates branch protection required checks are misconfigured.

Ensure Validate JSON & Schemas is explicitly required for merges.

Summary

Stage 12 is not “extra tests.”
Stage 12 is a contract: the baseline must be reproducible, and merges must be gated by that reproducibility.

If this contract holds, Owlume can evolve without losing its core correctness anchor.


---


If you want this even more “bulletproof,” the only addition I’d recommend is a short appendix listing the exact branch protection settings you enabled (PR required, up-to-date, required checks). But the document above is already sufficient as Objective 3.
