<<<<<<< HEAD
# owlume-engine
=======
───────────────────────────────────────────────
   🦉  OWLUME — ILLUMINATE BLIND SPOTS
   Questioncraft • Elenx • DilemmaNet • Empathy
───────────────────────────────────────────────
📦  Stage 3 — Execution Phase (v1.0 • Pre-Integration)
💡  Focus: Build Elenx Engine + DilemmaNet Logging (T1–T2)
───────────────────────────────────────────────



# 🦉 Owlume — Illuminate Blind Spots

**Brand promise:** Illuminate your blind spots before they cost you.  
**Contrast line:** Most AI gives answers. Owlume reveals what you’re missing — because what you miss costs you.  
**Challenge:** Now, let Owlume show you the blind spots behind your choices in seconds — before they cost you.

---

| 🧾 **Project Status** | **Details** |
|------------------------|-------------|
| **Version** | v1.0 — Pre-Integration |
| **Stage** | Stage 3 — Execution Phase |
| **Focus Tracks** | T1 (Elenx Engine Integration) • T2 (DilemmaNet Logging) |
| **Status** | ✅ Design Complete • 🧩 Build Beginning |
| **Next Milestone** | T3 — GPT App & User Experience Integration |
| **Maintainers** | Brian (Founder) • Ted (AI Partner) |
| **Last Updated** | October 2025 |


## Overview

Owlume is a clarity system built to detect cognitive and contextual blind spots in decisions. It fuses the **Questioncraft Matrix**, **Elenx Engine**, **Empathy Lens**, and **DilemmaNet** dataset into one adaptive architecture.

---

## Core Components

### 1. Questioncraft Matrix
A 5-Mode × 6-Principle structure guiding how Owlume asks questions that reveal assumptions, evidence gaps, and distortions.  
→ `/data/matrix.json` and `/schemas/matrix.schema.json`

### 2. Elenx Engine
Routes user text through the Matrix, detects Mode × Principle, overlays voices (e.g., Thiel, Feynman, Peterson), and applies empathy modulation.  
→ `/docs/elenx_architecture.md`

### 3. DilemmaNet Dataset
The structured data spine logging dilemmas, blind-spot tags, clarity metrics, and feedback.  
→ `/docs/dilemmanet_overview.md`

### 4. Empathy Lens
Cross-cutting overlay that expands blind-spot coverage into relational and moral domains, improving adoption and trust.  
→ `/docs/empathy_lens.md`

---

## Development Philosophy

**Clarity-Driven Engineering (CDE)** — Owlume’s variant of Feedback-Driven Engineering (FDE).  
Instead of measuring clicks or time, Owlume measures **clarity gained per reflection**. Every interaction becomes a feedback event that improves both the engine and the dataset.

**North Star Metric:** Clarity Gain (CGΔ) — the measurable increase in user understanding between entering and leaving a reflection.

---

## Repository Structure


* **/docs/** → explanatory and design documents.  
* **/data/** → validated JSON knowledge packs (Matrix, Voices, Fallacies, Context Drivers).  
* **/schemas/** → JSON Schema definitions (draft-07) for VS Code validation.

---

## DilemmaNet & Clarity Gain Logging

Owlume measures clarity before and after each reflection and logs a structured record into DilemmaNet. This turns every session into learning that sharpens Elenx.

**What we log (per reflection):**
- DID (Dilemma ID), CID (Conversation ID), optional QIDs (Mode × Principle tags)
- Clarity scores: `CG_pre`, `CG_post`, and `CG_delta = CG_post − CG_pre`
- Timestamp, app version, empathy overlay flag, and anonymous runtime signals

**Clarity thresholds:**
- Micro: Δ 1–2 — minor shift  
- **Meaningful:** Δ ≥ 3 — noticeable change (MVP success minimum)  
- Major: Δ ≥ 6 — transformative insight

**Files:**
- `/data/clarity_gain_thresholds.json` — reference thresholds & labels
- `/data/proof_of_clarity_signals.json` — user-facing feedback texts by delta range
- `/data/proof_of_clarity_insight_signals.json` — optional badges (rarity, depth, empathy, consistency)
- `/schemas/clarity_gain_record.schema.json` — validation for per-session records

**Privacy by default:**
- No raw text stored by default; records use hashed IDs
- Shareable summaries are opt-in and follow redaction rules (`share` object in schema)
- Users can view or delete their data summary on request

**Why it matters:**  
Clarity Gain is Owlume’s quality signal. Higher Δ correlates with sharper questions, better decisions, and a smarter engine over time.

---

## Stage 3 Documents

### [Clarity-Driven Engineering](/docs/clarity_driven_engineering.md)
Defines Owlume’s evolution of Feedback-Driven Engineering (FDE).  
Explains how every reflection becomes a data event, measured by clarity gained per interaction (CGΔ).

### [Clarity Gain Metric](/docs/clarity_gain_metric.md)
Specifies the core KPI of Owlume’s adaptive system — Clarity Gain (CG).  
Describes how clarity_before → clarity_after deltas are computed, weighted, and logged to DilemmaNet.

### [Owlume GPT Monetization Blueprint](/docs/owlume_gpt_monetization_blueprint.md)
Outlines Owlume’s three-layer monetization model: GPT App, Elenx API, and DilemmaNet dataset.  
Shows how CDE turns cognitive feedback into recurring economic value.

### [Owlume Agent Concept](/docs/owlume_agent_concept.md)
Early design paper for the future autonomous Owlume Agent.  
Explores timing, architecture, and roles after 100–500 reflections are logged in DilemmaNet.

---

## License & Attribution

All intellectual property © Owlume 2025. All frameworks (Questioncraft, Elenx, DilemmaNet, Empathy Lens, Clarity Gain) are proprietary conceptual and data structures belonging to the Owlume Project.

---

**Version:** Stage 3 — Execution Phase (October 2025)

───────────────────────────────────────────────
🦉  END OF DOCUMENT — ILLUMINATE, DON’T ASSUME
───────────────────────────────────────────────

>>>>>>> 5776714 (chore(repo): initialize Owlume repo  engine, data packs, schemas, scripts)
