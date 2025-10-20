───────────────────────────────────────────────
   🦉  OWLUME — CLARITY-DRIVEN ENGINEERING (CDE)
   Build Fast • Learn Clearly • Adapt Intelligently
───────────────────────────────────────────────

| 🧾 **Philosophy Status** | **Details** |
|---------------------------|-------------|
| **Version** | v1.0 — Pre-Integration |
| **Stage** | Stage 3 — Execution Phase |
| **Purpose** | Apply engineering feedback loops to clarity, not just behavior |
| **Status** | ✅ Defined • 🧩 Instrumentation Pending |
| **Next Milestone** | Connect CDE signals to DilemmaNet & Clarity Gain metrics |
| **Maintainers** | Brian (Founder) • Ted (AI Partner) |
| **Last Updated** | October 2025 |


# Clarity‑Driven Engineering (CDE)

> **Owlume’s evolution of Feedback‑Driven Engineering (FDE):** optimize for *cognitive clarity* over *behavioral activity*.

---

## 1) Purpose & Philosophy

**Goal:** Continuously increase *clarity gained per interaction (CG)* while preserving FDE’s learning speed.

**Premise:** In Owlume, feedback is cognitive. Each question is a probe; each reflection is a measurement.

**North Star:** *Maximize CG while keeping latency low and safeguards high.*

---

## 2) CDE Core Loop (Operational)

1. **User Interaction** → text/voice/nudge.
2. **DilemmaNet Logging** → capture dilemma intent + tags (Mode × Principle + fallacy/context drivers) and session context.
3. **Clarity Delta Compute** → compare pre vs post reflection states; derive `clarity_delta`.
4. **Adaptive Adjustment** → tune prompts, empathy overlays, Proof‑of‑Clarity thresholds, and question weighting.
5. **Feedback Decay** → apply time‑decay to keep learning recent and adaptive.

---

## 3) Instrumentation — Events & Fields (dev‑ready)

All events are JSON objects sent to the analytics stream and persisted to DilemmaNet. Use **draft‑07** for schemas and include `$schema` and `$id`.

### Common Envelope (attached to every event)

```json
{
  "$schema": "https://owlume/schemas/events/common_envelope.schema.json",
  "event_id": "uuid",
  "event_type": "string",
  "timestamp": "ISO-8601",
  "user_id": "opaque-id",
  "session_id": "uuid",
  "app_version": "semver",
  "client": { "platform": "web|ios|android|cli", "locale": "en-AU" },
  "privacy": { "pseudonymous": true, "consent": "standard|research" }
}
```

### Event: `session_start`

```json
{
  "$schema": "https://owlume/schemas/events/session_start.schema.json",
  "event_type": "session_start",
  "channel": "nudge|direct|import",
  "mode": "text|voice|paste",
  "pre_self_rating": { "clarity": 0.0, "confidence": 0.0 },
  "context": { "topic_hint": "string", "urgency": "low|med|high" }
}
```

### Event: `decision_captured`

```json
{
  "$schema": "https://owlume/schemas/events/decision_captured.schema.json",
  "event_type": "decision_captured",
  "dilemma": {"did": "DID-...", "summary": "short"},
  "tags": {
    "mode_id": "MID-...",
    "principle_id": "PID-...",
    "fallacy_ids": ["FID-..."],
    "context_driver_ids": ["CID-..."]
  }
}
```

### Event: `questions_shown`

```json
{
  "$schema": "https://owlume/schemas/events/questions_shown.schema.json",
  "event_type": "questions_shown",
  "qpack": [
    {"qid": "QID-...", "mid": "MID-...", "pid": "PID-...", "voice": "thiel|feynman|peterson|neutral"}
  ],
  "empathy": {"active": true, "tone": "gentle|direct|clinical"}
}
```

### Event: `proof_feedback_shown`

```json
{
  "$schema": "https://owlume/schemas/events/proof_feedback_shown.schema.json",
  "event_type": "proof_feedback_shown",
  "artifact": "reframe|decision_criteria|next_step",
  "post_self_rating": { "clarity": 0.0, "confidence": 0.0 }
}
```

### Event: `followup_scheduled`

```json
{
  "$schema": "https://owlume/schemas/events/followup_scheduled.schema.json",
  "event_type": "followup_scheduled",
  "when": "ISO-8601",
  "trigger": "time|calendar|decision_point"
}
```

### Event: `followup_completed`

```json
{
  "$schema": "https://owlume/schemas/events/followup_completed.schema.json",
  "event_type": "followup_completed",
  "outcome": "progress|stalled|abandoned",
  "notes": "string"
}
```

> **Note:** All IDs (DID/MID/PID/FID/CID/QID) must align with the validated JSON packs in `/data/` and `/schemas/` (draft‑07). Add `$schema` pointers at the top of each dataset.

---

## 4) Metrics & Formulas

### 4.1 Clarity Gain (CG)

`CG = w1 * Δclarity + w2 * Δconfidence + w3 * linguistic_delta + w4 * behavioral_depth`

* `Δclarity = post_self_rating.clarity − pre_self_rating.clarity`
* `Δconfidence = post_self_rating.confidence − pre_self_rating.confidence`
* `linguistic_delta` = score from NLP comparison (ambiguity ↓, concreteness ↑, assumption markers ↓)
* `behavioral_depth` = depth of engagement (questions expanded, edits made, follow‑up scheduled)
* Default weights (v0.1): `w = [0.4, 0.2, 0.25, 0.15]` (tunable)

**Session CG** = bounded to [−1.0, +1.0].

### 4.2 Nudge Accept Rate (NAR)

`NAR = accepted_nudges / nudges_sent`

### 4.3 Decision Check Rate (DCR)

`DCR = sessions_per_user_per_week`

### 4.4 Time‑to‑Question (TTQ)

`TTQ = t(first_question) − t(session_start)` (target < 10s)

### 4.5 Proof‑of‑Clarity Shown (PCS)

`PCS = proof_feedback_shown_sessions / total_sessions` (throttle to ~40%)

### 4.6 Feedback Decay (Half‑life ~14d)

```
weight_t = weight_0 * 0.5 ** (days_elapsed / 14)
```

Apply to question weights, empathy thresholds, and priors.

---

## 5) Adaptive Policies (v0.1)

* **Empathy Activation:** Enable when `CG < 0.1` *and* sentiment ⇒ tense/avoidant; switch tone to gentle.
* **Question Re‑weighting:** Promote questions with top‑quartile `CG` and demote bottom‑quartile after decay.
* **Thresholds:** If `PCS < 25%` *and* average `CG` rising → raise Proof‑of‑Clarity trigger; else lower slightly.
* **Conflict Handling:** If semantic Mode vs prior (fallacy/context) disagree and confidence in [0.35, 0.75] → carry top‑2 Modes forward (no forced choice).

---

## 6) Dashboards — "Pulse of Clarity"

* **Live tiles:** CG rolling median (7d/28d), NAR, DCR, TTQ, PCS.
* **Breakdowns:** By Mode, Principle, empathy tone, voice overlay.
* **Drill‑downs:** Top gaining questions (QID), laggard questions, new fallacy/context clusters.
* **Ops alerts:** Sudden CG drop (>20% week‑over‑week), TTQ regression, empathy over‑activation (>70%).

---

## 7) Privacy, Safety, Ethics

* Pseudonymous user IDs by default; explicit consent gate for research.
* Store only minimal text spans required for scoring; redact names/orgs.
* Rate‑limit adaptive changes; human review path for policy shifts.
* Keep a **model card** for Elenx adaptations (what changed, why, evidence).

---

## 8) Rollout Plan (MVP → v0.2)

* **MVP:** Implement `session_start`, `decision_captured`, `questions_shown`, `proof_feedback_shown`; compute CG with self‑ratings only; basic decay.
* **v0.2:** Add linguistic_delta & behavioral_depth, empathy gating, and top‑2 Mode carry‑forward; ship dashboard v1.
* **v0.3:** A/B test Proof‑of‑Clarity thresholds; add cohort‑level priors and per‑topic decay tuning.

---

## 9) Acceptance Criteria (MVP)

* Event schemas validate (draft‑07) with 0 errors in VS Code.
* Dashboard shows CG, NAR, DCR, TTQ within 24h of first sessions.
* ≥85% of sessions produce 3–7 mapped questions; 0 advice.
* Median CG ≥ +0.15 in week 2; TTQ ≤ 10s 95th percentile.

---

## Appendix A — Sample Event Flow (abridged)

```json
[
  {"event_type": "session_start", "pre_self_rating": {"clarity": 0.2, "confidence": 0.3}},
  {"event_type": "decision_captured", "dilemma": {"did": "DID-1042"}, "tags": {"mode_id": "MID-AskAssumptions", "principle_id": "PID-Evidence", "fallacy_ids": ["FID-appealToAuthority"], "context_driver_ids": ["CID-incentiveMismatch"]}},
  {"event_type": "questions_shown", "qpack": [{"qid": "QID-3321", "mid": "MID-AskAssumptions", "pid": "PID-Evidence", "voice": "feynman"}], "empathy": {"active": true, "tone": "gentle"}},
  {"event_type": "proof_feedback_shown", "post_self_rating": {"clarity": 0.55, "confidence": 0.6}}
]
```

**Computed:** `Δclarity=+0.35`, `Δconfidence=+0.30` → `CG ≈ 0.4*0.35 + 0.2*0.30 + ...`

---

*This document is designed to live alongside `/docs/owlume_gpt_monetization_blueprint.md`, the JSON packs in `/data/`, and their schemas in `/schemas/`. Treat it as the implementation contract for Owlume’s adaptive learning loop.*

───────────────────────────────────────────────
🦉  END OF DOCUMENT — ILLUMINATE, DON’T ASSUME
───────────────────────────────────────────────
