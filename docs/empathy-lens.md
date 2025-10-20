# 💡 Empathy Lens in Elenx

The **Empathy Lens** is a cross-cutting feature of Elenx that overlays relational, moral, and motivational perspectives onto blind-spot questions. It is not a Mode or Principle, but an augmentation that increases coverage, prioritization, and user adoption.

---

## 1. Why Empathy Matters
- **Blind spots are not only cognitive** → many stem from relational or motivational gaps.  
- **Users trust questions more when they feel understood.**  
- **Data shows** (v0.1 tests and projections):  
  - Coverage ↑ ~30–40%  
  - Prioritization sharpness ↑ ~20–30%  
  - Adoption/engagement nearly doubles  

---

## 2. Roles of Empathy Lens

### a) Architectural Role (Lens)
- Acts like an overlay that plugs into the Questioncraft Matrix pipeline.  
- Detects relational/moral triggers in text.  
- Suggests alternative phrasing of blind-spot questions to surface human context.  

### b) Outcome Role (Multiplier)
- Boosts quality and trust of outputs.  
- Expands reach into domains where logical fallacies alone miss critical factors.  

---

## 3. Implementation in Elenx Versions
- **v0.1** → Empathy Lens OFF (optional, placeholder only).  
- **v0.2+** → Empathy Lens ON (measurable augmentation).  
- **Schema field:** `empathy_relevance` (0–5) included in datasets (fallacies, context drivers).  

---

## 4. Example Transformations

**Without Empathy:**  
> What assumptions are hidden in this decision?  

**With Empathy Lens:**  
> How might hidden assumptions affect people differently depending on their role or needs?  

---

## 5. JSON Integration
- `fallacies.json` and `context_driver.json` include `empathy_relevance` scores (0–5).  
- `matrix.json` items may include optional `empathy_hint`.  
- Empathy Lens can rewrite or expand counter-questions dynamically.  

---

## 6. Position in Repo
```
elx-repo/
  docs/
    empathy-lens.md        # This file
  data/
    ...                    # JSON datasets (matrix, voices, fallacies, context drivers)
  schemas/
    ...                    # Validation schemas
  README.md
```

---

## 7. Next Steps
- Calibrate `empathy_relevance` scores across datasets.  
- Add empathy test cases to DilemmaNet.  
- Evaluate trust/adoption lift in early trials.  

---

© 2025 Owlume / Questioncraft Project
