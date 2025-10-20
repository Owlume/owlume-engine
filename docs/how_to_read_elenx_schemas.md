1️⃣ Voices Schema
Schema Snippet	Meaning (Plain Language)	Example That Passes
"type": "object"	Whole file must be { ... }.	✅ { "spec": "...", "defaults": {...}, "voices": [...] }
"required": ["spec","defaults","voices"]	All three keys must exist.	✅ all present ❌ missing one
"spec": { "type": "string" }	Version tag as plain text.	"spec": "voices.v1"
"defaults": { "type": "object" }	Must contain a sub-object.	"defaults": { "voice": "feynman" }"
"voices": { "type": "array" }	Must be a list of voice objects.	[ {...}, {...} ]
Each voice "id","label","style","example"	Defines the voice profile.	{ "id": "feynman","label":"Richard Feynman","style":"clear","example":"Why?" }
"required":["id","label","style"]	These three are mandatory.	✅ includes all three
"additionalProperties": false	No unlisted keys allowed.	❌ adding "tone": "curious" fails
2️⃣ Matrix Schema
Schema Snippet	Meaning (Plain Language)	Example That Passes
"type": "object"	File must be an object.	{ "Analytical": {...} }
"patternProperties": { "^[A-Za-z]+$": {...} }	Top-level keys = words only (your Modes).	"Analytical" ✅, "1Mode" ❌
Inner "patternProperties": { "^[A-Za-z]+$": {"type":"string"} }	Inside each Mode, keys = Principles, each value = guiding-question text.	"Assumptions": "What am I taking for granted?" ✅
"additionalProperties": false"	Forbids extra fields at both levels.	"Notes": "draft" ❌

✅ English summary:

Matrix = { Mode → { Principle → Question(string) } }

3️⃣ Fallacies Schema
Schema Snippet	Meaning (Plain Language)	Example That Passes
"type": "object"	Whole file is { ... }.	{ "spec": "...", "fallacies": [...] }
"required": ["spec","fallacies"]	Both must exist.	✅ has both
"fallacies": { "type": "array", "minItems": 1 }	Must be a non-empty list.	[ {...} ] ✅, [] ❌
Each "items": { "type": "object" }	Every list item = one fallacy object.	{ "id":"false_dilemma" }
"id": {"type":"string","pattern":"^[a-z0-9_]+$"}	Lowercase id, underscores allowed.	"false_dilemma" ✅, "False Dilemma" ❌
"label","definition": {"type":"string"}	Both must be text.	"label":"False Dilemma"
"required":["id","label","definition"]	All three fields required.	✅ complete entry
"additionalProperties": false	No extra fields like "example".	❌ fails if extra

✅ English summary:

Fallacies = [ {id, label, definition} ]

4️⃣ Context Drivers Schema
Schema Snippet	Meaning (Plain Language)	Example That Passes
"type": "object"	File must be { ... }.	{ "spec": "...", "drivers": [...] }
"required": ["spec","drivers"]	Both keys required.	✅ ok
"drivers": { "type":"array","minItems":1 }	At least one driver.	[ {...} ] ✅
Each "items": { "type":"object" }	Each entry = one driver.	{ "id":"incentive_misalignment" }
"id": {"pattern":"^[a-z0-9_]+$"}	Lowercase, underscores only.	"identity_protection" ✅
"label","definition": {"type":"string"}	Must be text.	"label":"Incentive Misalignment"
"required":["id","label","definition"]	All three mandatory.	✅ complete
"additionalProperties": false	Nothing else allowed.	❌ "example":"..."

✅ English summary:

Context Drivers = [ {id, label, definition} ]