# Owlume — Instrumented Vibe Coding (IVC)

> “Build fast with intuition. Anchor it with evidence.”

---

## 1. Concept
Traditional *vibe coding* = high-context, conversational creation of code.  
It delivers velocity but hides assumptions.

**Instrumented Vibe Coding (IVC)** is Owlume’s evolved practice:
> AI-assisted creativity + human intent → immediately wrapped in validation, provenance, and documentation.

IVC keeps the *flow* of co-building with AI while ensuring every line can be traced, tested, and reasoned about.

---

## 2. Why It Exists
Owlume’s engine grew through natural conversation between Brian and Ted — rapid idea → code loops.  
Stage 4 introduces more contributors and learning automation, so hidden logic or silent drift must be exposed.

IVC is how we protect Owlume’s clarity from opacity.

---

## 3. Core Principles

| Principle | Practice | Benefit |
|------------|-----------|----------|
| **Provenance** | Tag AI-generated commits: `feat(Tx-Sy): [AI-gen by Ted]`. | Makes authorship and accountability visible. |
| **Validation First** | Every new JSON/data file must bind to a schema and pass the validator. | Prevents quiet data corruption. |
| **Runtime Proof** | Each script gets a smoke test showing one successful run. | Converts assumption → evidence. |
| **Reason Memory** | Add a 1-page ADR (`/docs/adr/`) for any architectural or threshold decision. | Captures *why*, not just *what*. |
| **Trace Logs** | Log `source`, `timestamp`, and `commit_id` in script headers or metadata. | Enables forensic debugging. |
| **Peer Glance** | Every major file reviewed or reread by a second human. | Breaks the cognitive echo-chamber. |
| **CI Enforcement** | Lint + schema + smoke tests run automatically on push (Stage 4 L2). | Makes discipline effortless. |

---

## 4. Workflow Snapshot

IDEA → AI-draft (Ted) → Human review → Schema validate →
Smoke test → Commit + tag → ADR note → CI check


If any link fails, fix before merge.  
If all pass, the vibe becomes verified code.

---

## 5. Advantages

1. **Keeps creativity fast** — no heavy spec writing needed.  
2. **Adds scientific traceability** — every assumption is observable.  
3. **Enables safe collaboration** — new devs know what was AI-authored and why.  
4. **Feeds DilemmaNet’s meta-learning** — logs reveal which code decisions improved clarity gain.

---

## 6. Relation to Clarity-Driven Engineering

CDE measures *clarity gained* from user reflections.  
IVC measures *clarity retained* inside the codebase.

Together they form Owlume’s dual discipline:
> **CDE = what we build for users.**  
> **IVC = how we build it ourselves.**

---

## 7. Next Steps

- Add an ADR template (`docs/adr/adr_template.md`).  
- Expand CI (Stage 4 L2) to check provenance tags and schema validation.  
- Tag all pre-existing Stage 3 scripts with `# Source: AI-gen (Ted)` headers retroactively.

---

**Summary**

Owlume builds clarity systems — our process must embody clarity too.  
Instrumented Vibe Coding keeps intuition alive but grounds it in proof.

> “Vibe fast. Validate faster.”
