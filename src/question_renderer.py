# src/question_renderer.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import re
import time
import uuid

# -------- helpers --------

_SLUG_RE = re.compile(r"[^a-z0-9]+")

def slugify(text: str) -> str:
    s = text.strip().lower()
    s = _SLUG_RE.sub("-", s).strip("-")
    return s or "na"

def now_iso() -> str:
    # Seconds precision is enough; UI can format locally
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

# -------- public dataclasses --------

@dataclass
class UIPayload:
    """Minimal, stable payload for Owlume’s UI."""
    id: str                    # e.g., "qpack-<uuid>"
    created_at: str            # ISO UTC
    mode_id: str               # slug of mode label
    mode_label: str
    principle_id: str          # slug of principle label
    principle_label: str
    confidence: float          # overall fused confidence
    empathy_on: bool
    tags: Dict[str, List[str]] # {"fallacies": [...], "contexts": [...]}
    questions: List[Dict[str, Any]]  # [{"id","text","order"}]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# -------- rendering API --------

def render_question_pack(
    *,
    mode_label: str,
    principle_label: str,
    questions: List[str],
    confidence: float,
    empathy_on: bool,
    tags: Dict[str, List[str]],
) -> UIPayload:
    """
    Turn Engine Shim outputs into a UI pack with stable IDs and clean structure.
    IDs are slugs + short uuid to avoid collisions if labels change in future.
    """
    mode_id = slugify(mode_label)
    principle_id = slugify(f"{mode_label}--{principle_label}")
    pack_id = f"qpack-{uuid.uuid4().hex[:12]}"

    q_items: List[Dict[str, Any]] = []
    for i, q in enumerate(questions, 1):
        q_items.append({
            "id": f"q-{mode_id}-{principle_id}-{i}",
            "text": q.strip(),
            "order": i
        })

    return UIPayload(
        id=pack_id,
        created_at=now_iso(),
        mode_id=mode_id,
        mode_label=mode_label,
        principle_id=principle_id,
        principle_label=principle_label,
        confidence=round(float(confidence), 2),
        empathy_on=bool(empathy_on),
        tags=tags or {"fallacies": [], "contexts": []},
        questions=q_items
    )
