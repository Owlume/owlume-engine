Diff Appendix — What Became Untouchable at Stage 15

Exact Freeze Surface (Authoritative Reference)

Purpose
This appendix enumerates—precisely and exhaustively—the artifacts that became non-modifiable at Stage 15. It exists to remove ambiguity for reviewers, contributors, and future maintainers about what is irreversibly locked versus what remains evolvable.

This is a descriptive index, not a policy source. Authority remains in the frozen artifacts themselves.

1. Freeze Scope Summary (One Glance)

After Stage 15, no changes are permitted to:

Action gating logic

BLOCK prohibitions

Governance schemas enforcing action limits

Tests that assert those limits

The tags anchoring these freezes

Any modification to the items listed below constitutes a governance violation, not a refactor.

2. Immutable Artifacts (By Category)
A. Action Gating (Runtime Law)

Status: Frozen
Rationale: Determines whether any action may proceed.

/src/action_gating.py


Contains deterministic decision logic

No probabilistic paths

No learning hooks

No configuration-based overrides

Explicitly prohibited changes:

Adding new branches

Introducing confidence thresholds

Refactoring that alters control flow

Abstracting logic into tunable components

B. Action Gating Schema (Structural Law)

Status: Frozen
Rationale: Prevents construction of illegal action states.

/schemas/action_gating_table.schema.json


Declarative constraints only

Exhaustive enumeration of allowed states

Validated in CI

Explicitly prohibited changes:

Adding optional fields

Weakening required clauses

Expanding allowed enum values

Introducing conditional permissiveness

C. BLOCK Prohibitions (Negative Law)

Status: Frozen
Rationale: Defines actions that must never occur.

/schemas/block_negative_rules.schema.json


Enumerated “must-not” conditions

Evaluated prior to any action emission

Independent of model confidence or context

Explicitly prohibited changes:

Adding exceptions

Softening language (“should not” → “must not” is already fixed)

Introducing contextual bypasses

Making rules data-driven or learned

D. Governance Tests (Enforcement Proof)

Status: Frozen
Rationale: Ensure policy law is mechanically enforced.

/tests/test_stage14_action_gating_table.py
/tests/test_stage14_block_prohibitions.py


Tests assert failure for prohibited behavior

CI must fail if any frozen rule is violated

Explicitly prohibited changes:

Marking tests as xfail/skip

Weakening assertions

Reducing coverage

Rewriting expected failures as warnings

E. Freeze Anchors (Historical Law)

Status: Frozen
Rationale: Establish irreversible governance checkpoints.

git tag stage14-freeze
git tag stage15-precharter-green


Serve as audit and legal reference points

Define earliest permissible ancestor for any fork

Explicitly prohibited changes:

Moving tags

Re-tagging with different commits

Deleting or replacing tags

Rewriting history prior to these tags

3. What Remains Mutable (Explicit Non-Freeze)

To prevent overreach, the following are not frozen by Stage 15:

Analysis and perception logic

Reflection phrasing and UX presentation

Documentation explaining (but not redefining) governance

Telemetry, dashboards, and reporting layers

Constraint:
No mutable layer may cause, suggest, or imply behavior that violates frozen action law.

4. Change Classification Rule (Canonical)

Any proposed change after Stage 15 must answer:

“Does this alter what Owlume is allowed to do?”

Yes → Prohibited

No, it only alters how things are explained or observed → Permitted

There is no third category.

5. Reviewer Verification Checklist

An external reviewer can verify immutability by:

Checking the frozen tags exist and point to the declared commits

Inspecting listed schemas for strict prohibitions

Running governance tests and confirming failure on prohibited cases

Confirming CI rejects any mutation of these artifacts

No privileged access is required.

6. Canonical Statement (Appendix Scope)

After Stage 15, Owlume’s action boundaries are no longer part of development. They are part of history. (2026-01-17)