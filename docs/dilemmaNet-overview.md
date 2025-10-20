# 🔗 DilemmaNet Overview

DilemmaNet is the **data spine** of Owlume’s Questioncraft ecosystem. It captures user dilemmas, generated blind-spot questions, feedback, and outcomes — forming the proprietary dataset that powers and defends Elenx.

---

## 1. Purpose
- Provide a **living dataset** of real-world dilemmas and blind-spot questions.  
- Anchor Elenx outputs in **feedback loops** rather than static knowledge.  
- Create a **defensible moat**: competitors can’t replicate the dataset without user interaction history.  

---

## 2. How It Works
1. **Input** → User highlights or types a dilemma.  
2. **Processing** → Elenx applies the Questioncraft Matrix, generates blind-spot questions, tags with fallacies/context drivers, overlays Voices and Empathy (optional).  
3. **Feedback** → User selects or rates the most relevant blind-spot questions.  
4. **Storage** → All data (dilemma + tags + feedback) logged into DilemmaNet.  
5. **Iteration** → Over time, DilemmaNet refines Elenx, improving accuracy and coverage.  

---

## 3. Core Data Model (IDs)
- **DID** → Dilemma ID (unique identifier for each dilemma).  
- **CID** → Context ID (links text + tags from Matrix, Fallacies, Context Drivers).  
- **QID** → Question ID (generated blind-spot question).  
- **FID** → Feedback ID (user ratings, selections).  
- **OID** → Outcome ID (later outcomes/results if tracked).  
- **UID** → User ID (anonymized reference to user).  

---

## 4. JSON Integration
DilemmaNet is not a single JSON file but a **pipeline of logs**. Example record:

```json
{
  "did": "D20251004-001",
  "uid": "U123",
  "dilemma_text": "Should I raise VC funding now or bootstrap longer?",
  "context": {
    "cid": "C045",
    "principle_tags": ["risk","assumption"],
    "mode_tags": ["analytical","growth"],
    "fallacy_tags": ["false-dilemma"],
    "context_drivers": ["time_pressure"]
  },
  "generated_questions": [
    {
      "qid": "Q567",
      "text": "What hybrid financing options exist beyond VC or bootstrapping?",
      "voice_overlay": "Peter Thiel",
      "empathy_overlay": "How would this choice affect your team’s stability?"
    }
  ],
  "feedback": [
    {
      "fid": "F890",
      "qid": "Q567",
      "rating": 5,
      "selected": true
    }
  ],
  "timestamp": "2025-10-04T08:00:00Z"
}
```

---

## 5. Relationship to Other Pillars
- **Matrix** → provides the 30 guiding questions (baseline lens).  
- **Voices** → diversify style and perspective of questions.  
- **Empathy Lens** → overlays relational/moral context, boosting trust.  
- **DilemmaNet** → logs all of the above into a dataset, creating compounding value.  

---

## 6. Growth Phases
- **Phase 1**: Seed with 500–1,000 dilemmas (hand-curated, early users).  
- **Phase 2**: Expand to 10k dilemmas with structured feedback.  
- **Phase 3**: Reach 50k–100k dilemmas → clear moat, investor-grade dataset.  
- **Phase 4**: Package with whitepapers, IP filings, and scaling strategies.  

---

## 7. Repo Position
```
elx-repo/
  docs/
    dilemmaNet-overview.md
  data/
    ...
  schemas/
    ...
  README.md
```

---

## 8. Next Steps
- Define JSONL (JSON Lines) format for logging dilemmas.  
- Align schema for DilemmaNet with existing datasets (Matrix, Fallacies, Context Drivers).  
- Begin testing feedback loop with early adopters.  

---

© 2025 Owlume / Questioncraft Project
