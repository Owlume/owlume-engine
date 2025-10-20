Elenx Documentation Index

This folder stores all documentation for Elenx, Questioncraft, and DilemmaNet — the full Owlume decision-clarity stack.
Every file here connects directly to the JSON data and schemas in /data/ and /schemas/.

🧭 Core Overview
File	Purpose
README.md
	High-level orientation for the entire repo — quickstart for devs and collaborators.
how_to_read_elenx_schemas.md
	Line-by-line guide to reading and understanding Elenx JSON Schemas.
how_to_brief_for_schemas.md
	Template for briefing new schema creation requests in plain language.
empathy_lens.md
 (optional)	Explains how the Empathy Lens overlays the Matrix.
dilemmanet_overview.md
 (optional)	Describes how DilemmaNet stores dilemmas, blind-spot questions, feedback, and outcomes.
elenx_architecture.md
 (optional)	Visual and technical breakdown of Elenx’s engine, pipeline, and JSON data flow.
naming_conventions.md
 (optional)	Consistent file, field, and ID naming rules across the repo.
📂 Relationship Between Folders
elx-repo/
 ├── README.md
 ├── data/         → All live JSON datasets (Matrix, Voices, Fallacies, Context Drivers)
 ├── schemas/      → Validation rules for those datasets
 ├── docs/         → All documentation (you are here)
 └── assets/       → Diagrams, PNGs, and visual aids


/data/ → what the system knows

/schemas/ → how the data must be structured

/docs/ → how humans understand and extend it

🪜 Recommended Editing Flow

Read or update docs here (/docs/) in Markdown.

Edit or expand JSON data in /data/.

Validate JSONs automatically via linked schemas in /schemas/.

Commit and push once all green ✔️ in VS Code.

🧠 Notes for Future Contributors

Keep Markdown concise, versioned, and dated (## Update: YYYY-MM-DD).

Avoid duplicating content between docs — link to existing files instead.

Always run validation before committing new JSON data.

Major conceptual changes → record a short note in /docs/changelog.md.


Why saving to /data/ and /docs/ in VS Code is better than Notion
Reason	What it means for you
Version control	Every edit is tracked. You’ll always know what changed, when, and by whom.
Developer-ready	Devs can clone your repo and instantly see your logic, rules, and examples.
Live validation	VS Code automatically checks JSONs against schemas — Notion can’t.
Docs + Data side-by-side	/docs/ = explanation; /data/ = living source. That pairing is powerful.
Future-proof	GitHub repositories become the canonical record for both logic and philosophy (your “Questioncraft Canon”).
🗂️ Recommended folder discipline (Elenx standard)
elx-repo/
 ├── README.md
 ├── /data/                ← JSON datasets
 │     ├── matrix.json
 │     ├── voices.json
 │     ├── fallacies.json
 │     └── context_drivers.json
 ├── /schemas/             ← matching rulebooks
 │     ├── matrix.schema.json
 │     ├── voices.schema.json
 │     ├── fallacies.schema.json
 │     └── context_driver.schema.json
 ├── /docs/                ← explanations, guides, philosophy
 │     ├── how_to_read_elenx_schemas.md
 │     ├── how_to_brief_for_schemas.md
 │     └── [future Elenx engine diagrams, empathy lens doc, etc.]
 └── /assets/ (optional)   ← diagrams or PNGs


✅ This mirrors exactly how devs will structure the codebase later, so your workspace becomes directly usable.

🧾 Tips for smooth VS Code workflow

Markdown for all docs
Keep everything you’d normally write in Notion as .md files — easy to edit, link, and version.

Use headings consistently
So you can later auto-generate a table of contents in the README.

Save often (Ctrl/Cmd + S)
VS Code doesn’t auto-save like Notion.
You can enable auto-save in Settings → Files → Auto Save → After Delay.

Preview Markdown
Ctrl/Cmd + Shift + V to see how it will render on GitHub.

Commit later (when ready)
You don’t need to push yet — you can build quietly until we do a GitHub sync session.