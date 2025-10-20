🧩 Owlume — Elenx Engine Shim & UI Overview

Stage 3 · Track T1 Step 2
Last updated: Oct 2025

1. Purpose

This module set transforms unstructured text (a user’s reflection, dilemma, or idea) into a structured blind-spot question pack — the first stage where Elenx “thinks.”

It completes the flow:

text → detectMode() → detectPrinciple() → questions → rendered pack

2. Components
File	Role	Key Functions
src/elenx_engine.py	Core Engine Shim — interprets text via the Questioncraft Matrix and applies priors & empathy overlay.	analyze(), detect_mode(), detect_principle(), prescan_priors(), generate_questions(), apply_empathy()
src/question_renderer.py	Converts the engine output into a structured UI payload (stable IDs, timestamps, question list).	render_question_pack()
src/ui_utils.py	Lightweight console / demo renderer for human-readable display.	render_pack_console(), print_pack_console()
3. Data Flow
User text
   │
   ▼
ElenxEngine.analyze()
   ├─ prescan_priors()      → detect fallacies / contexts
   ├─ detect_mode()         → identify best Mode via Matrix tokens
   ├─ detect_principle()    → identify Principle within Mode
   ├─ fuse_with_priors()    → boost confidence if priors fire
   ├─ generate_questions()  → fetch 3–5 guiding Qs from Matrix
   ├─ apply_empathy()       → soften phrasing if empathy_on=True
   ▼
DetectionResult + Questions
   │
   ▼
render_question_pack()      → create UI payload (IDs, labels, questions)
   │
   ▼
render_pack_console()       → pretty print for demo or logs

4. Input & Output Contracts
ElenxEngine.analyze(text: str, empathy_on=False)

Returns:
DetectionResult + List[str]

Field	Type	Description
mode	str	Chosen Questioncraft Mode
principle	str	Chosen Principle within that Mode
confidence	float	Fused confidence (0-1)
priors_used	bool	Whether fallacy/context priors influenced score
empathy_on	bool	Empathy overlay toggle
tags	dict	{ "fallacies": [...], "contexts": [...] }
questions	list[str]	3–5 guiding questions from the Matrix
render_question_pack(...)

Purpose: Converts the engine result into a UI payload ready for front-end or API serialization.

Field	Example	Description
id	"qpack-2a9f04c7c812"	Unique short UUID
created_at	"2025-10-15T07:42:11"	UTC timestamp
mode_id / principle_id	"evidence" / "evidence--contrast"	Stable slugs for linking
mode_label / principle_label	"Evidence" / "Contrast"	Display labels
confidence	0.78	Overall fused score
empathy_on	true	Whether empathy overlay applied
tags	{ "fallacies": ["Cherry-picking"], "contexts": [] }	Active priors
questions	[{"id":"q-...-1","text":"...","order":1},...]	Ordered list of guiding questions
render_pack_console(pack: Dict[str,Any])

Pretty-prints the above payload for debugging or demos.

Output example:

🦉  Owlume — Trade-off × Constraints  (0.78)
Empathy: 🫶 | Fallacies: False Dilemma | Contexts: Overload/Complexity

  1. What trade-offs are being assumed between speed and quality?
  2. Out of care, How might our constraints be shaping this decision?
  3. What would a more balanced perspective reveal?

5. Developer Notes

Dependencies: pure Python 3 stdlib only; no external libraries required.

Extensibility:

Token extraction and overlap logic can later be replaced or fused with semantic embeddings.

Priors are modular — expand via prescan_priors() dictionaries.

Empathy overlay language can be refined in apply_empathy().

Testing:

Run scripts/smoke_test_engine_shim.py → verifies detection + question generation.

Run scripts/smoke_test_renderer.py → verifies payload integrity.

Run scripts/smoke_test_ui.py → verifies console output.

