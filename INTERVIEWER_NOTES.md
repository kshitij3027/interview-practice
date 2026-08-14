# POST-PRACTICE ONLY — Interviewer Notes

**Do not read this file before completing the exercise.**

## Intended solution outline

A strong solution usually adds a batch request/response contract, keeps authoritative processing in the backend service/store boundary, deduplicates selections, resolves current rows, sorts them by queue order, and processes them sequentially so capacity effects are deterministic. The frontend should model selection independently from the visible page, storing `{id, expectedRevision}` (and optionally display metadata) rather than deriving selection solely from rendered rows.

The bulk endpoint should return one outcome per unique opportunity with enough information for the client to separate successes from failures and update selection state safely. It should not require all items to succeed.

## Likely failure modes

- Processing in client-supplied order, making capacity outcomes nondeterministic.
- Computing target capacity once and failing to decrement/adjust after successful moves.
- Counting already-owned rows as new capacity consumption.
- Clearing all selection after partial success.
- Keeping selection only as checkboxes on the current page.
- Reusing the single-reassign endpoint N times from the browser, which makes batch semantics/order and reconciliation fragile.
- Ignoring expected revisions in bulk writes.
- Deduplicating after mutation rather than before processing.
- Returning only aggregate counts, leaving the client unable to reconcile hidden selections.

## Hidden checks

1. Target has exactly one free slot; request order is opposite priority order.
2. Duplicate ID appears with conflicting expected revisions; one deterministic unique item outcome only.
3. Stale highest-priority item fails, then next eligible item can consume remaining capacity.
4. One opportunity is already on the target owner and should succeed/no-op without consuming a new slot; revision behavior should be consistent with the candidate's documented contract (prefer no mutation/no revision bump for a true no-op).
5. Closed and region-mismatched rows fail independently.
6. Filter hides two selected IDs before bulk response; hidden selection state must still reconcile.
7. Single reassign and cursor tie behavior still pass existing tests.

## Subtle traps

- Capacity depends on current server state, not the revisions captured on selected rows.
- Deterministic ordering matters only when capacity can run out; naive tests may miss it.
- Selection persistence and filter visibility are different concerns.
- Per-item stale checks should happen before mutation of that item, but failures should not create batch-level rollback.
- If the candidate chooses a response status like 200 vs 207, consistency and client behavior matter more than the exact status code.

## Expected prioritization

A strong 60-minute sequence is:
1. Understand list ordering, single-reassign rules, and frontend paging state.
2. Implement/test backend batch semantics first, especially deterministic capacity + stale partial failure.
3. Add selection model independent from current page.
4. Wire bulk action and reconcile successes/failures.
5. Run existing tests plus a mixed-outcome feature test and manually verify cross-page selection.

## What to inspect after the hour

- Does batch processing have one authoritative deterministic order?
- Can any failure accidentally mutate a row?
- Is capacity recomputed/updated correctly as successes occur?
- Can hidden selected rows be lost or left ghost-selected?
- Are successful and failed rows distinguishable enough for the frontend?
- Did the candidate preserve existing single-row behavior and cursor ordering?
