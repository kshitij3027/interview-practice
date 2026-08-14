# POST-PRACTICE ONLY — Interviewer Notes

**Candidate: do not read this file before attempting the exercise.**

## Intended solution outline

A strong solution usually separates three responsibilities: CSV normalization/validation, deterministic reconciliation planning, and transactional-ish commit of a server-owned preview. The exact module boundaries are flexible.

A preview should be assigned an opaque server-generated identifier and stored in memory with normalized row outcomes, the proposed mutations, the revisions of affected accounts, and commit state. Commit should reference that server-side preview rather than accepting client-authored allocations.

For each account, planning should process valid non-duplicate payments in deterministic input order while maintaining a temporary view of invoice remaining balances and accumulated credit so that multiple payments in one file reconcile coherently without mutating live state.

Commit should check all affected revisions before any write. If any mismatch exists, reject the entire commit. If all match, apply the stored plan atomically under the process lock, update invoice statuses, aggregate account-credit changes, and increment each affected account revision once. Mark the preview committed and return the prior commit result on retry.

## Subtle traps

1. Using Python `float` for dollar parsing can introduce drift; string/Decimal-to-cents conversion is safer.
2. Previewing each row independently against live invoice state can allocate the same invoice balance more than once when several payments target one account.
3. Duplicate detection must be deterministic. The first occurrence is the candidate row; later identical IDs do not add money.
4. Account lookup is trim + case-insensitive, while persisted external IDs should remain unchanged.
5. Unknown/malformed rows should not abort valid rows.
6. Revision checks must happen before mutation; checking per account while mutating earlier accounts allows partial stale commits.
7. Revisions increment once per affected account for the import, regardless of number of rows/invoices.
8. A post-preview manual credit is an intentional conflict source and must invalidate commit.
9. Retry behavior should distinguish “same preview already committed” from a new invalid/stale request.
10. The client should preserve the CSV text on stale failure and allow re-preview rather than clearing operator work.

## Expected prioritization in 60 minutes

A strong candidate usually secures backend correctness first: parser + planner tests, server-owned preview, all-revision preflight, commit idempotency. Then they build a minimal but usable UI. Styling and exhaustive frontend abstractions should come last.

If time is short, correct backend semantics plus a rough end-to-end UI is better than a polished frontend with unsafe commit behavior.

## Hidden checks to run

- Header order changed but required names present.
- Blank line at end of CSV.
- `AcMe-001` and ` acme-001 ` both resolve to ACME-001.
- `10`, `10.0`, and `10.00` accepted; `10.001`, `1e2`, zero, negative, and non-numeric rejected.
- Duplicate payment ID appears with different data later; later occurrence still treated as duplicate, not a second payment.
- Two valid rows hit the same customer and together cross an invoice boundary.
- Two invoices share a due date; lexical invoice ID determines order.
- Payment exceeds all open invoices; remainder becomes credit.
- Preview leaves live store byte-for-byte equivalent for business state.
- Manual credit after preview changes revision; commit rejects with no invoice/payment mutation.
- Two affected accounts where only the second is stale; neither account mutates.
- Successful commit followed by same commit request returns committed result without double application.
- Existing manual-credit endpoint still increments revision and credit correctly after feature work.

## What to inspect after the hour

- Did the candidate identify revisioning as an existing invariant rather than replace it?
- Did they model preview state on the server or trust client allocations?
- Do multiple rows for one customer share a coherent temporary planning state?
- Is money parsed deterministically?
- Can stale detection cause partial writes?
- Are retry semantics explicit?
- Did they run tests/build and add focused tests for the dangerous cases?
