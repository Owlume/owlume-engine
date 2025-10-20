🪶 THE “ELENX SCHEMA BRIEF” TEMPLATE

When you want me to write a new schema, just tell me these six things — in your own words.
I’ll translate the rest into code.

1️⃣ Purpose

“This file defines what kind of data and why it matters.”

Example:

“This file defines all empathy lens overlays, so Elenx can tag which questions need relational framing.”

💡 Why: This helps me decide whether the structure should be a list, map, or nested map.

2️⃣ Structure (what the data looks like in your head)

“Each record contains ___.”
“It’s stored as a list / a map / grouped by category.”

Example:

“Each empathy lens entry has an id, label, trigger examples, and a short description.
They live inside an array called ‘lenses’.”

💡 Why: This tells me if the schema should use properties, patternProperties, or items.

3️⃣ Required vs Optional fields

“These are required; these are nice-to-have.”

Example:

“id, label, and description are required.
example and tone are optional.”

💡 Why: I’ll put these under required or leave them flexible.

4️⃣ Constraints / Rules

“IDs must look like ___.”
“No extra fields allowed.”
“Minimum one item in list.”

Example:

“IDs should be lowercase with underscores.
No extra keys.
Must have at least one lens.”

💡 Why: I’ll add regex patterns, additionalProperties:false, and minItems.

5️⃣ Versioning

“Add a spec tag like 'empathy.v1' at the top.”

💡 Why: I’ll make sure it includes "spec": "..." and set up $schema properly for VS Code validation.

6️⃣ Example entry (1 or 2 lines)

“Just to show what the data might look like.”

Example:

{
  "id": "trust_gap",
  "label": "Trust Gap",
  "description": "Occurs when intent is misread as manipulation.",
  "example": "How can I signal good faith more clearly?"
}


💡 Why: From this small example, I can infer 90% of the schema shape.

🧠 In short: you brief me like this

“Partner, create a schema for a dataset that lists all empathy lenses.
Each lens has: id (required, lowercase), label (required), description (required), and optional example.
Put everything in an array called ‘lenses’.
Add a spec field like ‘empathy.v1’ at the top.
No extra properties allowed.”

That’s it — from this short plain-English instruction, I’ll automatically create:

a valid JSON Schema (empathy.schema.json)

the matching empty data template (empathy.json)

and a 3-line explanation in human language (“what this schema enforces”).

✅ Why this works

Because schemas are logic, not magic: they only need to know

what’s inside,

what’s required,

what’s forbidden,

and how strict to be.

You supply those; I handle syntax, versioning, and structure.
