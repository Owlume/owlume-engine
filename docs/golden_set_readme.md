# 🦉 Owlume — Golden Set Challenge (Final Version)

## Purpose  
The Golden Set Challenge proves that Owlume is **not just another AI wrapper**.  
It validates that the MVP consistently produces **provocative, precise, and human** blind-spot questions — not generic lists or summaries.  

This QA flow enforces Owlume’s brand promise:

> *Illuminate your blind spots before they cost you.*

---

## Structure  
Each run uses **20 short dilemmas** (2–4 sentences).  
Every dilemma is tagged with its expected **Mode × Principle** from the Questioncraft Matrix.  
Evaluators run each dilemma through Owlume GPT and record outcomes.

---

## Evaluation Flow  

| Step | Action | Pass Criteria |
|------|---------|---------------|
| **D1 — Setup** | Load the `golden_set_dilemmas.csv` file. | File opens cleanly; each entry includes Mode × Principle tags. |
| **D2 — Run Test** | Paste each dilemma into Owlume GPT. | Response returns **3–7 sharp questions**, with **no advice or explanation.** |
| **D3 — Empathy Toggle** | Re-run with “Empathy ON.” | Language softens; structure and sharpness remain intact. |
| **D4 — Brand Check** | Verify tone aligns with *Front Page Flow* (human, reflective, confident). | Pass if it feels unmistakably like Owlume’s voice. |
| **D5 — Provocative Precision Rule** | Apply **Reject Generic Breadth / Accept Provocative Precision.** | **Fail if:** output reads like a consultant’s list of categories or “areas to consider.”<br>**Pass if:** it delivers 2–5 sharp, uncomfortable questions exposing assumptions, evidence gaps, hidden drivers, or consequences.<br>**CEO-Level Litmus Test:** Would a world-class decision-maker pause to debate this question or dismiss it as generic?<br>→ If **pause → Pass.**  If **dismiss → Fail.** |
| **D6 — Mode Accuracy** | Compare detected Mode to expected tag. | ≥ 80 % match = Pass. |
| **D7 — Principle Accuracy** | Compare detected Principle to expected tag. | ≥ 70 % match = Pass. |
| **D8 — Empathy Integrity** | Ensure empathy overlay didn’t distort logic. | Questions remain logically sound and relevant. |
| **D9 — Differentiation Check** | Run same dilemma in generic AI prompt “What blind spots?” | Owlume output must be **sharper, more structured, more human-framed.** |
| **D10 — Summary Report** | Record Pass/Fail per step. | ≥ 85 % overall pass rate = Golden Set MVP Ready. |

---

### 🔗 Related Reference — Golden Rules Appendix  

For detailed guidance on how to evaluate Step **D5 (Provocative Precision)** — including rationale, real examples of *Fail vs Pass*, and dataset curation tips — see:

➡️ **[Golden Rules → Appendix: Applying the D5 Rule in Practice](/docs/golden_rules.md)**  

This appendix expands on the philosophy behind Owlume’s sharpness standard and helps QA evaluators maintain consistent interpretation across tests.

---

## Files and Locations  

| File | Folder | Description |
|------|---------|-------------|
| `golden_set_dilemmas.csv` | `/qa/` | 20 dilemmas + expected Mode × Principle. |
| `golden_set_readme.md` | `/docs/` | This protocol. |
| `golden_set_results.md` | `/qa/results/` | Log of all test outcomes with timestamps. |
| `golden_rules.md` | `/docs/` | Contains **Provocative Precision** rule + **CEO Litmus Test.** |

---

## CEO-Level Litmus Test (Embedded in Track D2)  

> **Ask:**  
> “Would a world-class decision-maker pause the meeting to debate this question — or dismiss it as generic?”  
>  
> **If pause → Pass.**  
> **If dismiss → Fail.**

---

## Completion Criteria  

✅ Golden Set Challenge = **Complete** when:  
- 20 dilemmas validated through all 10 steps.  
- ≥ 85 % overall Pass rate.  
- No failures in Step D5 (Provocative Precision).  
- QA log stored in `/qa/results/`.

---

## Brand Tie-In  

> **Front Page Flow ↔ Golden Set**  
> Every accepted output must *sound* and *feel* like:  
> “Owlume reveals what you’re missing — because what you miss costs you.”

---

*Last updated:* **2025-10-11**  
*Status:* ✅ **Final, Locked**
