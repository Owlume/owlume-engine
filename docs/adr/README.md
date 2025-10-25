# Owlume — Architecture Decision Records (ADR Index)

> *“If it’s not written, it didn’t clarify.”*  
> Each ADR captures a key design decision that shaped the Owlume engine, data flows, and learning loops.  
> This index provides quick visibility into what was decided, when, and why.

---

## 📘 Purpose
Architecture Decision Records (ADRs) preserve **reasoning** — not just results.  
They ensure that every “vibe-coded” insight is traceable and every parameter choice has a memory.

---

## 🗂️ ADR Directory

| ADR ID | Title | Date | Status | Summary |
|--------|--------|------|---------|----------|
| [ADR-0003](adr-0003_confidence_gated_fusion.md) | Confidence-Gated Fusion for Mode Detection | 2025-10-15 | ✅ Accepted | Added confidence range [0.35 – 0.75], priors ≤ 25 %, empathy auto-toggle. |
| *(reserved)* ADR-0004 | Adaptive Weight Learning Loop | 2025-Q4 (planned) | ⏳ Proposed | Implement auto-tuning of fusion thresholds via Clarity Gain trends. |
| *(reserved)* ADR-0005 | Schema Validation in CI | 2025-Q4 (planned) | ⏳ Proposed | Enforce schema + smoke tests in Stage 4 GitHub Actions. |
| *(reserved)* ADR-0006 | Empathy Weight Calibration | 2025-Q4 (planned) | ⏳ Proposed | Quantify and normalize empathy impact in reflection outcomes. |

---

## 🧭 Usage Guidelines
1. **Create new ADRs** using [`adr_template.md`](adr_template.md).  
2. **Naming convention:** `adr-####_<short_title>.md` (zero-padded).  
3. **Status options:** Proposed → Accepted → Superseded / Deprecated.  
4. **Link each ADR** in this table after commit, with a one-line summary.  
5. **Keep ADRs brief** — ≤ 1 page each. Focus on decision and rationale.  

---

## 🔍 Finding ADRs
In VS Code, search: `ADR-` or `Status:` to quick-jump between decisions.

---

## 🧩 Relation to Instrumented Vibe Coding
ADRs are the *memory layer* of IVC.  
Every AI-assisted or high-context coding moment gets anchored by one of these concise records, turning “vibes” into verifiable knowledge.

---

## ⚙️ Pipeline Integration Note (coming Stage 4 L2)

To keep ADRs **live-checked** inside CI:

1. **Commit Reference Verification**  
   - CI script scans commits for `ADR-####` tags in messages or headers.  
   - Any code touching `src/` or `scripts/` without a linked ADR raises a warning.  

2. **Schema Validation Step**  
   - On every push, CI runs `python scripts/validate_schemas.py` to confirm data packs match their schemas and ADRs referenced in metadata exist.  

3. **Dashboard Traceback**  
   - Aggregated metrics and Clarity Gain reports embed the ADR ID of the decision that defined their logic (e.g., fusion rule → ADR-0003).  

4. **ADR Status Check**  
   - CI compares the index table here to individual ADR files; mismatch or missing status fails lint stage.  

> Result: Every technical decision remains auditable, validated, and connected to runtime evidence — closing the loop between *intent → implementation → impact*.

---

**Tagline:**  
> *“Decisions fade; documentation endures — and CI keeps them honest.”*

