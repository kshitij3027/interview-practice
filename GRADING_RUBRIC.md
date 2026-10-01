# Grading Rubric — 100 points

Happy-path-only work that ignores overlap semantics, stale revisions, or retries should not score above roughly **60–65**.

## 1. Functional correctness — 20
End-to-end schedule load, evaluate, create, cancel, and UI reconciliation.

## 2. Backend/domain behavior — 18
Fixture validation/loading, normalized instant handling, effective-playlist selection, server-generated IDs, mutation boundaries, and exact revision accounting.

## 3. Edge cases and correctness — 20
Exact start inclusion/end exclusion; offset-equivalent timestamps; all four tie-break levels; cancelled-window exclusion; offline-screen create rejection; duration/text boundaries; stale create/cancel; already-cancelled no-op; CSV row-order independence.

## 4. Frontend behavior — 12
Schedule rendering, forms, evaluation display, in-flight controls, preserving failed input, stale/error recovery, post-mutation reconciliation, and protection from obsolete async responses.

## 5. Integration/API contract — 10
Stable client/server shapes, backend authority for winners and mutations, and clean integration with existing screen/detail/revision flows.

## 6. Retry/idempotency semantics — 8
Normalized logical payload identity, offset-equivalent timestamp handling, original-result replay, conflicting key reuse rejection, and zero duplicate revision increments.

## 7. Tests — 7
Focused tests for overlap precedence plus at least two of: exact boundaries, offset equivalence, stale mutation, request-key replay/conflict, cancelled window, no-op cancel, or frontend races.

## 8. Code quality — 3
Clear naming/decomposition and consistency with the starter without a framework rewrite.

## 9. Verification/debugging discipline — 2
Evidence the candidate ran the baseline and exercised ordinary plus failure/race cases.

## Calibration
- 90–100: excellent and robust.
- 75–89: strong with limited gaps.
- 60–74: substantial partial solution with important holes.
- Below 60: incomplete/brittle or mostly happy-path.
