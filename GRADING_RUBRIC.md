# Grading Rubric — 100 points

A polished happy path that ignores ordering, idempotency, stale-state safety, or per-stream partial failure should not score above roughly **60–65**.

## 1. Functional correctness — 20 points
- 18–20: complete replay flow works end to end, including filtering, per-delivery results, retry progression, and state reconciliation.
- 12–17: main flow works with one meaningful semantic gap.
- 6–11: narrow happy path only.
- 0–5: largely incomplete or non-functional.

## 2. Backend/domain behavior — 18 points
Evaluate server-owned candidate selection, replay execution, state mutation boundaries, request validation, revision accounting, and response shape. Full credit requires clear separation between request parsing and replay semantics and no trust in client-authored candidate lists.

## 3. Frontend behavior — 12 points
Evaluate replay controls, readable partial results, preservation of last-known-good data on errors, correct post-replay counts/detail, duplicate-submit prevention, and protection from obsolete responses after endpoint/filter changes.

## 4. Integration/API contract — 10 points
Evaluate whether browser and server agree on normalized inputs, structured per-delivery outcomes, current revisions, idempotent retry responses, and conflict/error handling.

## 5. Edge cases and safety — 22 points
High-weight checks include row-order independence, stream ordering, maxEvents after ordering, stream-local blocking, retry_once progression, permanent failures, zero-candidate no-op, stale delayed replay, paused endpoint rejection, same-key retry, key reuse with changed payload, and exact one-time revision increments. Happy-path-only work should receive fewer than 10 points here.

## 6. Tests — 10 points
- 9–10: focused tests cover normal replay plus several high-risk failure/race/idempotency cases.
- 6–8: meaningful domain/API tests beyond the happy path.
- 3–5: limited or superficial tests.
- 0–2: no useful feature tests.

## 7. Code quality — 5 points
Clarity, naming, decomposition, consistency with the starter architecture, and avoidance of unnecessary infrastructure.

## 8. Verification/debugging discipline — 3 points
Evidence that the candidate ran the starter tests/build, exercised the feature, and inspected failure paths rather than relying only on generated code.

## Overall calibration
- **90–100 Excellent:** robust semantics, sensible prioritization, strong explanation.
- **75–89 Strong:** feature mostly correct with a few contained gaps.
- **60–74 Partial:** substantial progress but important correctness/safety holes.
- **Below 60:** happy-path-only, brittle, or incomplete.
