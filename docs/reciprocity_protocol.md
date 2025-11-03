# 🔄 Owlume Reciprocity Protocol — v0.1  
**Stage:** 7 · S7-S2 — Partner & Surface Protocols  
**Date:** 2025-11-03  

---

## 🎯 Purpose  
Define how external systems that use Owlume insights return learning signals back into DilemmaNet and BSE safely.  
It ensures clarity travels both ways — feedback strengthens the core engine rather than just consume it.

---

## ⚖️ Principles  

1. **Minimal Exposure** — only clarity signals, never raw text.  
2. **Reciprocal Learning** — external systems must return usage telemetry (CG changes, response depth).  
3. **Consent by Context** — data flows only within agreed scope (session, team, or platform).  
4. **Time-Bound Memory** — partner logs auto-expire after 14 days unless extended by user choice.  
5. **Audit Trail Parity** — each exchange gets a unique `reciprocity_id` traceable in both systems.

---

## 🧩 Data Exchange Format  

### Outbound (from Owlume → Partner)
```json
{
  "reciprocity_id": "RCP-2025-0001",
  "bse_vector": {...},
  "cg_delta": 0.15,
  "mode": "Analytical",
  "principle": "Assumption",
  "timestamp": "2025-11-03T03:21:00Z"
}

# Owlume Reciprocity Protocol (v0.1)

**Purpose.** Define a simple, safe loop for *two-way clarity transfer*:  
Partner → (reflection) → **Owlume** → (questions, vectors) → Partner → (outcomes/feedback) → **DilemmaNet**.

---

## 1) Transport & Auth

- **Transport:** HTTPS POST with `Content-Type: application/json; charset=utf-8`.
- **Auth:** Partner-signed JWT in `Authorization: Bearer <token>`. JWT must include `partner_id`, `iat`, `exp`, and `scope`.
- **Clock tolerance:** ±300s.

---

## 2) Message Contract

Both directions use the **SDK Stub Envelope** defined in `/schemas/owlume_sdk_stub.schema.json`.

- **Request (partner → Owlume):** envelope with `input` present.
- **Response (Owlume → partner):** envelope with `output` present.
- **Reciprocity:** Partner may later POST *learning* using the same `reciprocity_id`.

Minimum required fields:
- Request: `spec.version`, `trust.consent.*`, `input.reciprocity_id`, `input.timestamp`, `input.text`
- Response: `output.reciprocity_id`, `output.did`, `mode`, `principle`, `confidence`, `questions[]`, `vectors.bias_vector.*`

---

## 3) Trust Layer

- **Consent:** Partner asserts user consent via `trust.consent` (terms version, scope, token). Owlume validates + logs.
- **Anonymization:** If `trust.anonymization.enabled=true`, partner must send hashed user alias (`input.user_hint`). Owlume **never** requests de-anonymization.
- **Audit:** `trust.audit.log_level`:
  - `off` – no logs written (only counters)
  - `errors` – failures only
  - `summary` – request/response metadata + metric deltas (default)
  - `full` – includes model picks and vectors (PII already stripped)

---

## 4) Return Learning → DilemmaNet

Partners may send:
- **Outcome:** `{ "outcome": "IMPROVED_DECISION" | "STATUS_QUO" | "DEFERRED" }`
- **User feedback:** `{ "helpfulness": 1..5, "comment": "..." }`
- **Ground truth tag (optional):** `{ "label": "Hired" | "Not Hired" | ... }` (HR mode)
- **Clarity deltas:** If partner measures their own pre/post clarity, include `{ "cg_pre_ext": 0..1, "cg_post_ext": 0..1 }`.

**Endpoint suggestion (partner → Owlume):**
POST /reciprocity/learning
Authorization: Bearer <jwt>

{
"$schema": "https://owlume/schemas/owlume_sdk_stub.schema.json
",
"spec": { "version": "v0.1", "channel": "sdk-stub", "partner_id": "acme-hr" },
"trust": { "...": "..." },
"output": {
"reciprocity_id": "RCP-00123",
"did": "DID-7d3a2b",
"learning": {
"outcome": "IMPROVED_DECISION",
"helpfulness": 5,
"comment": "The alternatives question unblocked us.",
"label": "Hired",
"cg_pre_ext": 0.40,
"cg_post_ext": 0.75
}
}
}


**DilemmaNet ingestion:**
- Deduplicates by `reciprocity_id`.
- Writes event(s) to `data/logs/reciprocity_events.jsonl`.
- Updates aggregates and BSE EMA for the user alias.

---

## 5) Status & Errors

- `202 Accepted` — queued; response JSON contains `log_ref`
- `200 OK` — synchronous response with `output`
- `400 Bad Request` — schema violation; returns `errors[]`
- `401/403` — auth failure / scope mismatch
- `409 Conflict` — duplicate `reciprocity_id` with incompatible contents
- `429 Too Many Requests` — backoff header `Retry-After: s`
- `5xx` — transient; retry with jitter (100–800ms)

---

## 6) Sequence (ASCII)

Partner Owlume
| (input) request |
|--------------------------->| validate → anonymize → Elenx → vectors
| |
| (output) response |
|<---------------------------| questions, vectors, audit ref
| |
| (learning) POST |
|--------------------------->| DilemmaNet ingest → BSE EMA → dashboard
| |
| 202 Accepted + log_ref |
|<---------------------------|


---

## 7) Security & Privacy Notes

- Never transmit raw PII; use hashed aliases if partner needs user-level learning.
- Partners remain controllers of consent; Owlume is a processor within declared scope.
- Provide a `terms_version` bump path; mismatches return `412 Precondition Failed`.

---

