# src/elenx_engine.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import re, json

# -- Coerce context drivers pack into {"drivers":[...]}, robust to dict/tuple/list/JSON
def _coerce_context_pack(raw) -> Dict[str, Any]:
    import json as _json

    def _from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(d.get("drivers"), list):
            return {"drivers": d["drivers"]}
        # sometimes the list is under a different key like "items"
        if isinstance(d.get("items"), list):
            return {"drivers": d["items"]}
        # try to find any list that looks like drivers
        for k, v in d.items():
            if isinstance(v, list) and any(isinstance(x, dict) and ("label" in x or "name" in x) for x in v):
                return {"drivers": v}
        return {"drivers": []}

    if raw is None:
        return {"drivers": []}

    # direct dict
    if isinstance(raw, dict):
        return _from_dict(raw)

    # list/tuple: could be a list of drivers or contain a dict/JSON-string
    if isinstance(raw, (list, tuple)):
        # case: list of driver dicts
        if all(isinstance(x, dict) and ("label" in x or "name" in x) for x in raw):
            return {"drivers": list(raw)}
        # case: contains a dict with "drivers"
        for item in raw:
            if isinstance(item, dict):
                d = _from_dict(item)
                if d["drivers"]:
                    return d
            if isinstance(item, str):
                s = item.strip()
                if s and s[0] in "{[":
                    try:
                        parsed = _json.loads(s)
                        d = _coerce_context_pack(parsed)
                        if d["drivers"]:
                            return d
                    except Exception:
                        pass
        return {"drivers": []}

    # JSON string
    if isinstance(raw, str):
        s = raw.strip()
        if s and s[0] in "{[":
            try:
                parsed = _json.loads(s)
                return _coerce_context_pack(parsed)
            except Exception:
                return {"drivers": []}
        return {"drivers": []}

    return {"drivers": []}


# --- Context driver detection (label-aware, low-regret) ---
def _detect_context_drivers(text: str, drivers_pack: Dict[str, Any]) -> List[str]:
    """
    Heuristic detector that matches common cues in the user text
    to *existing* driver labels from your pack. It avoids
    hardcoding label names — if a label isn’t present, it’s skipped.
    """
    t = (text or "").lower()
    labels = [d.get("label", "") for d in (drivers_pack or {}).get("drivers", [])]

    found: List[str] = []

    # 1) Incentive Misalignment
    if any(k in t for k in ["incentive", "commission", "bonus", "quota", "kpi", "target mis", "misaligned", "perverse incentive"]):
        for lab in labels:
            if "incent" in lab.lower():  # matches "Incentive Misalignment"
                found.append(lab)

    # 2) Stakeholder / interpersonal pressure
    if any(k in t for k in ["stakeholder", "co-founder", "cofounder", "boss", "board", "investor", "client", "customer", "sales", "product", "team", "engineering", "marketing", "cross-functional"]):
        stake = next((lab for lab in labels if "stakeholder" in lab.lower()), None)
        if stake:
            found.append(stake)

    # 3) Time Pressure / Overload
    if any(k in t for k in ["time pressure", "deadline", "rushed", "rush", "overload", "burnout", "too busy", "no time"]):
        for lab in labels:
            lo = lab.lower()
            if "time" in lo or "pressure" in lo or "overload" in lo:
                found.append(lab)

    # 4) Conflict / Tension
    if any(k in t for k in ["conflict", "tension", "strained", "friction", "distant", "avoid", "avoidance"]):
        rel = next((lab for lab in labels if any(x in lab.lower() for x in ["relationship", "interpersonal", "people", "conflict"])), None)
        if rel:
            found.append(rel)

    # Deduplicate while preserving order
    out: List[str] = []
    seen = set()
    for f in found:
        if f and f not in seen:
            out.append(f)
            seen.add(f)
    return out


# --- Linguistic cue dictionaries (coverage for all modes) ---
LINGUISTIC_CUES = {
    "Creative": [
        r"\bbrainstorm\b", r"\bnew approach\b", r"\bnovel\b", r"\bidea(s)?\b",
        r"\bimagin(e|ation|ative)\b", r"\bwhat if\b", r"\bpossibilit(y|ies)\b",
        r"\bprototype\b", r"\bgreenfield\b", r"\bblue sky\b", r"\bconcept\b"
    ],
    "Reflective": [
        r"\bregret(s|ted|ting)?\b", r"\bhindsight\b", r"\bpattern(s)?\b",
        r"\blesson(s)?\b", r"\blearned\b", r"\bintrospect(ion|ive)?\b",
        r"\blooking back\b", r"\brecap\b", r"\breflection\b"
    ],
    "Growth": [
        r"\bhabit(s)?\b", r"\bmindset\b", r"\bdevelop(ment|ing)?\b",
        r"\bfeedback\b", r"\bcoach(ing)?\b", r"\bevolv(e|ing|ed)\b",
        r"\bimprov(e|ing|ement)\b", r"\bpractice\b", r"\broutine\b"
    ],
    "Analytical": [
        r"\bevidence\b", r"\bvalidate|validation\b", r"\bmetric(s)?\b",
        r"\btrade[- ]?off(s)?\b", r"\bmodel\b", r"\bassumption(s)?\b",
        r"\btest\b", r"\bexperiment\b", r"\bproof\b", r"\bdata\b"
    ],
    "Critical": [
        r"\bincentive(s)?\b", r"\bbias\b", r"\brisk(s)?\b", r"\bsecond[- ]order\b",
        r"\bconflict\b", r"\bcontradict\b", r"\bchallenge\b", r"\bpressure\b"
    ],
}

def _softmax(scores: Dict[str, float]) -> Dict[str, float]:
    import math
    if not scores:
        return {}
    mx = max(scores.values())
    exps = {k: math.exp(v - mx) for k, v in scores.items()}
    s = sum(exps.values())
    return {k: (exps[k] / s) for k in exps}


@dataclass
class DetectionResult:
    mode: str
    principle: str
    confidence: float
    priors_used: bool
    empathy_on: bool
    tags: Dict[str, List[str]]  # {"fallacies": [...], "contexts": [...]}
    alt_mode: str | None = None
    alt_principle: str | None = None
    alt_confidence: float | None = None


class ElenxEngine:
    """
    Owlume engine:
    - Robust Matrix handling (dict/tuple/list/JSON string) + ignores '$schema'
    - Detection tuned to your modes (Analytical/Critical/Creative/Reflective/Growth)
    - Questions from Matrix with Thiel / Peterson / Feynman voice overlays
    - Contextual follow-up if incentives/stakeholders/risk are detected
    """

    def __init__(self, packs: Dict[str, Any]):
        # Raw packs (loader may pass dict/tuple/list/str)
        self._matrix_raw: Any = packs.get("matrix", {}) or {}
        self.voices: Dict[str, Any] = packs.get("voices", {}) or {}
        self.fallacies_pack: Dict[str, Any] = packs.get("fallacies", {}) or {}
        _raw_ctx = packs.get("context_drivers", {}) or {}
        self.context_pack: Dict[str, Any] = _coerce_context_pack(_raw_ctx)
        self.context_drivers: Dict[str, Any] = self.context_pack  # alias for clarity
        self.context_drivers: Dict[str, Any] = self.context_pack

        # Config
        self.cfg: Dict[str, Any] = {}
        self.cfg.update({
            "LINGUISTIC_STARTER_CONF": 0.60,   # starter confidence for cue-detected mode
            "LINGUISTIC_MAX_BOOST": 0.15,      # cap how much cues can boost
            "LINGUISTIC_MIN_MATCHES": 1,       # at least N regex matches to count
        })

        # Preferred mode bias (your Matrix order)
        self._preferred_modes = ["Analytical", "Critical", "Creative", "Reflective", "Growth"]

        # Defaults from coerced + filtered matrix
        matrix = self._matrix()
        if self._valid_modes(matrix):
            self._default_mode, self._default_principle = self._first_mode_principle(matrix)
        else:
            self._default_mode, self._default_principle = "Analytical", "Evidence & Validation"

    # ---------- Linguistic cues ----------

    def _score_linguistic_mode(self, text: str) -> Dict[str, float]:
        """
        Returns a dict of mode -> normalized cue score based on regex hits.
        We keep it simple/robust: count distinct pattern hits (0/1 per pattern), then softmax.
        """
        text_l = (text or "").lower()
        raw: Dict[str, float] = {}
        for mode, patterns in LINGUISTIC_CUES.items():
            hits = 0
            for pat in patterns:
                if re.search(pat, text_l):
                    hits += 1
            if hits >= self.cfg["LINGUISTIC_MIN_MATCHES"]:
                raw[mode] = float(hits)
        return _softmax(raw)

    # ---------- Public API ----------

    def analyze(self, text: str, empathy_on: bool = True) -> Tuple[DetectionResult, List[str]]:
        text = (text or "").strip()

        # 1️⃣ Pre-scan for priors
        tags, priors_used = self._pre_scan_priors(text)

        # 2️⃣ Semantic detection
        mode, principle, confidence, alt_stub = self._detect_mode_principle(text)

        # 3️⃣ Context driver detection (NEW)
        contexts = _detect_context_drivers(text, self.context_drivers)
        if "contexts" in tags:
            tags["contexts"].extend(x for x in contexts if x not in tags["contexts"])
        else:
            tags["contexts"] = contexts
        tags.setdefault("fallacies", [])

        # 4️⃣ Assemble DetectionResult
        det = DetectionResult(
            mode=mode or self._default_mode,
            principle=principle or self._default_principle,
            confidence=confidence,
            priors_used=priors_used,
            empathy_on=empathy_on,
            tags=tags,
            alt_mode=alt_stub.get("alt_mode"),
            alt_principle=alt_stub.get("alt_principle"),
            alt_confidence=alt_stub.get("alt_confidence"),
        )

        # 5️⃣ Render questions
        questions = self._render_questions(det)
        return det, questions

    # ---------- Matrix coercion & filtering ----------

    def _matrix(self) -> Dict[str, Dict[str, str]]:
        """
        Coerce loader output into {mode: {principle: question}} dict.
        Accepts dict, JSON string, or (tuple/list) holding a dict/JSON string.
        """
        m = self._matrix_raw

        # Direct dict
        if isinstance(m, dict):
            return m

        # JSON string
        if isinstance(m, str):
            s = m.strip()
            if s and s[0] in "{[":
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, dict):
                        return parsed
                    if isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict):
                                return item
                except Exception:
                    return {}
            return {}

        # Tuple/list that may hold dict or JSON string
        if isinstance(m, (tuple, list)):
            for item in m:
                if isinstance(item, dict):
                    return item
                if isinstance(item, str):
                    s = item.strip()
                    if s and s[0] in "{[":
                        try:
                            parsed = json.loads(s)
                            if isinstance(parsed, dict):
                                return parsed
                        except Exception:
                            continue
        return {}

    def _valid_modes(self, matrix: Dict[str, Any]) -> List[str]:
        """Only real modes: dict values, non-empty, key not starting with '$'."""
        if not isinstance(matrix, dict):
            return []
        out: List[str] = []
        for k, v in matrix.items():
            try:
                if isinstance(v, dict) and v and not str(k).strip().startswith("$"):
                    out.append(k)
            except Exception:
                continue
        return out

    def _first_mode_principle(self, matrix: Dict[str, Dict[str, str]]) -> Tuple[str, str]:
        modes = self._valid_modes(matrix)
        if not modes:
            return "Analytical", "Evidence & Validation"
        # Use preferred order if possible
        for pm in self._preferred_modes:
            if pm in modes:
                mode = pm
                break
        else:
            mode = modes[0]
        principles = matrix.get(mode, {})
        if isinstance(principles, dict) and principles:
            principle = next(iter(principles.keys()))
        else:
            principle = "Evidence & Validation"
        return mode, principle

    # ---------- Priors scan (light) ----------

    def _pre_scan_priors(self, text: str) -> Tuple[Dict[str, List[str]], bool]:
        t = (text or "").lower()
        contexts: List[str] = []
        if re.search(r"\b(incentive|bonus|commission|quota|kpi)\b", t):
            contexts.append("Incentive (generic)")
        if re.search(r"\b(stakeholder|board|investor|customer|team|ops|legal)\b", t):
            contexts.append("Stakeholder (generic)")
        if re.search(r"\b(risk|downside|exposure|liability|compliance|safety)\b", t):
            contexts.append("Risk (generic)")

        fallacies: List[str] = []
        try:
            falls = (self.fallacies_pack or {}).get("fallacies", [])
            if re.search(r"\b(always|everyone|nobody|never)\b", t):
                hg = next((f.get("label") for f in falls if "Generalization" in (f.get("label") or "")), None)
                if hg:
                    fallacies.append(hg)
        except Exception:
            pass

        return {"contexts": contexts, "fallacies": fallacies}, bool(contexts or fallacies)

    # ---------- Detection ----------

    def _pick_from_matrix(self, pref_mode_contains: Optional[str], pref_principle_contains: Optional[str]) -> Tuple[str, str]:
        """
        SAFE: choose a Mode × Principle using coerced + filtered matrix.
        Falls back cleanly and honors preferred modes.
        """
        matrix = self._matrix()
        valid_modes = self._valid_modes(matrix)
        if not valid_modes:
            return self._default_mode, self._default_principle

        # 1) Mode selection
        chosen_mode = None
        # a) explicit hint wins if it matches
        if pref_mode_contains:
            for m in valid_modes:
                try:
                    if pref_mode_contains.lower() in m.lower():
                        chosen_mode = m
                        break
                except Exception:
                    continue
        # b) otherwise, use preferred ordering if present
        if not chosen_mode:
            for pm in self._preferred_modes:
                if pm in valid_modes:
                    chosen_mode = pm
                    break
        # c) final fallback = first valid
        if not chosen_mode:
            chosen_mode = valid_modes[0]

        # 2) Principle selection within chosen mode
        chosen_principle = None
        principles = matrix.get(chosen_mode, {})
        if isinstance(principles, dict) and pref_principle_contains:
            for p in principles.keys():
                try:
                    if pref_principle_contains.lower() in p.lower():
                        chosen_principle = p
                        break
                except Exception:
                    continue
        if not isinstance(principles, dict) or not principles:
            return chosen_mode, self._default_principle
        if not chosen_principle:
            chosen_principle = next(iter(principles.keys()), self._default_principle)

        return chosen_mode, chosen_principle

    def _pick_from_matrix_any(self, mode_hint: Optional[str], principle_hints: List[str]) -> Tuple[str, str]:
        """
        Try multiple principle hints; if none match but the hinted mode exists,
        return (hinted mode, its first principle). Only fall back to defaults
        if the mode itself doesn't exist.
        """
        # First try hinted principles
        for hint in principle_hints:
            m, p = self._pick_from_matrix(mode_hint, hint)
            if hint and p and hint.lower() in p.lower():
                return m, p

        # If we got here, hints didn't match. Prefer the hinted mode anyway.
        matrix = self._matrix()
        valid_modes = self._valid_modes(matrix)
        if mode_hint:
            for m in valid_modes:
                try:
                    if mode_hint.lower() in m.lower():
                        ps = matrix.get(m, {})
                        if isinstance(ps, dict) and ps:
                            return m, next(iter(ps.keys()))
                        else:
                            return m, self._default_principle
                except Exception:
                    continue

        # Final fallback
        return self._default_mode, self._default_principle

    def _default_mode_principle_from_matrix(self) -> Tuple[str, str]:
        return self._default_mode, self._default_principle

    def _prefer_principle_within_mode(self, mode: str, hints: List[str]) -> Optional[str]:
        # If the given mode exists, return the first principle under that mode whose
        # name contains any of the hint substrings (case-insensitive). Otherwise None.
        matrix = self._matrix()
        principles = matrix.get(mode, {})
        if not isinstance(principles, dict):
            return None
        for hint in hints:
            h = (hint or "").strip().lower()
            if not h:
                continue
            for pname in principles.keys():
                try:
                    if h in pname.lower():
                        return pname
                except Exception:
                    continue
        return None

    def _detect_mode_principle(self, text: str) -> Tuple[str, str, float, Dict[str, Any]]:
        """
        Step 6 — Full Matrix Coverage & Mode Diversification
        Expands detection to include Creative / Reflective / Growth Modes
        while retaining Analytical + Critical reliability.
        """
        t = (text or "").lower()
        mode, principle = self._default_mode_principle_from_matrix()
        confidence = 0.55
        alt_mode, alt_principle, alt_conf = None, None, None

        # --- 1) Critical — Stakeholder / incentive / relationship pressure ---
        if re.search(r"\b(co[- ]?founder|partner|stakeholder|board|investor|team|incentive|misalign|alignment|tension|conflict|trust|pressure)\b", t):
            mode, principle = self._pick_from_matrix_any(
                "Critical",
                ["Stakeholder", "Stakeholders", "Incentive", "Incentives",
                 "Alignment", "Misalignment", "Trust", "Conflict", "Tension",
                 "Relationship", "Relational", "Dynamics", "Second"]
            )
            preferred = self._prefer_principle_within_mode(mode, [
                "Stakeholder", "Stakeholders", "Incentive", "Incentives",
                "Alignment", "Misalignment", "Trust", "Conflict", "Tension",
                "Relationship", "Relational", "Dynamics"
            ])
            if preferred:
                principle = preferred
            confidence = max(confidence, 0.64)

        # --- 2) Analytical — 'What to do next' / uncertainty ---
        if re.search(r"\b(unsure|uncertain|what\s*to\s*do\s*next|next\s*step|where\s*to\s*start)\b", t):
            m2, p2 = self._pick_from_matrix_any(
                "Analytical",
                ["Test", "Assumption", "Next", "Validation", "Experiment"]
            )
            if confidence < 0.60:
                mode, principle = m2, p2
                confidence = 0.60

        # --- 3) Analytical — Evidence / validation cues ---
        if re.search(r"\b(test|validate|evidence|data|experiment|proof)\b", t):
            m2, p2 = self._pick_from_matrix("Analytical", "Evidence")
            if confidence < 0.62:
                mode, principle = m2, p2
                confidence = 0.62

        # --- 4) Critical ALT — Second-order / unintended consequences ---
        if re.search(r"\b(second[- ]order|unintended|downstream|what if)\b", t):
            alt_mode, alt_principle = self._pick_from_matrix("Critical", "Second")
            alt_conf = 0.48

        # --- 5) Creative — Ideation / imagination / new approaches ---
        if re.search(r"\b(brainstorm|idea|imagin|new approach|possibilit|prototype|blue sky|novel|what if|concept)\b", t):
            mode, principle = self._pick_from_matrix("Creative", "Exploration")
            confidence = max(confidence, 0.60)

        # --- 6) Reflective — Hindsight / lessons / introspection ---
        if re.search(r"\b(regret|hindsight|pattern|lesson|learned|looking back|reflection|introspect|recap)\b", t):
            mode, principle = self._pick_from_matrix("Reflective", "Root Cause")
            confidence = max(confidence, 0.60)

        # --- 7) Growth — Habits / mindset / feedback / evolution ---
        if re.search(r"\b(habit|mindset|develop|feedback|coach|evolv|improv|practice|routine)\b", t):
            mode, principle = self._pick_from_matrix("Growth", "Iteration")
            confidence = max(confidence, 0.60)

        # --- 8) Return result ---
        return mode, principle, confidence, {
            "alt_mode": alt_mode,
            "alt_principle": alt_principle,
            "alt_confidence": alt_conf
        }

    # ---------- Matrix & Voices helpers ----------

    def _norm(self, s: str) -> str:
        return (s or "").strip().lower().replace("&", "and").replace("  ", " ")

    def _get_matrix_question(self, mode: str, principle: str) -> str:
        """Forgiving lookup against coerced + filtered Matrix dict."""
        matrix = self._matrix()
        valid_modes = self._valid_modes(matrix)
        if not valid_modes:
            return ""

        # 1) Exact (only within valid modes)
        try:
            if mode in valid_modes:
                q = (matrix.get(mode, {}) or {}).get(principle)
                if q:
                    return str(q)
        except Exception:
            pass

        # Build normalized index only from valid modes
        target_mode, target_pr = self._norm(mode), self._norm(principle)
        norm_index: Dict[str, Dict[str, Any]] = {}
        for m in valid_modes:
            ps = matrix.get(m, {})
            if not isinstance(ps, dict):
                continue
            nm = self._norm(m)
            bucket = norm_index.setdefault(nm, {})
            for p, qv in ps.items():
                bucket[self._norm(p)] = qv

        # 2) Normalized exact
        if target_mode in norm_index and target_pr in norm_index[target_mode]:
            return str(norm_index[target_mode][target_pr])

        # 3) Partial within chosen mode(s)
        for nm, bucket in norm_index.items():
            if target_mode in nm or nm in target_mode:
                if target_pr in bucket:
                    return str(bucket[target_pr])
                for np, qv in bucket.items():
                    if target_pr in np or np in target_pr:
                        return str(qv)

        # 4) Global partial across all valid modes
        for nm, bucket in norm_index.items():
            for np, qv in bucket.items():
                if target_pr in np or np in target_pr:
                    return str(qv)

        # 5) Stable fallback: first valid mode's first principle
        try:
            fm = self._first_mode_principle(matrix)[0]
            fp = next(iter(matrix[fm].keys()))
            return str(matrix[fm][fp]) or ""
        except Exception:
            return ""

    def _voice_line(self, base_q: str, voice_name: str, empathy_on: bool) -> str:
        """
        Voice overlay with optional templating and sensible default rewrites.
        - If voices.json has a template, use it (supports {q}).
        - Else: apply short, voice-specific paraphrases.
        """
        if not base_q:
            return ""

        voice_prefix, template = "", None
        try:
            voices = (self.voices or {}).get("voices", [])
            v = next(
                (
                    v for v in voices
                    if ((v.get("display_name") or v.get("name") or "").lower()
                        == voice_name.lower())
                ),
                None
            )
            if v:
                voice_prefix = v.get("prefix", "") or ""
                template = v.get("template")
        except Exception:
            pass

        # Minimal defaults for prefixes
        if not voice_prefix:
            default_prefixes = {
                "Thiel": "Thiel →",
                "Peterson": "Peterson →",
                "Feynman": "Feynman →",
                # keep legacy labels working too:
                "Socratic": "Socratic →",
                "Challenger": "Challenge →",
                "Empathic": "Gently →" if empathy_on else "Consider →",
                "Neutral": ""
            }
            voice_prefix = default_prefixes.get(voice_name, "")

        # If a template exists, use it (insert the base question)
        if isinstance(template, str) and template.strip():
            phrased = template.replace("{q}", base_q)
            return f"{voice_prefix} {phrased}".strip()

        # Otherwise defaults per voice (concise paraphrases)
        rewrites = {
            "Thiel":    f"What is the non-obvious assumption? {base_q}",
            "Peterson": f"Start with the smallest actionable order: {base_q}",
            "Feynman":  f"Explain it so a smart 12-year-old gets it: {base_q}",
            # legacy fallbacks:
            "Socratic": f"Let’s reason it out: {base_q}",
            "Challenger": f"Pressure-test this: {base_q}",
            "Empathic": f"If it helps, {base_q}",
            "Neutral":  base_q
        }
        phrased = rewrites.get(voice_name, base_q)
        return f"{voice_prefix} {phrased}".strip()

    # ---------- Render ----------

    def _render_questions(self, det: DetectionResult) -> List[str]:
        out: List[str] = []

        # 1) Primary from Matrix (best effort)
        base_q = (self._get_matrix_question(det.mode, det.principle) or "").strip()
        if not base_q:
            base_q = "What evidence would most directly challenge your current conclusion?"

        # 2) Voices to apply (Thiel, Peterson, Feynman)
        voices_to_use: List[str] = ["Thiel", "Peterson", "Feynman"]

        # 3) Overlays (dedup)
        seen = set()
        for v in voices_to_use:
            q = self._voice_line(base_q, v, det.empathy_on)
            if q and q not in seen:
                out.append(q)
                seen.add(q)

        # 4) Contextual follow-up (incentives/stakeholders/risk)
        ctx_tags = (det.tags or {}).get("contexts", [])
        if any(("Incentive" in t) or ("Stakeholder" in t) or ("Risk" in t) for t in ctx_tags):
            follow = "Where could incentives or stakeholder pressures distort what looks like evidence?"
            if follow not in seen:
                out.append(follow)
                seen.add(follow)

        # 5) Ensure at least 3
        if len(out) < 3:
            probe = "What would you test next to learn the most with the least risk?"
            if probe not in seen:
                out.append(probe)

        return out[:5]

