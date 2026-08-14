# Grading Rubric — 100 points

Happy-path-only implementations should generally land at **60–65 points or below**.

## Functional correctness — 20
- 18–20: End-to-end bulk workflow works across pages and partial outcomes reconcile correctly.
- 13–17: Core bulk flow works with minor gaps.
- 7–12: Happy path works but important selection or response behavior is incomplete.
- 0–6: Workflow is largely nonfunctional.

## Backend/domain behavior — 20
- Deterministic queue-order processing.
- Per-item validation and mutation isolation.
- Correct revision handling.
- Correct target-owner no-op/capacity semantics.

## Edge cases & consistency — 20
- Stale revisions do not overwrite newer state.
- Capacity is consumed by earlier successes within the same batch.
- Region/closed/missing failures do not poison valid rows.
- Duplicate IDs cannot double-mutate.
- Mixed success/failure batches remain internally consistent.

## Frontend behavior — 15
- Selection survives pagination and hidden-by-filter state.
- In-flight duplicate submission is prevented.
- Successes are removed and failures retained after response.
- Current page is reconciled/refreshed after action.

## Integration/API contract — 10
- Request/response contract exposes enough per-item detail for robust UI handling.
- Frontend does not calculate authoritative capacity itself.
- Existing single-reassign and list endpoints remain compatible.

## Tests — 7
- Focused feature tests cover at least deterministic capacity and stale/partial failure behavior.
- Tests are meaningful rather than snapshots of implementation details.

## Code quality — 4
- Changes fit existing layering and avoid unnecessary rewrites.
- Naming/data structures make batch semantics understandable.

## Verification/debugging — 4
- Candidate demonstrates green baseline plus feature verification.
- Uses at least one mixed-outcome scenario rather than only a happy path.

## Hidden-evaluator-style checks

The evaluator may exercise cases such as:
- Client sends IDs in reverse priority order while the target rep has only one slot left.
- Same ID appears more than once in the batch.
- One selected row changed revision after selection while neighbors remain valid.
- A selected row is hidden by a filter when the batch completes.
- A row is already owned by the target rep while capacity is otherwise full.
- A high-priority row fails region validation; a lower-priority valid row should still be considered.
- Existing single reassignment still rejects stale revisions after bulk code is added.

## Overall calibration

- **90–100 (Excellent):** Correct end-to-end workflow with robust partial failure, deterministic capacity, stale-state handling, tests, and verification.
- **75–89 (Strong/acceptable):** Core design is sound; a limited edge case or UX reconciliation gap remains.
- **60–74 (Partial):** Useful happy path exists, but one or more major correctness dimensions are weak.
- **Below 60 (Failing):** Core semantics are missing, unsafe, or insufficiently integrated.
