# POST-PRACTICE ONLY — Interviewer Notes

## Intended solution outline

A strong solution separates preview calculation from mutation. It first normalizes suggestion identity deterministically, flags conflicting duplicate IDs, validates each surviving suggestion against the selected document, filters by confidence, then subtracts the union of existing redaction intervals from each valid suggestion. The remaining labeled fragments are resolved into canonical non-overlapping output geometry by page using category precedence, then same-category adjacent/overlapping output is coalesced and sorted.

The server stores an opaque preview record containing document ID, source revisions, normalized proposed ranges, categorization details, and applyability. Apply looks up that preview, checks request-key reuse, verifies reviewable status and exact document revision before any mutation, then creates all machine redactions in one synchronized mutation and increments document/dataset revision once. Successful apply results are cached by request key for retry safety.

The client should keep preview state tied to the selected document and confidence input, disable only the active operation, preserve last known-good preview on transient failures, and refresh/reconcile document data after success or stale conflict.

## Subtle traps / hidden checks

- `sg-1004` appears twice with identical payload and must count once.
- `sg-dup` has conflicting payloads. At thresholds that include it, the preview is blocking regardless of file order.
- `sg-1002` is fully covered by an existing manual redaction.
- `sg-1005` overlaps higher-precedence credentials geometry and must retain only its non-overlapped personal portion after canonicalization.
- `sg-1007` and `sg-1008` overlap with the same category and should coalesce after normalization.
- `sg-2005` refers to a page that does not exist; `sg-2006` extends beyond page text. Neither should crash preview.
- Existing manual redactions must remain byte-for-byte unchanged after machine apply.
- A suggestion partially covered by a manual interval can split into two fragments; hidden data should exercise this even if the visible fixture does not make it the most obvious case.
- Boundary semantics are half-open: touching intervals do not overlap, but final same-category adjacent fragments should coalesce by requirement.
- A delayed apply that loses the revision race must add zero redactions.
- Retry of a successful apply with the same request key must not generate new IDs or increment revisions.
- A zero-range preview should not necessarily increment document revision on apply; a strong design treats it as a successful no-op and caches that result idempotently.

## Likely failure modes

- Processing suggestions in CSV order and letting later rows win overlaps.
- Deduplicating by range/category instead of `suggestion_id`.
- Treating a conflicting duplicate ID as two independent invalid rows instead of a blocking identity ambiguity.
- Dropping an entire partially overlapped suggestion rather than subtracting only covered geometry.
- Mutating existing manual ranges to simplify normalization.
- Resolving cross-category overlap by choosing one whole input range instead of only the overlapping characters.
- Using client-submitted normalized ranges on apply.
- Checking revision after adding the first machine redaction, allowing partial stale mutation.
- Incrementing document/global revision once per generated redaction.
- Generating new redactions again on apply retry.
- Clearing preview/input state on conflict or transient failure.

## Expected prioritization

1. Pure normalization/domain helper with small focused tests.
2. Preview endpoint and server-owned preview storage.
3. Atomic revision-checked/idempotent apply.
4. Minimal readable UI and state reconciliation.
5. Delay-driven stale test, extra edge cases, and polish.

## What to inspect after the hour

Look for a clear interval model, deterministic canonicalization independent of fixture order, explicit precedence handling, a mutation boundary that protects manual state and revisions, server ownership of preview geometry, retry semantics that cannot double-apply, and evidence that the candidate verified the dangerous cases rather than relying only on generated code.
