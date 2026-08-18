# Grading Rubric — 100 points

## Functional correctness — 20 points
- **18–20 Excellent:** reserve → inspect hold → confirm/release works end to end, with correct state shown in the UI and no regressions to existing stock adjustment.
- **13–17 Acceptable:** core workflow works but one meaningful lifecycle or reconciliation issue remains.
- **7–12 Partial:** happy path works for simple orders but important states are incomplete.
- **0–6 Failing:** feature is largely non-functional or corrupts inventory/order state.

## Backend/domain behavior — 20 points
Evaluate aggregation of duplicate SKU lines, availability accounting, deterministic warehouse selection, split allocations, atomic reservation, order/hold transitions, and revision increments.

- **18–20 Excellent:** domain behavior is deterministic, atomic, and easy to reason about.
- **13–17 Acceptable:** mostly correct with one moderate semantic gap.
- **7–12 Partial:** route-level implementation works for simple cases but has fragile accounting or state transitions.
- **0–6 Failing:** incorrect inventory math, partial reservation, or broken lifecycle semantics.

## Frontend behavior — 10 points
Evaluate reservation controls, readable allocation/hold state, confirm/release controls, preservation of selected order, error feedback, and refreshed inventory/order state after mutations.

## Integration/API contract — 10 points
Evaluate whether client and server agree on request keys, revisions, hold identifiers, lifecycle outcomes, and whether authoritative allocation remains server-side.

## Edge cases and safety — 22 points
High-weight hidden-evaluator themes include:
- duplicate order lines for the same SKU;
- shortage on a later SKU after earlier SKUs appear allocatable;
- active reservations consuming availability;
- preferred-zone warehouse ordering, `pick_rank` ties, lexical ID ties, and split allocations;
- stale inventory revision before reserve;
- same request key retried for the same order;
- same request key reused for a different order;
- second non-idempotent reserve attempt for an already-held order;
- expiry exactly at the boundary;
- expired hold cleanup happening once rather than on every read;
- confirm retry after successful confirmation;
- release retry after successful release;
- manual stock adjustment while quantities are reserved;
- ensuring rejected or expired transitions do not partially mutate state.

**18–22 Excellent:** handles nearly all high-risk cases correctly.
**12–17 Acceptable:** core safety is sound but a few boundary cases remain.
**6–11 Partial:** several important traps are missing.
**0–5 Failing:** happy-path-only behavior or unsafe mutations.

## Tests — 10 points
- **9–10 Excellent:** focused tests cover deterministic allocation plus multiple failure/retry/expiry cases.
- **6–8 Acceptable:** meaningful tests cover the core lifecycle and at least one dangerous edge case.
- **3–5 Partial:** limited happy-path tests.
- **0–2 Failing:** no useful feature tests.

## Code quality — 4 points
Clarity, naming, reasonable decomposition, minimal accidental complexity, and consistency with the starter architecture.

## Verification/debugging — 4 points
Evidence that the candidate ran existing tests/build, exercised the feature end to end, and deliberately verified at least one stale/expiry/retry scenario.

## Overall calibration
- **90–100 Excellent:** robust under hidden checks, strong prioritization, good verification.
- **75–89 Strong/acceptable:** core feature correct with a few contained gaps.
- **60–74 Partial:** substantial progress but important lifecycle/safety holes remain.
- **Below 60 Failing:** brittle, incomplete, or happy-path-only implementation.

A solution that merely creates a reservation and renders it, without correct atomicity, deterministic allocation, expiry, revision protection, and retry safety, should **not score above roughly 60–65**, even if the UI is polished.
