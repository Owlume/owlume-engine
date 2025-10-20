───────────────────────────────────────────────
   🦉  OWLUME — CLARITY GAIN METRIC
   Measure of Insight • Proof of Clarity • Adaptive Learning
───────────────────────────────────────────────

| 🧾 **Metric Design Status** | **Details** |
|------------------------------|-------------|
| **Version** | v1.0 — Pre-Integration |
| **Stage** | Stage 3 — Execution Phase |
| **Purpose** | Define and measure cognitive clarity improvement (ΔCG) |
| **Status** | ✅ Defined • 🧩 Pending DilemmaNet Implementation |
| **Next Milestone** | Integrate CG logging into DilemmaNet schema (T2) |
| **Maintainers** | Brian (Founder) • Ted (AI Partner) |
| **Last Updated** | October 2025 |


🧭 Owlume — Clarity Gain Metric
Purpose

Clarity Gain (CG) quantifies how much clearer a user becomes between entering and leaving a reflection.
It turns Owlume’s core promise — “Illuminate your blind spots before they cost you.” — into a measurable signal of cognitive value.

1️⃣ Conceptual Definition
Variable	Description	Type	Range
CG_pre	Self-reported clarity level before reflection	Float	0.0–1.0
CG_post	Clarity after reflection (weighted by self-rating + linguistic improvement)	Float	0.0–1.0
CG_delta	Difference between CG_post and CG_pre, adjusted for signal confidence	Float	–1.0 → +1.0

CG_delta = (CG_post – CG_pre) × Weight_confidence

Typical thresholds:

+0.20 → modest clarity improvement

+0.40 → strong clarity gain

+0.60 + → breakthrough moment

2️⃣ Data Flow Inside DilemmaNet

Every reflection generates a Clarity Gain record:

{
  "did": "DID-2025-0012",
  "uid": "U-134A",
  "cg_pre": 0.42,
  "cg_post": 0.78,
  "cg_delta": 0.36,
  "empathy_state": "ON",
  "mode_detected": "Assumption",
  "principle_detected": "Evidence",
  "timestamp": "2025-10-11T12:44:00Z"
}


These values are logged, versioned, and aggregated for:

User-level insights (personal clarity trends)

System-level tuning (Elenx learning curves)

Dataset-level research (blind-spot typologies)

3️⃣ Measurement Inputs
Input Type	Source	Weight in CG calculation
Self-Rating Delta	“How clear do you feel?” before/after	40 %
Linguistic Delta	Semantic clarity gain from text analysis (less vagueness, stronger structure)	35 %
Behavioral Depth	Number and quality of follow-up questions explored	15 %
Proof-of-Clarity Feedback	User confirmation (“Yes, that made it clearer”)	10 %

Weights are adjustable per experiment; all contribute to the composite CG_post value.

4️⃣ Connection to Proof-of-Clarity Layer

Clarity Gain is the quantitative backbone that drives the qualitative feedback system.
The Proof-of-Clarity (PoC) layer translates raw CG data into human-readable reinforcement.

Proof-of-Clarity Signal	Driven by CG + Other Metrics	User-Facing Feedback Example
Depth of Reflection	CG_delta + Mode transitions	“You went one layer deeper than most users.”
Rarity of Insight	CG_delta + category rarity	“You caught what 82 % of users overlook.”
Empathy Ratio	CG_delta + empathy balance	“You balanced logic and empathy better today.”
Consistency Score	Rolling avg CG_delta × 7 days	“Clarity compounds — 5 days illuminated this week.”
Visual Summary
User Reflection
     ↓
Elenx Analysis → detectMode() → detectPrinciple()
     ↓
Compute Clarity Gain (CG_pre → CG_post → CG_delta)
     ↓
Feed to Proof-of-Clarity (signal selector)
     ↓
Feedback surfaced to user (“Depth of Reflection +0.4”)
     ↓
Log to DilemmaNet → update adaptive weights


In short:
Clarity Gain measures the change; Proof of Clarity makes the change felt.

5️⃣ Role in Clarity-Driven Engineering (CDE)
CDE Principle	How Clarity Gain Fulfills It
Instrument Everything	Every reflection logs CG metrics automatically.
Short Feedback Half-Life	Recent CG deltas weighted higher for adaptive learning.
Builder Visibility	DilemmaNet dashboards visualize CG trends per Mode × Principle.
Adaptive Release	Engine updates weekly based on CG performance, not raw usage.

Thus, Clarity Gain closes the loop between human perception of insight and systemic improvement of questioning quality.

6️⃣ Schema Reference

File → /schemas/clarity_gain_record.schema.json
(structure excerpt)

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "schemas/clarity_gain_record.schema.json",
  "title": "Clarity Gain Record",
  "type": "object",
  "properties": {
    "did": { "type": "string" },
    "uid": { "type": "string" },
    "cg_pre": { "type": "number", "minimum": 0, "maximum": 1 },
    "cg_post": { "type": "number", "minimum": 0, "maximum": 1 },
    "cg_delta": { "type": "number", "minimum": -1, "maximum": 1 },
    "empathy_state": { "type": "string" },
    "mode_detected": { "type": "string" },
    "principle_detected": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" }
  },
  "required": ["did", "cg_pre", "cg_post", "cg_delta", "timestamp"]
}

7️⃣ Future Extension

Integrate Voice reflections → infer clarity gain from speech pacing + tone confidence.

Add Confidence weighting → adjust CG_delta when user admits uncertainty.

Correlate Empathy and Clarity Gain → quantify the trust multiplier (expected +20–30 %).

🪶 Summary
Essence	Role
Clarity Gain	Quantitative measure of progress (the metric)
Proof of Clarity	Emotional reinforcement layer (the mirror)
Together	They make reflection measurable, meaningful, and addictive in the right way.
|
───────────────────────────────────────────────
🦉  END OF DOCUMENT — ILLUMINATE, DON’T ASSUME
───────────────────────────────────────────────
