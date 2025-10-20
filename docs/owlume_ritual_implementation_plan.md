# 🦉 Owlume Ritual Implementation Plan (v1.0)

## Purpose
To make “checking blind spots with Owlume” a **daily ritual**, combining gentle rhythm and contextual intelligence.  
Goal: 1 minute × Reflection × Reward = Repeat.

---

## 1. System Layer — Scheduling & Triggering

### A. Gentle Daily Nudge
**Objective:** Build user consistency through a predictable daily cue.

- **Trigger:** Once per day (default 9am local time)
- **Message:** “Your daily clarity check is ready.”
- **User options:** Start Now / Snooze / Skip
- **Implementation (MVP):**
  - Use OpenAI automation scheduling (`automations.create`) for daily notifications.
- **Future Elenx Integration:**
  - Sync with Google Calendar or Notion Tasks.
  - Mobile push notifications when Owlume app is live.

### B. Moment-Based Prompt
**Objective:** Catch reflection opportunities when users are about to act.

#### 1. Manual trigger
- Detect key phrases such as “before my meeting,” “about to send,” or “I’m deciding.”
- Respond contextually:
  > “Looks like you’re about to make a choice. Want to illuminate blind spots first?”

#### 2. Calendar integration (Phase 2)
- Integrate with Google Calendar.
- Trigger micro-prompts 5 minutes before high-stakes events.
  > “Before your strategy meeting, what’s one blind spot you might be missing?”

#### 3. Browser / Workspace integration (Phase 3)
- Lightweight Owlume icon pulse when user edits decision-heavy docs or emails.

---

## 2. Content Layer — Prompt Logic & Voice

| Trigger Type | Prompt Template | Tone |
|---------------|----------------|------|
| **Daily Nudge** | “Illuminate one assumption before you start your day.” | Calm, reflective |
| **Pre-Meeting Prompt** | “Before your next meeting, what’s one blind spot you might be missing?” | Professional, empathetic |
| **Pre-Decision** | “You’re about to make a choice. What could you be overlooking?” | Neutral, precise |
| **Post-Event Reflection** | “Something didn’t go as planned? Let’s find the blind spot behind it.” | Supportive, guiding |

**Voice Guidelines:**
- Always **sharp, human, calm, and confident**.
- Avoid chatty filler or over-coaching.
- Use verbs aligned with Owlume philosophy: *illuminate, reveal, spot, clarify, cost*.

---

## 3. UX Layer — Experience & Feedback Loop

| Phase | User Action | Owlume Response | Outcome |
|--------|--------------|----------------|----------|
| **Trigger moment** | User clicks nudge or receives prompt | 1 reflection text field appears | Low barrier to start |
| **Input** | User writes short entry (1–2 sentences) | Owlume returns 3–5 blind-spot questions | Instant clarity |
| **Close** | User clicks *Done for now* | Owlume offers micro-summary: “You spotted what most miss — clarity gained.” | Emotional payoff |
| **Feedback** | Optional 👍 / 👎 or Save Insight | Logged to DilemmaNet | Continuous personalization |

---

## 4. Operational Timeline

| Phase | Focus | Scope |
|--------|--------|--------|
| **MVP (GPT App)** | Static daily nudge + manual prompts | Use OpenAI automation scheduler |
| **Phase 2 (Elenx Integration)** | Calendar & event-based triggers | Google Calendar API + DilemmaNet context logging |
| **Phase 3 (Full Ritual System)** | Adaptive nudges + empathy-aware timing | Elenx analyzes text tone/fatigue to adjust prompts |

---

## 5. Outcome

By pairing **predictable rhythm** (daily nudge) with **contextual precision** (moment-based prompt), Owlume becomes more than an AI — it becomes a **clarity ritual**.

> “A day without reflection risks a blind spot that costs you.”
