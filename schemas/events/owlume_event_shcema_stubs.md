# Owlume Event Schema Stubs (draft-07)

> Drop these into `/schemas/events/`. Each `$id` assumes the canonical path `https://owlume/schemas/events/...`. Validate in VS Code with JSON Schema draft‑07.

---

## 0) `common_envelope.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://owlume/schemas/events/common_envelope.schema.json",
  "title": "Common Envelope",
  "type": "object",
  "properties": {
    "event_id": {"type": "string"},
    "event_type": {"type": "string"},
    "timestamp": {"type": "string", "format": "date-time"},
    "user_id": {"type": "string"},
    "session_id": {"type": "string"},
    "app_version": {"type": "string"},
    "client": {
      "type": "object",
      "properties": {
        "platform": {"type": "string", "enum": ["web", "ios", "android", "cli"]},
        "locale": {"type": "string"}
      },
      "required": ["platform"],
      "additionalProperties": false
    },
    "privacy": {
      "type": "object",
      "properties": {
        "pseudonymous": {"type": "boolean"},
        "consent": {"type": "string", "enum": ["standard", "research"]}
      },
      "required": ["pseudonymous"],
      "additionalProperties": false
    }
  },
  "required": ["event_id", "event_type", "timestamp", "session_id"],
  "additionalProperties": true
}
```

---

## 1) `session_start.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://owlume/schemas/events/session_start.schema.json",
  "title": "Session Start",
  "allOf": [
    {"$ref": "https://owlume/schemas/events/common_envelope.schema.json"},
    {
      "type": "object",
      "properties": {
        "event_type": {"const": "session_start"},
        "channel": {"type": "string", "enum": ["nudge", "direct", "import"]},
        "mode": {"type": "string", "enum": ["text", "voice", "paste"]},
        "pre_self_rating": {
          "type": "object",
          "properties": {
            "clarity": {"type": "number", "minimum": 0, "maximum": 1},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
          },
          "required": ["clarity", "confidence"],
          "additionalProperties": false
        },
        "context": {
          "type": "object",
          "properties": {
            "topic_hint": {"type": "string"},
            "urgency": {"type": "string", "enum": ["low", "med", "high"]}
          },
          "additionalProperties": false
        }
      },
      "required": ["event_type", "channel", "mode", "pre_self_rating"]
    }
  ]
}
```

---

## 2) `decision_captured.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://owlume/schemas/events/decision_captured.schema.json",
  "title": "Decision Captured",
  "allOf": [
    {"$ref": "https://owlume/schemas/events/common_envelope.schema.json"},
    {
      "type": "object",
      "properties": {
        "event_type": {"const": "decision_captured"},
        "dilemma": {
          "type": "object",
          "properties": {
            "did": {"type": "string"},
            "summary": {"type": "string", "maxLength": 400}
          },
          "required": ["did"],
          "additionalProperties": false
        },
        "tags": {
          "type": "object",
          "properties": {
            "mode_id": {"type": "string"},
            "principle_id": {"type": "string"},
            "fallacy_ids": {"type": "array", "items": {"type": "string"}},
            "context_driver_ids": {"type": "array", "items": {"type": "string"}}
          },
          "required": ["mode_id", "principle_id"],
          "additionalProperties": false
        }
      },
      "required": ["event_type", "dilemma", "tags"]
    }
  ]
}
```

---

## 3) `questions_shown.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://owlume/schemas/events/questions_shown.schema.json",
  "title": "Questions Shown",
  "allOf": [
    {"$ref": "https://owlume/schemas/events/common_envelope.schema.json"},
    {
      "type": "object",
      "properties": {
        "event_type": {"const": "questions_shown"},
        "qpack": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "properties": {
              "qid": {"type": "string"},
              "mid": {"type": "string"},
              "pid": {"type": "string"},
              "voice": {"type": "string", "enum": ["thiel", "feynman", "peterson", "neutral"]}
            },
            "required": ["qid", "mid", "pid"],
            "additionalProperties": false
          }
        },
        "empathy": {
          "type": "object",
          "properties": {
            "active": {"type": "boolean"},
            "tone": {"type": "string", "enum": ["gentle", "direct", "clinical"]}
          },
          "required": ["active"],
          "additionalProperties": false
        }
      },
      "required": ["event_type", "qpack"]
    }
  ]
}
```

---

## 4) `proof_feedback_shown.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://owlume/schemas/events/proof_feedback_shown.schema.json",
  "title": "Proof of Clarity Shown",
  "allOf": [
    {"$ref": "https://owlume/schemas/events/common_envelope.schema.json"},
    {
      "type": "object",
      "properties": {
        "event_type": {"const": "proof_feedback_shown"},
        "artifact": {"type": "string", "enum": ["reframe", "decision_criteria", "next_step"]},
        "post_self_rating": {
          "type": "object",
          "properties": {
            "clarity": {"type": "number", "minimum": 0, "maximum": 1},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
          },
          "required": ["clarity", "confidence"],
          "additionalProperties": false
        }
      },
      "required": ["event_type", "artifact", "post_self_rating"]
    }
  ]
}
```

---

## 5) `followup_scheduled.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://owlume/schemas/events/followup_scheduled.schema.json",
  "title": "Follow-up Scheduled",
  "allOf": [
    {"$ref": "https://owlume/schemas/events/common_envelope.schema.json"},
    {
      "type": "object",
      "properties": {
        "event_type": {"const": "followup_scheduled"},
        "when": {"type": "string", "format": "date-time"},
        "trigger": {"type": "string", "enum": ["time", "calendar", "decision_point"]}
      },
      "required": ["event_type", "when", "trigger"]
    }
  ]
}
```

---

## 6) `followup_completed.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://owlume/schemas/events/followup_completed.schema.json",
  "title": "Follow-up Completed",
  "allOf": [
    {"$ref": "https://owlume/schemas/events/common_envelope.schema.json"},
    {
      "type": "object",
      "properties": {
        "event_type": {"const": "followup_completed"},
        "outcome": {"type": "string", "enum": ["progress", "stalled", "abandoned"]},
        "notes": {"type": "string", "maxLength": 600}
      },
      "required": ["event_type", "outcome"]
    }
  ]
}
```

---

### Integration Notes

* Keep `$id` paths in sync with the repo. If you serve schemas from a different domain/path, update `$id` and the `$ref` targets accordingly.
* Enforce `additionalProperties: false` only after initial telemetry hardening.
* Add unit tests: each event emitter should export a sample payload that passes validation in CI.
