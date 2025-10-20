# 🧩 Elenx Architecture Overview

Elenx is the **engine** of Owlume’s Questioncraft system. It applies the Questioncraft Matrix, overlays Voices, and tags blind spots using Fallacies and Context Drivers. This document gives a structured overview of how Elenx works.

---

## 1. Core Philosophy
- **Purpose:** Reveal blind spots that derail decisions more than ignorance.  
- **Foundation:** Questioncraft Matrix (5 Modes × 6 Principles).  
- **Overlays:** Voices (e.g., Thiel, Peterson, Feynman), Empathy Lens.  
- **Root causes of blind spots:** Logical fallacies + Contextual drivers.  
- **Dataset Spine:** DilemmaNet (stores dilemmas, blind-spot questions, feedback).  

---

## 2. Elenx Pipeline (v1.2)
**Flow:**  
1. **Input:** User highlights or enters text.  
2. **Processing:**  
   - Parsed through Questioncraft Matrix (30 guiding questions).  
   - Blind-spot questions generated.  
   - Tagged with fallacies and context drivers.  
   - Optional Empathy Lens overlay.  
   - Optional Voices overlay.  
3. **Output:** 3–5 blind-spot questions returned to the user.  
4. **Feedback:** User selects/rates → logged into DilemmaNet.  

---

## 3. Data Components (JSON-based)
- **matrix.json** → 30 guiding questions, definitive.  
- **voices.json** → question overlays, style modifiers.  
- **fallacies.json** → logical fallacies, linked to Matrix principles.  
- **context_driver.json** → systemic drivers (e.g., misaligned incentives, overload).  

Each is validated by a schema in `/schemas/`.  

---

## 4. Empathy Lens (Cross-Cutting)
- **Overlay role:** adds relational/moral perspective to blind-spot questions.  
- **Multiplier role:** increases coverage, prioritization, and adoption.  
- Implemented as an optional **lens** in Elenx v0.2+.  

---

## 5. DilemmaNet (Data Spine)
- Stores dilemmas, CID/QID pairs, feedback, and outcomes.  
- Provides the defensibility moat (proprietary dataset).  
- Schema includes IDs (DID, CID, QID, FID, OID, UID).  

---

## 6. Repo Structure (Recap)
```
elx-repo/
  data/       # JSON datasets (matrix, voices, fallacies, context drivers)
  schemas/    # Validation schemas
  docs/       # Documentation (naming conventions, architecture, empathy lens)
  README.md   # Project overview
```

---

## 7. Next Steps
- Populate JSON files with v0.1 data (Matrix, 20–40 fallacies, 5 voices, 5–10 context drivers).  
- Enable schema validation in VS Code.  
- Begin logging dilemmas into DilemmaNet.  
- Iterate feedback loop to refine schema + content.  

---

© 2025 Owlume / Questioncraft Project
