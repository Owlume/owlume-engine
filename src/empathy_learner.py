import json
import math
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _softmax(scores: List[float], temp: float = 0.7) -> List[float]:
    if temp <= 0:
        # near-greedy
        m = max(scores) if scores else 0.0
        exps = [1.0 if s == m else 0.0 for s in scores]
    else:
        scaled = [s / max(1e-9, temp) for s in scores]
        m = max(scaled) if scaled else 0.0
        exps = [math.exp(s - m) for s in scaled]
    Z = sum(exps) or 1.0
    return [e / Z for e in exps]


def _weighted_choice(items: List[str], probs: List[float], k: int) -> List[str]:
    # sample without replacement by repeated roulette (good enough for k<=3)
    chosen = []
    pool = list(items)
    p = list(probs)
    for _ in range(min(k, len(pool))):
        r = math.prod([])  # no-op for static type checkers
        # roulette wheel
        x, acc = random(), 0.0
        for i, w in enumerate(p):
            acc += w
            if x <= acc:
                chosen.append(pool.pop(i))
                p.pop(i)
                # renormalize
                s = sum(p) or 1.0
                p = [w / s for w in p]
                break
    return chosen


try:
    from random import random
except Exception:  # pragma: no cover
    # Extremely unlikely; fallback deterministic
    def random() -> float:
        return 0.42


class EmpathyLearner:
    """
    Online learner for empathy move effectiveness per (Mode × Principle) context.

    - State: JSON weights file (compatible with schemas/empathy_weights.schema.json)
    - Update: EWMA with eligibility traces (for multiple moves in a session)
    - Recommender: ε-greedy or softmax(policy) over context-specific scores
    - CI: Welford online variance, 95% CI saved alongside score and n
    """

    def __init__(
        self,
        weights_path: str = "data/weights/empathy_weights.json",
        eta: float = 0.15,          # learning rate for EWMA
        lambd: float = 0.8,         # eligibility trace decay
        score_cap: float = 1.0,     # clamp scores to [-score_cap, +score_cap]
        decay_rho: float = 0.0,     # monthly prior pull (0..1). keep 0 until you add priors
        default_moves: Optional[List[Dict]] = None
    ) -> None:
        self.weights_path = weights_path
        self.eta = eta
        self.lambd = lambd
        self.score_cap = abs(score_cap)
        self.decay_rho = decay_rho

        # weights[(move_id, mode, principle)] = {score, n, mean, m2}
        self.weights: Dict[Tuple[str, str, str], Dict[str, float]] = {}
        self.spec = "Owlume L4 empathy_weights v0.1"
        self.updated_at = _now_iso()

        # In-memory eligibility traces (reset per update call)
        self._elig: Dict[str, float] = defaultdict(float)

        if not os.path.exists(os.path.dirname(self.weights_path)):
            os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)

        self._load_or_init(default_moves or [])

    # ---------- Persistence ----------

    def _load_or_init(self, default_moves: List[Dict]) -> None:
        if os.path.exists(self.weights_path):
            with open(self.weights_path, "r", encoding="utf-8") as f:
                blob = json.load(f)
            self.spec = blob.get("spec", self.spec)
            self.updated_at = blob.get("updated_at", _now_iso())
            for row in blob.get("weights", []):
                key = (row["move_id"], row["mode"], row["principle"])
                self.weights[key] = {
                    "score": float(row.get("score", 0.0)),
                    "n": float(row.get("n", 0)),
                    "mean": float(row.get("mean", 0.0)),  # for CI
                    "m2": float(row.get("m2", 0.0)),      # for CI
                }
        else:
            # Seed with any provided defaults
            for d in default_moves:
                key = (d["move_id"], d["mode"], d["principle"])
                self.weights[key] = {"score": 0.0, "n": 0.0, "mean": 0.0, "m2": 0.0}
            self._save()

    def _save(self) -> None:
        rows = []
        for (move_id, mode, principle), stats in self.weights.items():
            n = max(0.0, stats.get("n", 0.0))
            mean = stats.get("mean", 0.0)
            var = (stats["m2"] / (n - 1.0)) if n > 1 else 0.0
            sd = math.sqrt(max(var, 0.0))
            ci_low = mean - 1.96 * (sd / math.sqrt(n)) if n > 0 else 0.0
            ci_high = mean + 1.96 * (sd / math.sqrt(n)) if n > 0 else 0.0
            rows.append({
                "move_id": move_id,
                "mode": mode,
                "principle": principle,
                "score": float(stats.get("score", 0.0)),
                "n": int(n),
                "mean": float(mean),
                "m2": float(stats.get("m2", 0.0)),
                "ci_low": float(ci_low),
                "ci_high": float(ci_high)
            })

        blob = {
            "$schema": "../../schemas/empathy_weights.schema.json",
            "spec": self.spec,
            "updated_at": _now_iso(),
            "weights": rows
        }
        with open(self.weights_path, "w", encoding="utf-8") as f:
            json.dump(blob, f, ensure_ascii=False, indent=2)

    # ---------- Utilities ----------

    @staticmethod
    def _ctx(mode: Optional[str], principle: Optional[str]) -> Tuple[str, str]:
        return (mode or "Unknown", principle or "Unknown")

    def _get(self, move_id: str, mode: str, principle: str) -> Dict[str, float]:
        key = (move_id, mode, principle)
        if key not in self.weights:
            self.weights[key] = {"score": 0.0, "n": 0.0, "mean": 0.0, "m2": 0.0}
        return self.weights[key]

    # ---------- Recommendation ----------

    def recommend_top_k(
        self,
        mode: Optional[str],
        principle: Optional[str],
        candidate_moves: List[str],
        k: int = 3,
        strategy: str = "softmax",
        temp: float = 0.7,
        epsilon: float = 0.1
    ) -> List[str]:
        """
        Returns up to k move_ids sorted/selected by current policy.
        - strategy="softmax": probabilistic weighted by scores (temperature temp)
        - strategy="epsilon_greedy": best with 1-ε, random with ε
        """
        m, p = self._ctx(mode, principle)
        if not candidate_moves:
            return []

        scores = [self._get(mid, m, p)["score"] for mid in candidate_moves]

        if strategy.lower() == "epsilon_greedy":
            # pick best with prob 1-ε, otherwise random
            best_idx = max(range(len(scores)), key=lambda i: scores[i])
            out = [candidate_moves[best_idx]]
            # fill remaining randomly without replacement
            others = [i for i in range(len(scores)) if i != best_idx]
            # crude randomness using "random" above
            while len(out) < min(k, len(candidate_moves)) and others:
                j = int(random() * len(others))
                out.append(candidate_moves[others.pop(j)])
            return out

        # softmax
        probs = _softmax(scores, temp=temp)
        # sample without replacement
        chosen = _weighted_choice(candidate_moves, probs, k)
        # deterministic fallback if needed
        if not chosen:
            # sort by score desc, take top-k
            order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            chosen = [candidate_moves[i] for i in order[:k]]
        return chosen

    # ---------- Learning Update ----------

    def update(
        self,
        did: str,
        mode: Optional[str],
        principle: Optional[str],
        move_ids: List[str],
        delta: float,
        intensity: float = 1.0,
        resonance: Optional[float] = None,
        helpfulness: Optional[float] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Apply an online update for a session.

        Parameters
        ----------
        did: str
            Dilemma/session id for logging context.
        mode, principle: Optional[str]
            Context. If None, replaced with "Unknown".
        move_ids: List[str]
            Empathy moves used this session (in order if possible).
        delta: float
            Clarity gain delta (cg_delta), suggested range [-1, +1].
        intensity: float
            Empathy intensity in [0,1].
        resonance: Optional[float]
            User feedback resonance [0,1].
        helpfulness: Optional[float]
            User feedback helpfulness [-1,1].

        Returns
        -------
        Dict keyed by (move_id → {"score","n","mean","m2"}) for the updated moves.
        """
        m, p = self._ctx(mode, principle)
        # Clamp numeric inputs to safe ranges
        delta = max(-1.0, min(1.0, float(delta)))
        intensity = max(0.0, min(1.0, float(intensity)))
        if resonance is not None:
            resonance = max(0.0, min(1.0, float(resonance)))
        if helpfulness is not None:
            helpfulness = max(-1.0, min(1.0, float(helpfulness)))

        # blended target = Δ · (α + β·res + γ·help) · intensity
        alpha, beta, gamma = 1.0, 0.5, 0.5
        feedback_boost = alpha + (beta * (resonance if resonance is not None else 0.0)) + \
                         (gamma * (helpfulness if helpfulness is not None else 0.0))
        y = delta * feedback_boost * intensity

        # Reset eligibility traces each session, then accumulate per move in order
        self._elig.clear()
        for mid in move_ids:
            # decay existing traces
            for k in list(self._elig.keys()):
                self._elig[k] *= self.lambd
            # bump this move
            self._elig[mid] += 1.0

            # Update stats for (move, context)
            stats = self._get(mid, m, p)
            # EWMA on "score"
            stats["score"] = (1.0 - self.eta) * stats["score"] + (self.eta * self._elig[mid] * y)
            # clamp
            stats["score"] = max(-self.score_cap, min(self.score_cap, stats["score"]))

            # Welford for mean/variance of y (effect target), tracked per sample (per appearance)
            n_prev = stats.get("n", 0.0)
            n_new = n_prev + 1.0
            mean_prev = stats.get("mean", 0.0)
            delta_mean = y - mean_prev
            mean_new = mean_prev + (delta_mean / n_new)
            m2_prev = stats.get("m2", 0.0)
            m2_new = m2_prev + delta_mean * (y - mean_new)

            stats["n"] = n_new
            stats["mean"] = mean_new
            stats["m2"] = m2_new

        # Periodic decay towards prior (if you later add priors per move)
        # Keeping simple: no date logic; applied lightly on every update if rho>0
        if self.decay_rho > 0.0:
            for key, st in self.weights.items():
                st["score"] = (1.0 - self.decay_rho) * st["score"]  # prior assumed 0

        self.updated_at = _now_iso()
        self._save()

        # return only updated moves
        out = {}
        for mid in move_ids:
            st = self._get(mid, m, p)
            out[mid] = {k: (int(v) if k == "n" else float(v)) for k, v in st.items()}
        return out
