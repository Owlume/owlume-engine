# 🧭 Owlume Naming Conventions — Global Tracks Across Stages
**File:** `/docs/naming_conventions_global_tracks.md`  
**Version:** 1.0 (2025-10-30)

---

## 1. Purpose
This document defines how **Tracks (T#)** and **Stages (S#)** interact across the Owlume technical roadmap.  
It ensures consistent naming, traceability, and scalability across the 8 Stages of technical execution.

---

## 2. Core Principle
> **Tracks persist; Stages progress.**  
> Each *Track* represents a core subsystem of Owlume (Elenx, DilemmaNet, UX, Dashboard, Agent).  
> Each *Stage* represents a macro-phase of evolution (from build → learning → activation → distribution).  
>  
> A Track can appear in multiple Stages — evolving from prototype to live system — but it keeps the same global ID.

---

## 3. Hierarchy
Stage (S#) → Track (T#) → Step (S# inside)

| Symbol | Meaning | Example |
|---------|----------|----------|
| **S#** | Macro development phase | Stage 5 = Activation Phase |
| **T#** | Persistent subsystem family | T5 = Learning Agent / Nudge System |
| **S# (nested)** | Sequential step inside that Stage | S2 = Runtime Core |

---

## 4. Global Track Families

| Track | Core Focus | Introduced | Continues Through |
|--------|-------------|-------------|--------------------|
| **T1** | Elenx Engine Integration | Stage 3 | Stage 4 → Stage 6 |
| **T2** | DilemmaNet & Clarity Gain Logging | Stage 3 | Stage 5 → Stage 6 |
| **T3** | UX & App Integration | Stage 3 | Stage 5 → Stage 7 |
| **T4** | Dashboard & Instrumentation | Stage 3 | Stage 5 → Stage 8 |
| **T5** | Nudge System → Learning Agent → Distribution Intelligence | Stage 3 | Stage 5 → Stage 8 |

---

## 5. File Naming Convention

T{TrackID}-S{StageID}-S{StepID}_{short_description}.py

### Example — Stage 5 (Activation Phase)
/src/agent/
T5-S5-S1_mini_ux_demo.py
T5-S5-S2_runtime_core.py
T5-S5-S3_feedback_bridge.py
T5-S5-S4_dashboard_v2.py


**Breakdown**
- **T5** → Learning Agent subsystem (descended from Nudge System)  
- **S5** → Stage 5 = Activation Phase  
- **S1–S4** → Sequential build steps within that stage  

---

## 6. Commit & CI Naming
Use the full `T#-S#` scope for commits, tasks, and CI logs for perfect traceability.

| Context | Example |
|----------|----------|
| **Commit message** | `feat(T5-S5): implement learning agent runtime core` |
| **CI output** | `[T5-S5-S3] feedback bridge passed all tests` |
| **Pull request title** | `T5-S5: Activate runtime core and empathy feedback merge` |

---

## 7. Strategic vs Technical Usage

| Layer | Use “Stage” or “Track”? | Example | Context |
|--------|--------------------------|----------|----------|
| **Docs / Roadmaps** | **Stage-first (S5-T1)** | “Stage 5 → Track 1: Agent Activation” | Human-readable strategy |
| **Code / Commits / CI** | **Track-first (T5-S5)** | `T5-S5-S2_runtime_core.py` | Machine-sortable execution |

**Guiding Rule:**  
> *Stage for storytelling, Track for building.*

---

## 8. Example Evolution — Track 5 Lineage

| Stage | File / Task | Meaning |
|--------|--------------|----------|
| **Stage 3** | `T5-S3-nudge_scheduler.py` | Prototype daily nudge system |
| **Stage 4** | `T5-S4-nudge_emitter.py` | Adaptive nudge integration with Clarity Gain |
| **Stage 5** | `T5-S5-S2_runtime_core.py` | Nudge logic elevated to Learning Agent runtime |
| **Stage 6** | `T5-S6-distribution_hooks.py` | Agent expands to distribution intelligence |
| **Stage 7+** | `T5-S7-enterprise_bridge.py` | Enterprise-level integration of adaptive Agent |

---

## 9. Benefits
✅ Clear lineage of subsystems across stages  
✅ Clean alphabetical sorting in GitHub / VS Code  
✅ Immediate visual traceability in commits  
✅ No collision between Stages using the same Track numbers  

---

## 10. Quick Reference

| Symbol | Meaning | Example |
|---------|----------|----------|
| **S#** | Stage Number | `S5 → Activation Phase` |
| **T#** | Track Number | `T5 → Learning Agent` |
| **S# (inner)** | Step Number | `S2 → Runtime Core` |
| **Full Pattern** | `T5-S5-S2_runtime_core.py` | Track 5, Stage 5, Step 2 |

---

### 🦉 Guiding Mantra
> **“Tracks persist; Stages progress.”**  
> The architecture learns like Owlume itself — each Stage a new level of clarity,  
> each Track a continuing thread of intelligence.

---
