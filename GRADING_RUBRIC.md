# GRADING RUBRIC — 100 points

## 1. Functional end-to-end behavior — 22 points
- 6: Reviewer can select pending grants across more than one server-paginated page and see a persistent selected count.
- 5: Bulk approve/revoke submits grant IDs with the revisions captured at selection time plus one normalized reason and request key.
- 5: Response exposes a clear per-grant outcome and successfully applied grants visibly transition without a full page reload.
- 3: Successful items leave selection while failed/conflicted items remain understandable and deliberately recoverable.
- 3: Existing grant browsing, detail, filtering, pagination, and owner-note behavior continue to work.

## 2. Backend/domain policy correctness — 22 points
- 5: `pending` and expected-revision checks are server authoritative and happen per submitted grant.
- 4: Expiry is compared to the fixed cycle `asOf`; equality is expired.
- 5: `high` approval correctly accepts fresh usage OR a valid exception, with the freshness boundary inclusive.
- 4: `critical` approval requires a valid exception even with recent usage; equality at `asOf` is valid.
- 2: `low`/`medium`, null usage, and null exception semantics are correct.
- 2: Applied grants store normalized reason plus deterministic `reviewedAt = cycle.asOf` and increment their own revision once.

## 3. Concurrency, idempotency, and revision accounting — 16 points
- 4: One stale item does not block independent valid items; partial success is correct under delayed execution.
- 4: Same request key + same normalized logical payload returns the original result without reevaluating or mutating again.
- 3: Same request key + materially different payload fails clearly; item order does not make an otherwise identical logical payload different.
- 3: Dataset revision increments once per bulk request if and only if at least one grant changes, never once per successful grant.
- 2: Existing note mutation can make a selected grant stale without corrupting other outcomes.

## 4. Frontend state and reconciliation — 14 points
- 4: Selection is identity-based and survives page navigation under the same filters, with revision snapshot semantics preserved.
- 3: Filter changes handle hidden selection explicitly rather than silently carrying unknown selected grants.
- 3: After mutation, pagination is reconciled from a safe position so rows are not skipped/duplicated when the filtered set shrinks.
- 2: Older list responses cannot repaint newer filters/pages; bulk failure preserves useful last-known-good state.
- 2: In-flight duplicate bulk submission is prevented without freezing unrelated browsing.

## 5. Edge cases and request validation — 10 points
- 2: Empty request and >50 item request are rejected before mutation.
- 2: Duplicate grant IDs in one request are rejected before mutation.
- 2: Unknown, no-longer-pending, stale, expired, and policy-ineligible grants get distinct useful outcomes.
- 2: Reason trimming/length and malformed values are validated consistently.
- 2: Timestamp parsing failures are surfaced instead of guessed; exact boundary cases are handled correctly.

## 6. API/integration design — 6 points
- 2: Bulk contract is coherent, server authoritative, and returns enough current/result state for the browser to reconcile.
- 2: Optional bounded `delay_ms` is implemented in a way that can actually reproduce a stale item at execution time.
- 2: New routing/service/store code composes with the existing app rather than bypassing its state/revision model.

## 7. Tests — 5 points
- 3: Focused tests cover at least one partial-stale case, one approval-policy boundary, and retry idempotency.
- 2: Tests cover a frontend-relevant or pagination/revision regression risk, not only happy-path store calls.

## 8. Code quality — 3 points
- 3: Clear names, small coherent functions, no duplicated policy logic across client/server, and changes fit the starter structure.

## 9. Verification/debugging discipline — 2 points
- 2: Candidate can show commands/manual checks used and explain at least one discovered failure mode or tradeoff.

## Score caps

A submission that provides only a happy-path checkbox UI and bulk endpoint but ignores stale revisions, idempotency, policy boundaries, or pagination reconciliation should not score above **62/100**.

A solution that is backend-correct but has no credible cross-page frontend workflow should generally not exceed **78/100**. A solution that is visually polished but trusts browser-computed eligibility or silently applies stale grants should score substantially lower.
