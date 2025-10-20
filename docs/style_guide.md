🦉 OWLUME — Documentation Style Card

File: /docs/style_guide.md
Purpose: Maintain consistency and identity across all Markdown docs in the Owlume (Elenx) repository.

🧭 1. Philosophy

Every Owlume document should feel as clear as it reads.
The design language expresses the product’s purpose — Illuminate blind spots. Build clarity.
That means:

Minimal noise

Consistent visual rhythm

Purposeful hierarchy

Readable in both dark and light modes

🏗️ 2. Document Layout Standard

Each doc should include three visual anchors:

Section	Purpose	Example
Header Banner	Establishes identity and phase	────────────────────────── block with owl + tagline
Status Block	Shows current version, phase, and focus	2-column table labeled “🧾 Project Status” or “🧾 Dev Onboarding Status”
Footer Banner	Provides philosophical or emotional close	“🦉 END OF DOCUMENT — ILLUMINATE, DON’T ASSUME”

🪶 3. Header Banner Template
───────────────────────────────────────────────
   🦉  OWLUME — [DOCUMENT TITLE IN CAPS]
   [Short tagline or purpose line]
───────────────────────────────────────────────


Examples

🦉 OWLUME — ILLUMINATE BLIND SPOTS

🦉 OWLUME — DEV ONBOARDING GUIDE (v1.0)

🦉 OWLUME — CLARITY-DRIVEN ENGINEERING NOTES

Rules

Always use 3 lines (top border, title line, bottom border).

Title line must include the 🦉 emoji and a concise title.

Optional second line: purpose or phase.

🧾 4. Status Block Template
| 🧾 **[Status Type]** | **Details** |
|------------------------|-------------|
| **Version** | vX.X — [stage/phase descriptor] |
| **Stage** | Stage 3 — Execution Phase |
| **Focus Tracks** | [T1–T4 summary] |
| **Status** | [Design Complete / Build in Progress / Released] |
| **Next Milestone** | [Upcoming step] |
| **Maintainers** | Brian (Founder) • Ted (AI Partner) |
| **Last Updated** | [Month Year] |


Examples

README.md → Project Status

dev_onboarding.md → Dev Onboarding Status

clarity_gain_metric.md → Metric Design Status

🧩 5. Footer Banner Template
───────────────────────────────────────────────
🦉  END OF DOCUMENT — ILLUMINATE, DON’T ASSUME
───────────────────────────────────────────────


Use this footer on all major docs (README, onboarding, companion guides, blueprints).
It signals closure and reinforces Owlume’s voice — calm, precise, reflective.

✏️ 6. Tone & Voice Guidelines
Dimension	Guideline
Tone	Intelligent but approachable — no jargon without purpose.
Style	Use short declarative sentences; clarity over cleverness.
Headings	Use sentence case (## Stage 3 — Companion Guide), not all caps.
Bullets	Use • or – for mid-level lists; avoid nested bullets deeper than two levels.
Icons/Emojis	Use sparingly to orient (🦉 for brand, ⚙️ for process, 💡 for insight).
Timestamps	Include “Last Updated” in status block — month and year only.

🧩 7. File Naming Conventions (Docs)
Type	Format	Example
Main README	README.md	Root system overview
Companion Guide	stage3_companion_guide.md	Execution guide
Developer File	dev_onboarding.md	Onboarding reference
Style Guide	style_guide.md	This file
Blueprints	*_blueprint.md	owlume_gpt_monetization_blueprint.md
Metrics	*_metric.md	clarity_gain_metric.md
Archived Notes	/archive/*.md	archive/owlume_train_manifest_map.md

💡 8. Visual Rhythm Checklist

Before saving a new doc:

✅ Header banner present

✅ Status block near the top

✅ Logical section hierarchy

✅ Footer banner at bottom

✅ “Last Updated” field filled

✅ Tone consistent with Owlume brand

📘 9. Template Snippet (Copy & Start)

Here’s a pre-formatted structure to start any new Owlume Markdown doc:

───────────────────────────────────────────────
   🦉  OWLUME — [DOCUMENT TITLE]
   [Optional tagline or purpose line]
───────────────────────────────────────────────

| 🧾 **[Status Type]** | **Details** |
|------------------------|-------------|
| **Version** | vX.X — [Descriptor] |
| **Stage** | Stage 3 — Execution Phase |
| **Focus** | [Brief focus summary] |
| **Status** | [In Progress / Complete] |
| **Maintainers** | Brian • Ted |
| **Last Updated** | [Month Year] |

## 1. Overview
[Explain what this doc is for.]

## 2. Core Concepts
[Summarize the logic or framework.]

## 3. Implementation or Process
[Describe how it fits or runs.]

## 4. Outcome or Next Steps
[What this leads to.]

───────────────────────────────────────────────
🦉  END OF DOCUMENT — ILLUMINATE, DON’T ASSUME
───────────────────────────────────────────────

✅ 10. Why This Matters

Owlume’s credibility depends on structured clarity — not just in how it thinks, but in how it documents its thinking.
This style guide ensures that clarity scales as you add new developers, documents, and datasets.