# 🦉 Owlume — Frequency Metrics Specification (v1.0)

## Purpose
To provide a unified measurement framework for user frequency, engagement, and reflection quality inside Owlume.  
These metrics guide growth experiments, track habit strength, and feed back into DilemmaNet and Elenx for adaptive tuning.

---

## 1. Overview

**North Star Metric:**  
`WRU (Weekly Reflecting Users)` — percentage of active users who complete at least one reflection per week.

Supporting KPIs track behavior from **trigger → reflection → return** across both *daily nudges* and *moment-based prompts.*

---

## 2. Core Metrics Table

| Metric | Definition | Formula / Event Source | Objective |
|---------|-------------|------------------------|------------|
| **WRU (Weekly Reflecting Users)** | % of active users completing ≥1 reflection in a 7-day window | `unique(session_end)` / `unique(active_users)` | Retention & ritual adoption |
| **NAR (Nudge Accept Rate)** | % of nudges that lead to reflection sessions | `nudge_accepted` / `nudge_sent` | Measures prompt relevance |
| **DCR (Decision Check Rate)** | Average reflections per user per week | `count(session_end)` / `unique(users)` | Usage depth |
| **TTQ (Time-to-Question)** | Median seconds from app open to first blind-spot question shown | `timestamp(questions_shown)` − `timestamp(session_start)` | Detects friction |
| **MMR (Moment Match Rate)** | % of moment prompts triggered within 10 min of a real event (meeting, message, doc edit) | `nudge_timestamp` vs `event_timestamp` | Context precision |
| **R48 (Return ≤ 48 h)** | % of users returning within 48 h after any session | `session_start` (t < 48 h since last `session_end`) | Short-term stickiness |
| **PCS (Proof-of-Clarity Shown)** | % of sessions that display reinforcement feedback | `proof_feedback_shown` / `session_end` | Feedback cadence health |

---

## 3. Event Schema (Canonical Logging)

All events should include:  
`user_id`, `session_id`, `timestamp`, `trigger_type` (daily / moment / manual).

| Event | When Fired | Key Properties |
|--------|-------------|----------------|
| `session_start` | User begins reflection | `entry_point`, `trigger_type` |
| `decision_captured` | User inputs text | `word_count`, `category_detected` |
| `questions_shown` | Blind-spot questions displayed | `mode_detected`, `principle_detected` |
| `proof_feedback_shown` | Reinforcement line delivered | `feedback_type` (rarity / depth / empathy / consistency) |
| `session_end` | User exits reflection | `duration`, `responses_viewed` |
| `nudge_sent` | Daily or moment prompt issued | `nudge_type`, `context_tag` |
| `nudge_accepted` | User clicks prompt | `response_time` |
| `snoozed` | User postpones prompt | `delay_minutes` |
| `declined` | User dismisses prompt | – |
| `followup_scheduled` | User opts for future reminder | `followup_delay_hours` |
| `followup_completed` | User opens follow-up session | – |

---

## 4. Data Flow — From App → DilemmaNet → Elenx

1. **App Layer:** Emits raw events with metadata (decision category, empathy toggle, etc.).  
2. **DilemmaNet Layer:** Aggregates anonymized statistics for cohort comparisons (e.g., average rarity percentiles, reflection depth).  
3. **Elenx Engine:** Uses aggregated frequency and engagement data to adapt trigger timing and content relevance.  
   - High `TTQ` → simplify UX.  
   - Low `NAR` → adjust nudge phrasing/time.  
   - Declining `WRU` → activate re-engagement scripts.

---

## 5. Benchmarks & Targets (MVP)

| Metric | Target | Health Indicator |
|---------|---------|------------------|
| **WRU** | ≥ 55 % | Core habit forming |
| **NAR** | ≥ 40 % | Nudges are well-timed |
| **DCR** | 2.0–3.0 / week | Sustainable use |
| **TTQ** | ≤ 10 s | Low friction |
| **MMR** | ≥ 60 % | Good contextual accuracy |
| **R48** | ≥ 35 % | Returning engagement |
| **PCS** | ~33 % | Balanced reinforcement |

---

## 6. Visualization Dashboard (for analytics team)

Suggested panels:
1. **Frequency Heatmap:** sessions/day/user.
2. **Conversion Funnel:** nudge → accept → reflection → return.
3. **TTQ Distribution:** friction curve.
4. **Reflection Depth Histogram:** from Elenx semantic scoring.
5. **Clarity Feedback Coverage:** proportion of Proof-of-Clarity messages delivered.
6. **R48 Cohort Trend:** retention by week.

---

## 7. Data Hygiene & Privacy

- Log only anonymized, non-content metadata to DilemmaNet.  
- Full reflection text remains private to user.  
- Aggregate statistics only used for percentile feedback (“82 % of users overlook …”).  
- GDPR/CCPA compliant retention window: 30 days for raw events, 12 months for aggregated metrics.

---

## 8. Reporting Cadence

| Report | Frequency | Audience |
|---------|------------|-----------|
| **Weekly Growth Snapshot** | Every Monday | Product & Growth |
| **Monthly Retention Review** | 1st of month | Leadership |
| **Quarterly Learning Loop Report** | Quarterly | Strategy + Investors |

---

## 9. Success Definition

> Owlume reaches sustainable frequency when:  
> - 55 %+ of users reflect weekly,  
> - 40 %+ accept nudges,  
> - Average session < 60 s,  
> - Proof-of-Clarity feedback shown in 1 of 3 sessions,  
> resulting in continuous data enrichment for DilemmaNet and reduced churn.

---

## 10. Next Steps

1. Implement unified event schema in GPT and Elenx builds.  
2. Connect metrics to internal dashboard (Superset / Metabase).  
3. Automate weekly reports with WRU, NAR, TTQ, and R48 trends.  
4. Use insights to tune ritual cadence and nudge timing adaptively.

---

*Maintainer:* Product Analytics Lead  
*Spec version:* `2025-10-11`
