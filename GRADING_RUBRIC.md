# Grading Rubric — 100 points

## Functional correctness — 20 points
- 8: A usable batch selector, preview flow, and apply flow work end to end.
- 5: Preview is non-mutating and clearly reports proposed per-case changes and diagnostics.
- 4: Apply updates visible receipt state and per-case outcomes without a full reload.
- 3: Existing manual-exception behavior remains usable alongside reconciliation.

## Backend / domain behavior — 22 points
- 5: Scan IDs are canonicalized deterministically, including exact duplicates and conflicting duplicate payloads.
- 5: Effective parcel events are selected with the required event-time / ingestion-time / ID ordering and are row-order independent.
- 5: Parcel-to-return resolution correctly handles unique ownership, valid hints, reused parcel IDs, closed returns, unknown IDs, and wrong warehouses.
- 4: Receipt sets/statuses are derived from current case state without inventing parcels or mutating during preview.
- 3: Preview state is server-owned and captures the case revisions needed for later apply.

## Frontend behavior — 12 points
- 4: Preview and apply states are understandable, with useful diagnostics and per-case results.
- 3: Filters and selected case remain coherent after successful or partially successful apply.
- 3: A slower obsolete preview cannot overwrite a newer requested preview/batch selection.
- 2: Transient failures preserve last known-good data/preview and show an actionable error.

## Integration — 10 points
- 4: API contracts keep scan rows and authoritative proposed mutations on the server rather than trusting browser-authored receipt sets.
- 3: Apply reconciles case list/detail, revisions, receipt state, and dataset revision consistently.
- 3: Existing exception mutation boundary and optimistic-concurrency contract remain intact.

## Edge cases / safety — 22 points
- 5: Partial stale apply is correct by case: stale cases are skipped, independent current cases can still succeed, and no skipped case is mutated.
- 4: Each successful case revision increments once and the dataset revision increments once per apply request only when at least one case changed.
- 4: Apply retries with the same request key are idempotent; key reuse for another preview is rejected.
- 3: A consumed preview cannot be replayed with a fresh request key against newer state.
- 3: Invalid timestamps/event kinds, unknown parcels/hints, ambiguity, wrong-warehouse receipts, and no-op changes are isolated and reported appropriately.
- 3: Empty/no-effective-change batches and retractions of previously received parcels are handled without revision inflation or fabricated state.

## Tests — 8 points
- 4: Focused domain tests cover at least deterministic canonicalization/event selection plus ambiguous resolution or retraction semantics.
- 2: Tests cover stale partial apply and/or idempotent retry behavior.
- 2: Existing tests remain green and new tests are deterministic and readable.

## Code quality — 3 points
- 2: Reconciliation/domain logic is separated enough from HTTP/DOM glue to reason about and test.
- 1: Naming, error handling, and state transitions are consistent with the starter rather than a parallel ad-hoc architecture.

## Verification / debugging — 3 points
- 2: Candidate demonstrates the green baseline and verifies at least one ordinary reconciliation plus a high-risk failure path.
- 1: Candidate can explain observed revisions/state after the verification scenario.

## Calibration
- **90–100 — Excellent:** End-to-end feature is robust, deterministic, and safe under duplicate/out-of-order data, ambiguous ownership, partial stale state, and retries. Existing behavior remains intact.
- **75–89 — Acceptable / strong:** Core preview/apply is correct with sound server authority and most dangerous edge cases covered; a smaller UI or diagnostic gap may remain.
- **60–74 — Partial:** Meaningful working slice, but one or more important reconciliation, concurrency, idempotency, or client-race behaviors are missing.
- **Below 60 — Failing / incomplete:** Happy-path-only, browser-authoritative, row-order-dependent, globally all-or-nothing when partial behavior is required, or unsafe under stale/retry conditions.

A solution that simply loops over CSV rows, marks matching parcels received, and updates cases from the browser should not score above **60–65**, even if the UI looks polished.
