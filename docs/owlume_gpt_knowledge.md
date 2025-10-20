🦉 Owlume — Questioncraft Knowledge Pack (MVP v1.0)
What the Questioncraft Matrix Is

Owlume runs on the Questioncraft Matrix — a structured map of how humans miss what matters.
It combines:

5 Modes (ways of thinking) × 6 Principles (rules of clarity) → 30 lenses for spotting blind spots.
When text is analyzed, the Matrix routes it through these lenses to surface blind-spot questions — questions that reveal hidden assumptions, missing evidence, or overlooked consequences.

Each output question is tagged with:

Mode × Principle + Voice


Example:

Analytical × Evidence (Feynman Voice):
“What evidence would convince you that your current assumption is wrong?”

How the Empathy Lens Works

Empathy is an optional overlay — not a separate mode.
When OFF, Owlume focuses purely on logical and structural blind spots.
When ON, it adds relational, emotional, and moral depth — surfacing questions about human impact and perspective.

Example:

Relational Overlay:
“How might others who depend on this decision experience its side-effects?”

Empathy increases coverage (~30–40%) and makes questions feel more grounded in real human context.

What the Outputs Look Like

For any dilemma or decision text, Owlume returns 3–5 blind-spot questions, each clearly labeled.

Sample Output

{
  "blind_spot_questions": [
    {
      "qid": "Q-2025-001",
      "mode": "Analytical",
      "principle": "Evidence",
      "voice": "Feynman",
      "text": "What proof would make your assumption false?"
    },
    {
      "qid": "Q-2025-002",
      "mode": "Creative",
      "principle": "Alternatives",
      "voice": "Thiel",
      "text": "What’s the opposite idea that might secretly be true?"
    }
  ],
  "empathy": "off",
  "spec_version": "2025-10-08"
}

Attribution & Version

Questioncraft Matrix © Owlume 2025
Specification: MVP v1.0 (2025-10-08)
Empathy Lens © Owlume — overlay framework for moral and relational blind-spot detection.