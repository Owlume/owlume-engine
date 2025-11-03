# src/adapters/owlume_sdk_stub_handler.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Callable, Dict, Any

from jsonschema import Draft7Validator

SCHEMA_PATH = Path("schemas/owlume_sdk_stub.schema.json")
SCHEMA_REF = "https://owlume/schemas/owlume_sdk_stub.schema.json"

class OwlumeSDKHandler:
    def __init__(self, partner_id: str, terms_version: str = "2025-10-01"):
        self.partner_id = partner_id
        self.terms_version = terms_version
        self._validator = self._load_validator()

    def _load_validator(self) -> Draft7Validator:
        with SCHEMA_PATH.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        Draft7Validator.check_schema(schema)
        return Draft7Validator(schema)

    def validate(self, envelope: Dict[str, Any]) -> None:
        errors = list(self._validator.iter_errors(envelope))
        if errors:
            msgs = []
            for e in errors[:5]:
                path = "$" + "".join([f"[{repr(p)}]" if isinstance(p, int) else f".{p}" for p in e.path])
                msgs.append(f"{path}: {e.message}")
            raise ValueError("Schema violation(s):\n  - " + "\n  - ".join(msgs))

    def build_response(
        self,
        reciprocity_id: str,
        did: str,
        processed: Dict[str, Any],
        trust_from_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "$schema": SCHEMA_REF,
            "spec": {"version": "v0.1", "channel": "sdk-stub", "partner_id": self.partner_id},
            "trust": trust_from_request,
            "output": {
                "reciprocity_id": reciprocity_id,
                "did": did,
                **processed
            }
        }

    def process_input(
        self,
        envelope: Dict[str, Any],
        processor: Callable[[str], Dict[str, Any]],
        did_factory: Callable[[str], str],
    ) -> Dict[str, Any]:
        """Validate request envelope, process text via `processor`, and return response envelope."""
        self.validate(envelope)
        if envelope.get("input") is None:
            raise ValueError("Envelope must include `input` for analysis requests.")
        inp = envelope["input"]
        reciprocity_id = inp["reciprocity_id"]
        text = inp["text"]
        trust = envelope.get("trust", {})

        processed = processor(text)
        did = did_factory(reciprocity_id)

        resp = self.build_response(reciprocity_id, did, processed, trust)
        # Validate the outgoing response too (defensive)
        self.validate(resp)
        return resp
