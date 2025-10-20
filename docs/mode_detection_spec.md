# Elenx Mode Detection – Spec (v1)

This document specifies how `detectMode(userText)` classifies text into one or two Modes: Analytical, Critical, Creative, Reflective, Growth.

---

## 1. Objective
Produce robust **multi-label** mode scores using a hybrid method that works well in cold-start and improves as DilemmaNet grows.

---

## 2. Inputs & Outputs
- **Input:** `userText` (string), optional `ThreadContext` (recent modes, user toggles)
- **Output:**
  ```json
  {
    "modes": ["Analytical", "Critical"],
    "scores": {"Analytical":0.72, "Critical":0.61, "Creative":0.18, "Reflective":0.12, "Growth":0.22},
    "confidence": 0.11,
    "rationale": {"Analytical":"mentions compare/estimate", "Critical":"flags risk/assumption"}
  }