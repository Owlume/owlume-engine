# src/clarity_logger.py
from __future__ import annotations
import json, os, datetime
from typing import Dict, Any
from jsonschema import validate, Draft7Validator

def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load and return a JSON schema object."""
    return _read_json(schema_path)

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Raise ValueError with readable messages if record fails validation."""
    v = Draft7Validator(schema)
    errors = sorted(v.iter_errors(record), key=lambda e: e.path)
    if errors:
        msgs = "\n".join([f"- {'/'.join([str(p) for p in e.path])}: {e.message}" for e in errors])
        raise ValueError(f"Record failed schema validation:\n{msgs}")

def make_session_id(prefix: str = "DLM") -> str:
    """Generate a readable, time-stamped session id (Sydney local time ok)."""
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{ts}"

def log_record(record: Dict[str, Any], logs_dir: str = "data/logs") -> str:
    """Append the record to the current month JSONL and return the file path."""
    _ensure_dir(logs_dir)
    month = datetime.datetime.now().strftime("%Y%m")
    path = os.path.join(logs_dir, f"clarity_gain_{month}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path

