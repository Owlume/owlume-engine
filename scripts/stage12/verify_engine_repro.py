#!/usr/bin/env python3
"""
Stage 12 — Engine Reproducibility Contract (ERC) verifier

Runs the minimal reproducibility surface as a single command:
  1) validate_packs
  2) reproduce_baseline (byte-identical)
  3) engine fusion smoke test

Exit code:
  0 = all checks passed
  non-zero = at least one check failed
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: List[str], extra_env: dict | None = None) -> int:
    env = os.environ.copy()

    # Import-resolution shim (no behavior change): add repo root and src to PYTHONPATH
    py_path = env.get("PYTHONPATH", "")
    parts = [p for p in py_path.split(os.pathsep) if p]
    want = [str(REPO_ROOT), str(REPO_ROOT / "src")]
    for w in want:
        if w not in parts:
            parts.insert(0, w)
    env["PYTHONPATH"] = os.pathsep.join(parts)

    if extra_env:
        env.update(extra_env)

    print("\n" + "=" * 78)
    print("[RUN]", " ".join(cmd))
    print("=" * 78)
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env)
    return int(completed.returncode)


def main() -> int:
    print("=" * 78)
    print("Owlume — Engine Reproducibility Contract (ERC) verifier")
    print(f"Repo root : {REPO_ROOT}")
    print(f"Python    : {sys.version.split()[0]} ({sys.executable})")
    print(f"OS        : {platform.system()} {platform.release()} ({platform.machine()})")
    print("=" * 78)

    checks: List[Tuple[str, List[str]]] = [
        ("validate_packs", [sys.executable, "-u", "scripts/validate_packs.py"]),
        ("reproduce_baseline", [sys.executable, "-u", "scripts/stage11/reproduce_baseline.py"]),
        ("smoke_test_engine_fusion", [sys.executable, "-u", "scripts/smoke_test_engine_fusion.py"]),
    ]

    for name, cmd in checks:
        rc = _run(cmd)
        if rc != 0:
            print(f"\n[FAIL] ERC check failed: {name} (exit={rc})")
            return rc
        print(f"\n[OK] ERC check passed: {name}")

    print("\n" + "=" * 78)
    print("[OK] Engine Reproducibility Contract PASSED (all checks).")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
