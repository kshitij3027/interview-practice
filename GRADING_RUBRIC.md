# Grading Rubric — 100 points

## 1. Functional correctness — 20 points
- **18–20:** The complete create → pending → accept/reject workflow works end-to-end, accepted swaps update both shifts correctly, and normal/stale/retry paths are usable from the UI.
- **13–17:** Core workflow works but one meaningful lifecycle or recovery case is incomplete.
- **7–12:** A narrow happy path works, but atomicity, lifecycle, or reconciliation has significant holes.
- **0–6:** The feature is largely non-functional.

## 2. Backend/domain behavior — 22 points
Evaluate qualification rules, overlap/rest validation on the *resulting* schedule, captured revisions, expiration, request lifecycle, atomic dual-shift mutation, exact revision accounting, and idempotency semantics.

- **19–22:** Domain behavior is explicit, deterministic, and safe across lifecycle transitions and retries.
- **14–18:** Mostly correct with one material domain gap.
- **7–13:** Endpoint-heavy implementation with fragile or incomplete invariants.
- **0–6:** Unsafe or fundamentally incorrect swap semantics.

## 3. Frontend behavior — 14 points
Evaluate request creation/selection, request list/status rendering, accept/reject controls, in-flight isolation, preservation of filter/selection, stale recovery, and actionable errors without full-page reloads.

## 4. Integration / API contract — 10 points
Evaluate whether client and server agree on request identity, revisions, lifecycle outcomes, current-state conflict payloads, idempotency keys, and post-success reconciliation.

## 5. Edge cases & safety — 18 points
High-value evaluator themes include:
- same shift or same assignee;
- two active requests sharing one shift;
- qualification failure on either destination;
- overlap checks that accidentally include the two old assignments;
- rest gaps just below, exactly at, and just above 8 hours;
- stale global revision caused by an intervening manual reassignment;
- no partial swap when the second side would fail;
- request expiration before acceptance;
- create idempotency for A/B versus B/A;
- acceptance retry after success without swapping back;
- request-key reuse with different logical input.

A happy-path-only implementation should receive **no more than 8/18** here.

## 6. Tests — 8 points
- **7–8:** Focused tests cover resulting-schedule validation plus at least two high-risk stale/idempotency/expiry cases.
- **5–6:** Useful feature tests beyond the happy path.
- **2–4:** Limited or mostly superficial tests.
- **0–1:** No meaningful feature tests.

## 7. Code quality — 4 points
Reasonable decomposition, naming, mutation boundaries, consistency with the starter architecture, and minimal accidental complexity.

## 8. Verification / debugging — 4 points
Evidence that the candidate ran baseline tests/build, exercised the end-to-end flow, and checked at least one failure or stale/retry scenario rather than trusting generated code.

## Overall calibration
- **90–100 — Excellent:** robust semantics, strong prioritization, and clear verification under hidden cases.
- **75–89 — Strong / acceptable:** core implementation is correct with a few edge-case or UI gaps.
- **60–74 — Partial:** useful end-to-end progress, but meaningful safety or lifecycle holes remain.
- **Below 60 — Failing / incomplete:** happy path only, unsafe mutation semantics, or feature not credibly integrated.

A polished implementation that merely creates a request and performs two ordinary reassignments, without atomicity, resulting-schedule validation, stale protection, expiry, and retry safety, should **not exceed roughly 60–65 points**.
