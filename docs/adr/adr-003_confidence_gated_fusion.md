# ADR-0003: Confidence-Gated Fusion for Mode Detection

---

## 1. Date
2025-10-15

---

## 2. Context
During T1-S3 (Hybrid Fusion), we needed to merge two information streams inside the Elenx engine:

1. **Semantic detector output** — the LLM-derived Mode and Principle confidence scores.  
2. **Prior cues** — early fallacy and context-driver signals surfaced by a light pre-scan.

Early tests showed that applying priors indiscriminately caused instability and false positives.  
However, ignoring them lost valuable anticipatory cues.  
We needed a rule that preserved interpretability while adding sharpness.

---

## 3. Decision
Implement a **confidence-gated fusion rule** inside `src/elenx_engine.py`:

- Semantic detector runs first.  
- If its confidence ∈ **[0.35 – 0.75]**, the prior layer is activated.  
- Prior influence weight capped at **≤ 25 %** of total mode score.  
- If semantic confidence ≥ 0.85, skip priors entirely (assume semantic dominance).  
- If semantic confidence ≤ 0.35, still log priors but do not override result.  
- When semantic and priors disagree, carry **top-2 Modes** forward to preserve context.

Empathy overlay triggers automatically when fusion relies primarily on priors.

---

## 4. Consequences
✅ Improves predictive sharpness on ambiguous dilemmas.  
✅ Maintains interpretability and stability under high confidence.  
⚠️ Slight latency increase (~5–10 %) due to dual scoring pass.  
⚠️ Adds complexity to tuning thresholds; values may need adaptive weighting in Stage 4 L1.

---

## 5. Evidence / Validation
- Verified by `scripts/smoke_test_engine_fusion.py` on 2025-10-15.  
- Output confirmed semantic-prior balance with empathy auto-toggle.  
- Aggregator metrics (T4-S2) later showed no regressions; avg Δ = +0.105 Clarity Gain.

---

## 6. Alternatives Considered
- **Run priors before semantic scan** — produced false positives and confusion loops.  
- **Ignore priors entirely** — lost early detection of incentive/stakeholder distortions.  

---

## 7. Related Files / Commits

src/elenx_engine.py
scripts/smoke_test_engine_fusion.py
data/context_drivers.json
commit: T1-S3-hybrid-fusion


---

## 8. Status
**Accepted**

---

### Summary Line
> **Decision:** Confidence-gated fusion (priors ≤ 25 %) • **Date:** 2025-10-15 • **Status:** Accepted

---

**Tagline:**  
> *Balance speed with sanity — trust semantics, consult priors.*
