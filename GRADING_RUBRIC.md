# Grading Rubric — 100 points

## 1. Functional correctness — 18 points
- 16–18: Create and toggle flows work end-to-end, reconcile visible state correctly, preserve existing severity behavior, and remain usable under delayed responses and failures.
- 11–15: Core flows work with one meaningful correctness gap.
- 6–10: Happy path works but retries, conflicts, filters, or reconciliation are materially incomplete.
- 0–5: Feature is largely non-functional.

## 2. Backend/domain behavior — 20 points
Evaluate create validation/normalization, permanent ID assignment, request-key idempotency, request-key payload mismatch detection, per-action revision checks, incident/global revision increments, stale rejection without mutation, deterministic action ordering, and bounded delay handling.

Excellent work keeps these rules in testable domain/service boundaries rather than scattering correctness across route handlers. Partial work usually has working endpoints but fragile mutation semantics. Failing work duplicates creates, mutates on stale requests, or corrupts revision accounting.

## 3. Frontend behavior — 20 points
Evaluate optimistic create rendering, temporary-to-server identity reconciliation, optimistic toggle/rollback, per-row in-flight state, retry UX, draft preservation, action-status filtering/search, preservation of incident/severity selection, and keeping last known-good data visible on failures.

A strong UI behaves correctly when optimistic rows enter/leave filters and when the selected incident changes before a response returns.

## 4. Integration / client-server contract — 12 points
Evaluate whether shared contracts and API shapes clearly support idempotency, stale reconciliation, current revisions, and server-assigned identity. The browser must not invent permanent server truth or rely on a full reload as its primary reconciliation mechanism.

## 5. Edge cases and race safety — 16 points
High-value evaluator checks include:
- summary consisting only of whitespace;
- owner not present in incident responders;
- due date before incident start;
- retrying the same successful create request key;
- reusing a request key with a different normalized payload;
- stale action revision with no mutation;
- toggling an item while another row is mutating;
- an optimistic open→done row disappearing under an `open` filter and reappearing after stale failure;
- switching incidents while a delayed create or toggle response is pending;
- delayed responses finishing after newer list/detail loads;
- correct open-action count and revision reconciliation after mutations;
- deterministic ordering with equal priority/due dates and null due dates.

## 6. Tests — 7 points
- 6–7: Focused automated tests cover idempotent create plus at least two of stale mutation, validation, revision accounting, deterministic ordering, or delayed/race-sensitive behavior.
- 4–5: Meaningful backend/domain tests beyond happy path.
- 2–3: Limited tests with weak edge-case coverage.
- 0–1: No useful feature tests.

## 7. Code quality — 4 points
Clarity, naming, decomposition, minimal accidental complexity, consistency with existing architecture, and avoidance of a wholesale rewrite.

## 8. Verification/debugging — 3 points
Evidence that the candidate ran the existing build/tests, exercised the UI, and deliberately tested at least one delayed/conflict/retry path.

## Overall calibration
- **90–100 — Excellent:** robust semantics and client reconciliation, strong prioritization, focused verification.
- **75–89 — Good/acceptable:** core feature is solid with a few edge-case or polish gaps.
- **60–74 — Partial:** substantial implementation, but at least one major retry/concurrency/reconciliation dimension is weak.
- **Below 60 — Failing/incomplete:** happy-path-only, brittle, or materially broken integration.

A solution that only adds synchronous create/toggle buttons and refreshes the page afterward should **not exceed roughly 60–65 points**, even if the ordinary happy path looks polished.
