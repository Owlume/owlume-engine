"""
Stage 14 — Policy Fingerprinting (Audit Hashes)

Computes deterministic sha256 fingerprints over canonical policy artifacts.
Used to bind governance events (e.g., BLOCK) to the exact policy state that
authorized them.

Primary target:
- /data/policy/stage14_action_gating_table.v1.json

Optional targets:
- /data/policy/stage14_block_negative_rules.v1.json
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import hashlib
import json


def _repo_root() -> Path:
    # /src/governance/policy_fingerprint.py -> repo root is two levels up
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _canonical_json_bytes(obj: Any) -> bytes:
    """
    Produce canonical bytes for hashing:
    - sorted keys
    - no insignificant whitespace
    - stable UTF-8 encoding
    """
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Stage14PolicyFingerprints:
    action_gating_table_sha256: str
    block_negative_rules_sha256: str


def compute_stage14_policy_fingerprints(
    action_table_path: Path | None = None,
    negative_rules_path: Path | None = None,
) -> Stage14PolicyFingerprints:
    root = _repo_root()
    at_path = action_table_path or (root / "data" / "policy" / "stage14_action_gating_table.v1.json")
    nr_path = negative_rules_path or (root / "data" / "policy" / "stage14_block_negative_rules.v1.json")

    action_table = _load_json(at_path)
    negative_rules = _load_json(nr_path)

    # Hash the canonical JSON forms (stable across formatting differences).
    at_hash = sha256_hex(_canonical_json_bytes(action_table))
    nr_hash = sha256_hex(_canonical_json_bytes(negative_rules))

    return Stage14PolicyFingerprints(
        action_gating_table_sha256=at_hash,
        block_negative_rules_sha256=nr_hash,
    )


def compute_action_gating_table_hash(action_table_path: Path | None = None) -> str:
    """
    Convenience helper: returns sha256 hex for the action-gating table.
    """
    fps = compute_stage14_policy_fingerprints(action_table_path=action_table_path)
    return fps.action_gating_table_sha256
