# Architecture Decision Record (ADR) — Template

> **Purpose:** Capture the reasoning behind any non-trivial technical or design decision in Owlume.  
> Each ADR turns an implicit “vibe” into explicit, recoverable knowledge.

---

## 1. ADR ID and Title
**ADR-XXXX:** _Short title (e.g., “Confidence-gated priors in detectMode fusion”)_

---

## 2. Date
YYYY-MM-DD

---

## 3. Context
_Describe the problem or uncertainty that led to this decision._  
- What was unclear, conflicting, or risky?  
- What other options existed?  
- What stage or track does this relate to (e.g., T1-S3 Hybrid Fusion, T4-S2 Aggregator)?  

Example:  
> During fusion development, we needed to combine semantic confidence with fallacy/context priors without losing interpretability.

---

## 4. Decision
_Summarize what was decided and why._  
Include thresholds, parameters, and rationale.

Example:  
> We introduced a **confidence-gated fusion rule** where priors influence mode detection only if semantic confidence ∈ [0.35, 0.75] and are capped at ≤25% total influence.

---

## 5. Consequences
_List expected outcomes, trade-offs, or risks._  
- What improves because of this decision?  
- What new constraints appear?  

Example:  
> ✅ Improves predictive sharpness on mid-confidence cases.  
> ⚠️ Slightly higher latency due to dual scoring pass.

---

## 6. Evidence / Validation
_Reference experiments, smoke tests, or discussion threads that support the choice._

Example:  
> Verified by `scripts/smoke_test_engine_fusion.py` (2025-10-15).  
> Confidence stability tested on 10 dilemmas (avg Δ = +0.105).

---

## 7. Alternatives Considered
_Optional — list options rejected and why._

Example:  
> - Run priors before semantic scan (too unstable).  
> - Ignore priors entirely (missed early cues).

---

## 8. Related Files / Commits
_Link to affected scripts, schemas, or commits._  

src/elenx_engine.py
scripts/smoke_test_engine_fusion.py
commit: T1-S3-hybrid-fusion


---

## 9. Status
Choose one:  
- **Proposed**  
- **Accepted**  
- **Superseded** (by ADR-####)  
- **Deprecated**

---

### Summary Line (for dashboards)
> **Decision:** [Short phrase] • **Date:** [YYYY-MM-DD] • **Status:** [Accepted]

---

### Notes
Keep each ADR self-contained and ≤1 page.  
Commit it as a standalone file:  
`docs/adr/adr-####_<short_title>.md`

---

**Tagline:**  
> *“If it’s not written, it didn’t clarify.”*
