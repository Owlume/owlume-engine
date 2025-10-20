# 🦉 Owlume — Golden Rules

## Purpose  
This file defines the **core QA and philosophical rules** that govern Owlume’s Golden Set Challenge.  
These rules ensure every output remains true to the brand promise — **“Illuminate your blind spots before they cost you.”**

They are applied during **Track D2** of the Golden Set QA process and during **dataset curation** to maintain consistent voice and cognitive sharpness.

---

## Rule 1 — 🧭 Provocative Precision  
**Name:** Reject Generic Breadth, Accept Provocative Precision  

### Why It Exists  
Generic AI and consultants produce broad categories of considerations.  
Owlume must differentiate by generating *sharp, human questions* that expose blind spots with precision and provocation.  
This rule keeps Owlume out of “safe” territory.

### Definition  
| Reject | Accept |
|--------|---------|
| Lists, inventories, or summaries (e.g., “Customer, Market, Financial Impacts”). | 2–5 sharp, uncomfortable questions that reveal assumptions, evidence gaps, hidden drivers, or downstream consequences. |

### Pass/Fail Criteria  
| Condition | Outcome |
|------------|----------|
| Output could appear in a management consultant’s slide deck. | ❌ Fail — Generic Breadth |
| Output provokes reflection, tension, or debate. | ✅ Pass — Provocative Precision |

---

## Rule 2 — 🧠 CEO-Level Litmus Test  
**Question:**  
> “Would a world-class decision-maker pause the meeting to debate this question — or dismiss it as generic?”  

- If **pause → Pass.**  
- If **dismiss → Fail.**

### Purpose  
This is Owlume’s **ultimate quality gate** — a human calibration rule that ensures each blind-spot question has intellectual and emotional weight.  
It prevents technically correct but *soulless* outputs.

---

## Rule 3 — 💬 Empathy Integrity  
When Empathy Mode is ON, the tone may soften, but the logic must remain uncompromised.  
If empathy dilutes precision or shifts focus away from the dilemma’s truth, mark as **Fail** under Step D8 (Empathy Integrity).  

---

## Rule 4 — 🔁 Clarity Gain Alignment *(Future integration)*  
Each interaction should measurably increase user clarity (tracked later in DilemmaNet as `CG_pre`, `CG_post`, and `CG_delta`).  
The Golden Set will eventually log this to ensure that every question contributes to **Clarity Gain**, not noise.

---

## Rule Usage Summary  

| Rule | Where Applied | Outcome |
|------|----------------|----------|
| Provocative Precision | Step D5 of Golden Set QA | Ensures intellectual sharpness |
| CEO-Level Litmus | Step D5 (sub-check) | Confirms human impact |
| Empathy Integrity | Step D8 of QA | Confirms logical fidelity under empathy |
| Clarity Gain Alignment | Future (CDE integration) | Quantifies clarity produced |

---

## 🔍 Appendix — Applying the D5 Rule (“Provocative Precision”) in Practice  

### 1. Rationale  
The D5 rule exists because **most AI outputs default to breadth** — enumerating safe, predictable dimensions.  
Owlume’s strength is *depth*: it forces focused reflection where stakes are hidden or uncomfortable.  
Every dataset curator or QA evaluator must ask:  
> “Does this question change how the person sees their dilemma — or just restate what they already know?”

---

### 2. Fail vs. Pass Examples  

| Type | Example Output | Reason |
|------|----------------|--------|
| ❌ **Fail — Generic Breadth** | “Consider customer reactions, competitor moves, and timing implications before raising prices.” | Feels like a business-school checklist. No tension or revelation. |
| ✅ **Pass — Provocative Precision** | “What evidence do we have that customers see 20% more value than last quarter — or are we assuming loyalty will carry the difference?” | Exposes a hidden assumption; invites uncomfortable, clarifying debate. |
| ❌ **Fail — Informative but Safe** | “Team morale could be affected by this change.” | Obvious observation, not a discovery. |
| ✅ **Pass — Human and Sharp** | “If morale drops after this change, what story will our people tell themselves — and are we ready to own that story?” | Turns a generic risk into a human blind spot. |

---

### 3. Dataset Curation Guidance  

When building or expanding the Golden Set or DilemmaNet samples:  

- **Tag all Fail-type outputs** with `reason = "Generic breadth"` so they can be excluded from model learning.  
- **Prioritize Pass-type outputs** that display one or more of these traits:  
  - Reveal hidden assumptions or timing flaws.  
  - Create cognitive tension (“Wait — we never thought of that”).  
  - Shift focus from surface data to reasoning drivers.  
  - Trigger a pause, silence, or reflection moment in testing.  
- **Cross-check empathy versions** — ensure that turning Empathy ON softens tone but does *not* dilute precision.  

---

### 4. How to Apply During QA (Track D2 Step D5)  

| Step | Action | What to Look For |
|------|---------|------------------|
| **1. Read Output** | Skim the 3–7 generated questions. | Do they provoke thought or list safe areas? |
| **2. Identify Core Tension** | Ask yourself: “Where is the discomfort or insight?” | If none → likely fail. |
| **3. Apply CEO Litmus** | “Would a world-class decision-maker pause or dismiss this?” | Pause → Pass. Dismiss → Fail. |
| **4. Document Decision** | Log `pass/fail` and reasoning in `/qa/results/golden_set_results.md`. | Consistent QA traceability. |

---

### 5. Visual Heuristic — “Owlume Precision Curve”

Imagine a horizontal line from **Breadth → Depth**.  
Owlume aims for the right side of that curve:

[ Generic Breadth ]———[ Analytical Clarity ]———🦉[ Provocative Precision ]
0% 50% 100%


> The sweet spot is where the question feels *slightly uncomfortable but deeply clarifying.*

---

*Integration Note:*  
This D5 expansion complements the main rule definitions above.  
Keep it appended at the end of `/docs/golden_rules.md` as a **QA and dataset curation reference.**

*Last updated:* **2025-10-11**  
*Status:* ✅ Rule Expansion Integrated




