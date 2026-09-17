# POST-PRACTICE ONLY — Interviewer Notes

## Intended solution outline
A strong solution treats reconciliation as a domain pipeline rather than as row-by-row mutations. Load the immutable scan feed once, select a batch, canonicalize duplicate scan identities deterministically, validate timestamps/kinds, reduce canonical rows to one effective event per parcel, resolve each parcel to a single eligible return, and then derive proposed receipt sets from a consistent case snapshot. Store the resulting proposal server-side under an opaque preview ID together with the captured revisions for cases that would actually change.

Apply should operate from that stored preview. For each proposed changed case, compare the captured revision with current state and independently mark that case success or conflict. Mutate only current cases, increment each changed case once, and increment the global dataset revision once if any case changed. Cache the complete apply result by request key so retries return the same result and cannot change state twice. Mark the preview consumed after its first logical apply attempt so a new key cannot replay it.

On the client, keep reconciliation state separate from the existing selected-case/exception state. Associate preview requests with a monotonically increasing local request token or otherwise check that the response still corresponds to the currently selected batch before committing it to UI state.

## Subtle traps / hidden checks
- Exact duplicate `scan_id` rows collapse without changing semantics or depending on CSV row order.
- Conflicting rows with the same `scan_id` use greatest `ingested_at`; equal ingestion times require the canonical-payload lexical tie-break.
- Canonicalization happens before choosing the effective event for a parcel.
- Effective parcel event ordering is by `scanned_at`, then `ingested_at`, then `scan_id`; CSV order must not leak into the result.
- Invalid timestamps cannot participate in ordering and should be reported rather than treated as zero time.
- `PKG-A2` is deliberately expected by two open returns. A blank hint is ambiguous; a valid hint can select one.
- A hint to a closed return does not make that return eligible.
- Wrong-warehouse `received` is invalid for the target case; `retracted` is about removing a prior receipt for the resolved return and should not be treated as a new warehouse receipt.
- Retraction of `PKG-C1` should be able to move a case backward in receipt state.
- A case whose derived receipt set equals its current set is not a mutation and must not inflate revisions.
- Manual exception edits increment the same case revision, so they intentionally make a stored reconciliation proposal stale for that case even though the exception field itself is orthogonal to parcel state.
- Partial apply is not a transaction across all cases. A stale case must not prevent independent current cases from succeeding.
- The dataset revision increments once for the apply request, not once per successful case.
- Same apply request key must return the prior per-case result exactly; do not re-evaluate formerly conflicted cases on retry.
- Reusing an idempotency key for a different preview is an error.
- Replaying a consumed preview with a new request key is an error rather than a fresh attempt.
- Delayed older preview responses must not repaint a newer selected batch.

## Likely failure modes
- Mutating cases during preview.
- Processing scan rows sequentially and therefore making output depend on fixture order.
- Treating conflicting duplicate IDs as two independent events.
- Resolving reused parcel IDs to the first matching return.
- Trusting `return_id_hint` without checking that the case is open and expects the parcel.
- Treating all apply conflicts as all-or-nothing despite the required per-case partial semantics.
- Incrementing the dataset revision once per case.
- Caching only successful cases for idempotency and allowing stale cases to apply on retry.
- Forgetting that the existing exception workflow changes the case revision.
- Clearing the preview on a transient error or accepting an out-of-order preview response in the browser.

## Expected prioritization
1. Understand existing case/revision semantics and the scan fixture.
2. Implement a pure/testable preview derivation path: canonicalize, validate, select effective parcel event, resolve owner, derive proposed case state.
3. Add server-owned preview storage and preview API.
4. Implement partial apply with revision checks, one dataset revision bump, idempotency, and consumed-preview semantics.
5. Wire a minimal usable UI and guard against obsolete preview responses.
6. Add focused tests for the highest-risk deterministic/stale/retry cases before polishing.

## Hidden-evaluator-style checks
- Shuffle scan rows repeatedly and compare preview output after removing opaque IDs/timestamps.
- Duplicate a valid row exactly; result should not change except duplicate diagnostics.
- Swap the order of two conflicting duplicate-ID rows with equal/different ingestion times.
- Preview a batch that affects multiple cases, then manually change exactly one affected case before delayed apply; verify one conflict and independent successes.
- Retry that partial apply with the same request key after changing the conflicted case again; verify byte-equivalent logical result and no new mutations.
- Attempt replay of the consumed preview using a different request key.
- Exercise `PKG-A2` with and without a valid hint.
- Exercise a retraction that changes `received` to `partial` or `awaiting`.
- Verify no-op proposed cases do not increment case/dataset revisions.
- Start two previews with different delays and ensure the older response cannot replace the newer batch's preview.
- Re-run all pre-existing exception tests and manually verify stale exception recovery still works.

## What to inspect after the hour
Look for a clear mutation boundary, deterministic data reduction that is independent of row order, explicit treatment of ambiguous ownership, server-owned preview state, correct per-case stale handling, exact revision accounting, full-result idempotency, and client-side protection from obsolete asynchronous responses. Ask the candidate to explain which invariants they protected first and which acceptance criteria they intentionally deferred.
