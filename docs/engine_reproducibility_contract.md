# Owlume Engine Reproducibility Contract (ERC)

## Purpose
Define *exactly* what “engine is reproducible” means for Owlume at this stage, in a way that is:
- testable (pass/fail),
- stable (minimal surface area),
- identical locally and in CI.

This contract exists to prevent overclaiming prior to external trials.

## Scope (What is guaranteed reproducible)
Given:
- a fresh clone of this repo at a specific commit,
- Python 3.13,
- dependencies installed per this repo’s instructions,

The following are guaranteed to run successfully on:
- Windows (CI: windows-latest)
- Ubuntu (CI: ubuntu-latest)

### ERC Checks
1) Pack validation
- Command: `python scripts/validate_packs.py`
- Meaning: JSON data packs validate against schemas; loader expectations remain coherent.

2) Stage 11 baseline reproduction contract
- Command: `python scripts/stage11/reproduce_baseline.py`
- Meaning: Produces the Stage 12 reproduction snapshot and verifies it is byte-identical to the golden Stage 11 baseline snapshot.

3) Engine fusion smoke test
- Command: `python scripts/smoke_test_engine_fusion.py`
- Meaning: Engine-level wiring is operational (loader + hybrid fusion path), and the smoke test completes successfully.

## Single-command verification (local = CI)
Preferred command:
- `python scripts/stage12/verify_engine_repro.py`

This runs the three ERC checks above in order and exits non-zero on failure.

## Expected local outputs
Running the contract may create or update artifacts under:
- `/reports/` (human-readable and machine-readable outputs)

These files are outputs and are not intended to be committed.

## Explicit non-goals (What is NOT guaranteed)
The ERC does NOT guarantee:
- identical runtime performance, latency, or memory usage across machines,
- determinism for any non-contract scripts not listed above,
- dashboard rendering identity, visualization pixel-perfect stability, or UI parity,
- reproducibility under Python versions other than 3.13,
- reproducibility if dependencies are altered outside the repo’s supported install path.

## Contract change policy
Any change to:
- the list of ERC checks,
- pass/fail criteria,
- or the wrapper’s behavior
must be made intentionally, reviewed, and validated on both OSes in CI.

Reason: external trials depend on this contract to define “what success means.”
