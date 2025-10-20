"""
T1 — Elenx Engine Integration (Blueprint)
-----------------------------------------
Repo layout assumed:

/owlume/
├─ data/
│  ├─ matrix.json
│  ├─ voices.json
│  ├─ fallacies.json
│  └─ context_drivers.json
├─ schemas/ (optional for validation)
├─ src/
│  └─ (this file would live here in practice as multiple modules)
└─ scripts/

This blueprint shows how the core Elenx functions connect. It is
implementation-ready scaffolding with TODOs and clear extension points.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import re
import logging

# ----------------------------------------------------------------------------
# 0) Config & Logging
# ----------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent  # assumes /src/ placement
DATA_DIR = ROOT / "data"
SCHEMAS_DIR = ROOT / "schemas"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger("elenx")


# ----------------------------------------------------------------------------
# 1) Data models (typed containers Elenx passes around)
# ----------------------------------------------------------------------------

@dataclass
class ModeGuess:
    mode: str
    confidence: float
    rationale: Optional[str] = None


@dataclass
class PrincipleGuess:
    principle: str
    confidence: float
    rationale: Optional[str] = None


@dataclass
class DiagnosticTags:
    fallacies: List[str] = field(default_factory=list)
    contexts: List[str] = field(default_factory=list)


@dataclass
class VoiceSpec:
    id: str
    style: Dict[str, Any]  # e.g., {"tone": "sharp", "cadence": "brief"}


@dataclass
class Question:
    mode: str
    principle: str
    text: str
    confidence: float
    empathy: bool
    fallacy_tags: List[str]
    context_tags: List[str]
    voice_id: Optional[str] = None


# ----------------------------------------------------------------------------
# 2) Loader — reads JSON packs (and optionally validates)
# ----------------------------------------------------------------------------

class DataLoader:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.matrix: Dict[str, Any] = {}
        self.voices: Dict[str, Any] = {}
        self.fallacies: Dict[str, Any] = {}
        self.context_drivers: Dict[str, Any] = {}

    def _load_json(self, name: str) -> Dict[str, Any]:
        with open(self.data_dir / name, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_all(self) -> None:
        log.info("Loading core JSON packs from %s", self.data_dir)
        self.matrix = self._load_json("matrix.json")
        self.voices = self._load_json("voices.json")
        self.fallacies = self._load_json("fallacies.json")
        self.context_drivers = self._load_json("context_drivers.json")
        log.info("Loaded: matrix=%d modes, voices=%d, fallacies=%d, contexts=%d",
                 len(self.matrix or {}),
                 len(self.voices.get("voices", [])) if self.voices else 0,
                 len(self.fallacies.get("fallacies", [])) if self.fallacies else 0,
                 len(self.context_drivers.get("drivers", [])) if self.context_drivers else 0)

    # Optional: plug a JSON Schema validator here
    # def validate_against_schema(self) -> None:
    #     from jsonschema import validate
    #     ...  # iterate data files vs schemas and raise on errors


# ----------------------------------------------------------------------------
# 3) Priors / Heuristics — fast pre-scan for fallacy & context cues
# ----------------------------------------------------------------------------

class PriorScanner:
    def __init__(self, fallacies_pack: Dict[str, Any], contexts_pack: Dict[str, Any]):
        # Minimal heuristic cues — in production, hydrate from packs (keywords/regex)
        self.fallacy_patterns: List[Tuple[str, re.Pattern]] = []
        self.context_patterns: List[Tuple[str, re.Pattern]] = []
        self._init_from_packs(fallacies_pack, contexts_pack)

    def _init_from_packs(self, fallacies: Dict[str, Any], contexts: Dict[str, Any]):
        # TODO: read cue lists from the packs once defined (e.g., fallacies[].cues[])
        # Below are illustrative placeholders:
        default_fallacies = [
            ("hasty_generalization", re.compile(r"\ball\b|\balways\b|\beveryone\b", re.I)),
            ("false_dilemma", re.compile(r"\beither\b.*\bor\b|\bno other option\b", re.I)),
        ]
        default_contexts = [
            ("incentive_misalignment", re.compile(r"bonus|commission|quota", re.I)),
            ("identity_protection", re.compile(r"reputation|face|embarrass", re.I)),
        ]
        self.fallacy_patterns = default_fallacies
        self.context_patterns = default_contexts

    def scan(self, text: str) -> DiagnosticTags:
        f = [fid for fid, pat in self.fallacy_patterns if pat.search(text)]
        c = [cid for cid, pat in self.context_patterns if pat.search(text)]
        return DiagnosticTags(fallacies=f, contexts=c)


# ----------------------------------------------------------------------------
# 4) Mode/Principle detectors — semantic + linguistic fusion
# ----------------------------------------------------------------------------

class ModeDetector:
    def __init__(self, matrix_pack: Dict[str, Any]):
        self.matrix = matrix_pack
        # TODO: hydrate linguistic cues per Mode from your canonical doc (v0.2 annotated)
        self.cues = {
            "Assumptions": [r"assume", r"probably", r"taken for granted"],
            "Evidence": [r"data", r"study", r"proof", r"source"],
            "Tradeoffs": [r"cost", r"risk", r"opportunity", r"vs\."],
            "SecondOrder": [r"long-term", r"second-order", r"unintended"],
            "Alternatives": [r"option", r"else", r"another way"],
        }

    def detect(self, text: str, prior_bias: float = 0.0) -> ModeGuess:
        # Simple heuristic score by cue hits. Production: LLM or classifier + fusion.
        scores: Dict[str, float] = {}
        for mode, patterns in self.cues.items():
            for pat in patterns:
                if re.search(pat, text, re.I):
                    scores[mode] = scores.get(mode, 0.0) + 1.0
        if not scores:
            # Fallback default (tune as needed)
            return ModeGuess(mode="Assumptions", confidence=0.35, rationale="no-cue-fallback")
        mode, raw = max(scores.items(), key=lambda kv: kv[1])
        conf = min(0.9, 0.5 + 0.1 * raw + 0.25 * prior_bias)  # naive fusion
        return ModeGuess(mode=mode, confidence=conf, rationale=f"cue hits={raw}")


class PrincipleDetector:
    def __init__(self, matrix_pack: Dict[str, Any]):
        self.matrix = matrix_pack
        # TODO: map principles per mode to cues from your Matrix (tightened)
        self.cues = {
            "Evidence": [r"data", r"metrics", r"proof"],
            "Assumptions": [r"assume", r"suppose"],
            "Alternatives": [r"option", r"alternative"],
            "Consequences": [r"impact", r"effect", r"after"],
            "Tradeoffs": [r"cost", r"risk"],
        }

    def detect(self, text: str, mode: str) -> PrincipleGuess:
        # Restrict to principles available under the chosen mode if desired
        scores: Dict[str, float] = {}
        for p, patterns in self.cues.items():
            for pat in patterns:
                if re.search(pat, text, re.I):
                    scores[p] = scores.get(p, 0.0) + 1.0
        if not scores:
            return PrincipleGuess(principle="Evidence", confidence=0.4, rationale="no-cue-fallback")
        principle, raw = max(scores.items(), key=lambda kv: kv[1])
        conf = min(0.9, 0.55 + 0.1 * raw)
        return PrincipleGuess(principle=principle, confidence=conf, rationale=f"cue hits={raw}")


# ----------------------------------------------------------------------------
# 5) Question templates & Voices — renderers
# ----------------------------------------------------------------------------

class QuestionRenderer:
    def __init__(self, matrix_pack: Dict[str, Any], voices_pack: Dict[str, Any]):
        self.matrix = matrix_pack
        self.voices = voices_pack

    def _pick_template(self, mode: str, principle: str) -> str:
        """Pull a template from matrix.json. Expected shape:
        matrix[mode][principle] -> list[str] or str
        """
        try:
            node = self.matrix[mode][principle]
            if isinstance(node, list) and node:
                return node[0]
            if isinstance(node, str):
                return node
        except Exception:
            pass
        # Fallback template
        return "What might you be treating as fact that’s actually untested?"

    def _apply_voice(self, question: str, voice_id: Optional[str]) -> Tuple[str, Optional[str]]:
        if not voice_id:
            return question, None
        # TODO: use voices.json to transform wording/cadence.
        # For now, return unchanged.
        return question, voice_id

    def render(self, mode: str, principle: str, voice_id: Optional[str] = None) -> str:
        template = self._pick_template(mode, principle)
        q, _ = self._apply_voice(template, voice_id)
        return q


# ----------------------------------------------------------------------------
# 6) Empathy overlay — tone modulation based on cues
# ----------------------------------------------------------------------------

class EmpathyOverlay:
    def __init__(self):
        # TODO: hydrate empathy triggers from your Empathy Lens doc
        self.triggers = [re.compile(r"worried|anxious|conflict|tension|feel", re.I)]

    def should_apply(self, text: str) -> bool:
        return any(p.search(text) for p in self.triggers)

    def apply(self, question: str) -> str:
        # Light, non-preachy softener
        if question.lower().startswith("what"):
            return "If it helps, " + question[0].lower() + question[1:]
        return "If it helps, " + question


# ----------------------------------------------------------------------------
# 7) The Pipeline — generate blind-spot questions end-to-end
# ----------------------------------------------------------------------------

class ElenxEngine:
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.priors = PriorScanner(loader.fallacies, loader.context_drivers)
        self.mode_detector = ModeDetector(loader.matrix)
        self.principle_detector = PrincipleDetector(loader.matrix)
        self.renderer = QuestionRenderer(loader.matrix, loader.voices)
        self.empathy = EmpathyOverlay()

    def generate(self, text: str, n: int = 3, force_voice: Optional[str] = None) -> List[Question]:
        # 1) pre-scan priors
        tags = self.priors.scan(text)
        prior_bias = 0.15 if (tags.fallacies or tags.contexts) else 0.0

        # 2) detect mode/principle (fusion could incorporate LLM scores later)
        mode_guess = self.mode_detector.detect(text, prior_bias=prior_bias)
        principle_guess = self.principle_detector.detect(text, mode_guess.mode)

        # 3) render questions (could produce variations)
        qs: List[Question] = []
        for i in range(n):
            q_text = self.renderer.render(mode_guess.mode, principle_guess.principle, force_voice)

            # 4) empathy overlay (conditional)
            applied_empathy = False
            if self.empathy.should_apply(text):
                q_text = self.empathy.apply(q_text)
                applied_empathy = True

            qs.append(
                Question(
                    mode=mode_guess.mode,
                    principle=principle_guess.principle,
                    text=q_text,
                    confidence=round((mode_guess.confidence + principle_guess.confidence) / 2, 3),
                    empathy=applied_empathy,
                    fallacy_tags=tags.fallacies,
                    context_tags=tags.contexts,
                    voice_id=force_voice,
                )
            )

        # 5) (Optional) dedupe/format variations here
        return qs


# ----------------------------------------------------------------------------
# 8) Example wiring — how a CLI / service would call this
# ----------------------------------------------------------------------------

def bootstrap_engine() -> ElenxEngine:
    loader = DataLoader(DATA_DIR)
    loader.load_all()
    # loader.validate_against_schema()  # optional safety gate
    engine = ElenxEngine(loader)
    return engine


def demo_run():
    engine = bootstrap_engine()

    user_text = (
        "I’m worried our launch team is rushing. Everyone keeps saying there’s no other option "
        "but to ship next week, even without solid data on failure rates."
    )
    results = engine.generate(user_text, n=3, force_voice=None)

    print("\nINPUT:\n", user_text)
    print("\nOUTPUT QUESTIONS:")
    for i, q in enumerate(results, 1):
        print(f" {i}. ({q.mode} × {q.principle}, conf={q.confidence}) {q.text}")
        if q.fallacy_tags or q.context_tags:
            print(f"    tags: fallacies={q.fallacy_tags} contexts={q.context_tags}")


if __name__ == "__main__":
    demo_run()
