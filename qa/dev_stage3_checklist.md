───────────────────────────────────────────────
   🦉  OWLUME — STAGE 3 DEVELOPER CHECKLIST
   Elenx Engine • DilemmaNet Logging • Clarity Loop
───────────────────────────────────────────────

| 🧾 **Checklist Status** | **Details** |
|--------------------------|-------------|
| **Version** | v1.0 — Pre-Integration |
| **Stage** | Stage 3 — Execution Phase |
| **Focus Tracks** | T1 — Elenx Engine • T2 — DilemmaNet Logging |
| **Status** | ⏳ In Progress |
| **Maintainers** | Brian (Founder) • Ted (AI Partner) • [Developer] |
| **Last Updated** | October 2025 |

---

## ✅ Developer Run Sheet (10-Step Completion Checklist)

| # | Task | Description | Status |
|---|------|--------------|--------|
| 1 | **Repo Setup** | Clone `elx-repo`, open in VS Code, ensure JSON Schema validation is enabled. | ☐ |
| 2 | **Environment Check** | Run `.vscode/tasks.json` → “Validate All JSON Files”. Confirm *0 schema errors*. | ☐ |
| 3 | **Data Load Test** | Execute `src/elenx_loader.py` to load all JSON packs (Matrix, Voices, Fallacies, Context Drivers). | ☐ |
| 4 | **Engine Integration** | Implement and test `detectMode()` + `detectPrinciple()` functions in `elenx_engine.py`. | ☐ |
| 5 | **Empathy Overlay** | Add empathy toggle logic (`apply_empathy_overlay()`) and confirm output tone changes. | ☐ |
| 6 | **Fallacy/Context Scan** | Integrate lightweight pre-scan (priors) and confirm combined results are stable. | ☐ |
| 7 | **DilemmaNet Logger** | Create `dilemmanet_logger.py` → record `DID`, `CID`, `QID`, `CG_pre`, `CG_post`, `CG_delta`. | ☐ |
| 8 | **Smoke Test** | Run `scripts/smoke_test_clarity_gain.py` → confirm Clarity Gain output logged in `/logs/`. | ☐ |
| 9 | **Golden Set QA** | Test 20 dilemmas (from `/qa/golden_set.md`) → verify ≥85% Mode × Principle alignment. | ☐ |
| 10 | **Final Validation** | Re-run all JSON + schema validations, commit clean state with tag `stage3_complete`. | ☐ |

---

## 🧠  Tips for Smooth Execution
- Keep logs small and structured (`.jsonl` format).  
- Run validations often — *no schema drift allowed*.  
- Keep all outputs interpretable — if it’s unclear to a human, fix it.  
- Every question must remain **diagnostic, not advisory.**

---

## 🧾  Completion Criteria

✅ All 10 boxes checked  
✅ No schema errors  
✅ Golden Set QA ≥ 85%  
✅ Output logs show Clarity Gain entries  
✅ Final commit pushed with `stage3_complete` tag

---

───────────────────────────────────────────────
🦉  END OF DOCUMENT — ILLUMINATE, DON’T ASSUME
───────────────────────────────────────────────
