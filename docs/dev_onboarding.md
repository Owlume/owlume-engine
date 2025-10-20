───────────────────────────────────────────────
   🦉  OWLUME — DEV ONBOARDING GUIDE (v1.0)
   Illuminate Blind Spots. Build Clarity.
───────────────────────────────────────────────

| 🧾 **Dev Onboarding Status** | **Details** |
|------------------------------|-------------|
| **Version** | v1.0 — Pre-Integration |
| **Stage** | Stage 3 — Execution Phase |
| **Environment** | Elenx Repo (VS Code + JSON Validation Ready) |
| **Focus Tracks** | T1 — Engine Integration • T2 — Logging Setup |
| **Status** | ✅ Documentation Complete • 🧩 Awaiting Implementation |
| **Next Milestone** | T1 — Connect JSON Packs to `detectMode()` Logic |
| **Maintainers** | Brian (Founder) • Ted (AI Partner) |
| **Last Updated** | October 2025 |


Welcome to OWLUME (Elenx Repository)

This guide orients new developers and collaborators.
Owlume is a reflection engine that transforms human text into structured blind-spot questions using Questioncraft, the Elenx Engine, and DilemmaNet learning loop.

🧭 1. Purpose

Owlume converts reflection into clarity.
It analyzes user text → identifies blind spots → generates sharp, human questions → logs learning into DilemmaNet.

The build fuses:

Questioncraft Matrix (reasoning structure)

Elenx Engine (logic core)

DilemmaNet (data spine)

Empathy Lens (human layer)

Clarity Gain Metric (value measure)

🗂️ 2. Repository Structure
Folder	Description
/data/	Core JSON datasets (matrix, voices, fallacies, context drivers).
/schemas/	JSON Schema validators for each dataset.
/docs/	Explanatory files (architecture, empathy, companion guides).
/qa/	Golden Set tests, proof-of-clarity scripts, validation samples.
/archive/	Historical or deprecated design notes.
/logs/ (optional)	Runtime logs (DilemmaNet or clarity-gain samples).
⚙️ 3. Getting Started (Developers)

Open in VS Code

Make sure JSON Schema validation is active.

Run Validation Tasks

.vscode/tasks.json → “Validate All JSON Files.”

Expect 0 schema errors before build.

Explore Data Packs

matrix.json — Questioncraft Matrix

voices.json — tone/voice definitions

fallacies.json / context_drivers.json — diagnostic priors

Load Core Data

(Later) via elenx_loader.py → load_matrix(), etc.

Run Reasoning Engine

(Later) elenx_engine.py handles:

detectMode()

detectPrinciple()

empathy overlay

fallacy/context scanning

Observe Output

Input text → questions tagged by Mode × Principle.

Results logged into /logs/dilemmalog_sample.jsonl.

🧩 4. Key Concepts (Quick Glossary)
Term	Meaning
Mode	High-level blind-spot type (e.g., Evidence, Assumption).
Principle	Guiding lens within each Mode (e.g., Contrast, Causality).
Empathy Lens	Adjusts tone and relational precision.
DilemmaNet	Logs reflections, blind-spot tags, and Clarity Gain metrics.
Clarity Gain (CG)	Measured improvement in user clarity.
CDE Loop	Clarity-Driven Engineering — the system learns from reflection data.
🧠 5. Orientation for New Developers

Start with /README.md — system overview.

Then read /docs/stage3_companion_guide.md — explains build tracks (T1–T4).

Review /docs/img/stage3_pipeline.png — visual summary.

Validate JSONs before editing.

For any unclear logic, find the explainer doc with the same name under /docs/.

🔐 6. Ground Rules

Keep schema alignment.

Don’t change structure without updating its schema.

Respect version locks.

Files ending in _v1, _v2 = stable checkpoints.

Commit with context.

Messages must explain why, not just what.

Prioritize interpretability.

Owlume’s edge is clarity — not complexity.

✅ 7. Build Sequence (Dev Workflow)
Step	Description
1. Validation	Confirm JSON–Schema alignment.
2. Engine Integration	Implement elenx_engine.py logic (T1).
3. Logging	Connect DilemmaNet + Clarity Gain (T2).
4. UX Integration	Test in GPT interface (T3).
5. Feedback Loop	Activate CDE learning dashboard (T4).
✉️ 8. Contact / Context
Role	Name	Notes
Founder / Product Lead	Brian	Vision, Questioncraft, and system design.
System Guide / Spec Author	Ted (AI Partner)	Architecture, documentation, and logic spec.

(End of file — ready for /docs/dev_onboarding.md)