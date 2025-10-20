# Owlume Golden Set — QA & Acceptance Test Guide (v1)

**Purpose:**  
This golden set verifies that Elenx isn’t “just another AI wrapper.”  
It tests whether the engine can correctly detect **blind-spot patterns** and map them to the **Questioncraft Matrix (Mode × Principle)**.

---

## 🧭 What’s Inside

- **owlume_golden_dilemmas_v1.csv** → structured dataset (20 dilemmas, Mode × Principle labels)  
- **owlume_golden_dilemmas_v1.md** → readable Markdown version for manual review  

Each dilemma = one real-world decision scenario (2–4 sentences).  
Each is pre-tagged with the *expected* Mode and Principle that a human Questioncrafter would assign.

---

## 🧪 How to Use

1. **Feed to Elenx:**  
   Import or paste each dilemma as a test input to `detectMode()` and `detectPrinciple()` functions.

2. **Compare Outputs:**  
   - Check if Elenx’s predicted Mode and Principle match the tags in the CSV.  
   - Note confidence scores and disagreements.  
   - Record whether empathy overlay or fallacy/context priors influenced the result.

3. **Acceptance Criteria:**  
   - ≥ 75% Mode match accuracy across the 20 dilemmas.  
   - ≥ 80% Principle alignment when empathy lens is ON.  
   - Explanations must reference **Matrix terms**, not generic reasoning.

4. **Log Results:**  
   Save your test results to `/data/qa_results/` (create this folder if needed).  
   Each test run should include:
   - timestamp  
   - dilemma id  
   - predicted Mode/Principle  
   - confidence  
   - notes on mismatch or interpretation.

---

## 🧩 Next Step

Future QA versions will:
- Add empathy-off vs empathy-on comparison columns.  
- Expand to 50 dilemmas drawn from DilemmaNet once v0.2 dataset matures.

---

**Maintainer:** You (Brian Shen)  
**Spec Version:** 2025-10-10  
**File location:** `/data/golden_set_readme.md`
