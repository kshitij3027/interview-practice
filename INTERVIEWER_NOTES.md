# POST-PRACTICE ONLY — INTERVIEWER NOTES

Do not show this file to the candidate during the timed exercise.

## Intended solution outline

A strong solution separates request-level validation, per-grant eligibility/conflict evaluation, mutation, and browser reconciliation.

On the server, normalize the bulk payload before idempotency comparison: trim the reason, validate one decision, reject duplicate IDs/empty/>50, represent each submitted item as `(grant_id, expected_revision)`, sort the item representation for the idempotency fingerprint, and preserve an explicit result keyed by grant ID. The request-key cache should store the normalized fingerprint plus a deep copy of the original response. An identical retry returns that stored response without reevaluating current state.

At execution time, evaluate each unique item independently against current state. Check existence, `pending`, and expected revision before policy eligibility. For `approve`, parse the fixed cycle `asOf`, expiry, usage, and exception timestamps; use inclusive freshness/exception boundaries and strict expiry. `revoke` needs no risk eligibility beyond current pending/revision checks. Collect valid mutations and per-item failures. Apply each valid mutation once, increment each changed grant revision once, then increment the dataset revision once if the valid mutation set is non-empty. Store the idempotency result after the logical operation is complete.

On the client, use an identity-keyed selection structure such as a `Map<grantId, {revision,...}>` separate from the current page array. Selection should capture the visible revision at click time. The simplest acceptable filter behavior is to clear selection explicitly on filter change. After bulk completion, remove successful IDs from selection, retain/render failures, invalidate any older list request, reset cursor/history, and refetch the first page under the currently active filters. Existing list request tokens can be reused/extended so slow older pages cannot repaint newer state.

## Policy checkpoints from the provided fixtures

At cycle `asOf = 2026-09-22T15:00:00Z` with a 30-day freshness window:

- `g-001`: low, pending, unexpired -> approval eligible.
- `g-002`: medium, old usage -> approval eligible because medium has no freshness requirement.
- `g-003`: high, fresh usage -> approval eligible.
- `g-005`: high, stale usage but valid exception -> approval eligible.
- `g-006`: expires exactly at `asOf` -> approval ineligible as expired.
- `g-007`: critical with valid exception -> approval eligible.
- `g-008`: critical with exception before `asOf` -> approval ineligible.
- `g-010`: high with stale usage and no exception -> approval ineligible.
- `g-011`: critical with very recent usage but no exception -> approval ineligible.
- `g-012`: low with null usage -> approval eligible.
- `g-013`: medium -> approval eligible.
- `g-014`: high with usage inside the freshness window -> approval eligible.

All still-pending grants are revocable if their submitted revision is current.

## Subtle traps

1. **Revision snapshot drift:** a weak UI reconstructs expected revisions from the latest page data at submit time. That defeats the point of selecting a snapshot and can hide a concurrent edit.
2. **Offset cursor after mutation:** the starter cursor is position-based. If several `pending` rows become approved/revoked, continuing from an old cursor can skip surviving rows. Reset after successful mutation.
3. **Dataset revision overcount:** incrementing global revision once per successful grant violates the contract; it is one increment for the whole bulk request.
4. **Idempotency order dependence:** the same logical item set in different array order must be considered identical.
5. **Idempotency re-evaluation:** retrying a successful key after state changes elsewhere must return the stored original result, not rerun eligibility and create a different answer.
6. **Boundary inversion:** expiry equality fails approval, while usage threshold equality and exception equality pass their respective checks.
7. **Critical shortcut:** recent usage never substitutes for a critical exception.
8. **Partial-success rollback:** request-level malformed payloads are atomic rejects, but normal per-item conflicts are not all-or-nothing.
9. **Selection leaks across filters:** hidden selected IDs carried silently into a different filter are dangerous. Clear or make the cross-filter model unmistakable.
10. **Out-of-order list response:** an older delayed GET can arrive after a post-mutation first-page refresh; response token/context checks must prevent repainting.
11. **Reason normalization:** idempotency should compare the trimmed logical reason, so `" audit "` and `"audit"` are the same logical payload.
12. **Changed grant detail:** if the currently open grant succeeds, the detail panel must not keep showing stale `pending`/revision state.

## Hidden checks

Use these after the candidate finishes; do not reveal them beforehand.

- Approve `g-006` at its exact expiry boundary -> must report expired and not mutate.
- Construct a high-risk grant whose `lastUsedAt` is exactly `asOf - 30 days` -> eligible.
- Construct high/critical grants whose `exceptionUntil` is exactly `asOf` -> exception is valid.
- Submit `[g-001@2, g-003@4]`, mutate `g-003` note during `delay_ms`, then execute -> `g-001` can succeed and `g-003` must be stale; dataset revision increments once for the bulk request plus whatever the note mutation already did.
- Submit two or more valid grants -> each revision +1, dataset revision only +1.
- Submit zero valid grants -> dataset revision unchanged.
- Retry the same key with identical items in reverse array order and extra reason whitespace -> original result, no second mutation.
- Retry the same key with one expected revision changed -> clear key-reuse conflict.
- Submit the same grant ID twice -> reject before any mutation.
- Include unknown ID alongside a valid ID -> unknown receives `not_found`, valid item may still succeed.
- Submit a grant that was changed from pending by an earlier request -> `no_longer_pending`, not `applied` and not a second revision bump.
- While viewing `status=pending`, decide early rows on page 1, then refresh -> surviving pending rows should not be skipped because an old cursor was reused.
- Select items on page 1 and page 2 -> selected count and captured revisions survive back/forward navigation.
- Change filters with non-empty selection -> selection is explicitly cleared or clearly carried with visible cross-filter semantics.
- Fire a slow old list request, change filters, then load a new page -> old response must not overwrite new filter/page.
- Force bulk request network failure -> last known-good queue and selection remain usable.
- Existing owner-note stale/no-op behavior still passes after feature changes.

## Likely AI-agent failure modes

- Generates a monolithic `/bulk` route with client-side policy checks duplicated from the backend.
- Uses current grant revisions from a fresh server lookup rather than submitted selection revisions.
- Treats all item failures as one transaction failure, losing required partial-success semantics.
- Uses `Date.now()` instead of the review cycle `asOf`, making results nondeterministic.
- Stores idempotency keys but not normalized payload fingerprints, so key reuse with different requests is silently accepted.
- Fingerprints raw JSON, making item order or whitespace alter logical identity.
- Increments dataset revision inside the item loop.
- Keeps cursor/history after a filtered result set shrinks.
- Stores selection as checkbox indexes tied to the current page.
- Clears the whole UI on an error or lets a delayed response reset filters.
- Focuses on CSS and leaves policy/retry/concurrency paths untested.

## Recommended prioritization for a 60-minute attempt

1. Understand starter revision and cursor semantics.
2. Implement server-side normalized bulk request validation, policy evaluation, partial results, revisions, and request-key idempotency.
3. Add focused store/API tests for policy boundaries, partial stale, and retry.
4. Add cross-page identity-based selection and bulk controls.
5. Reconcile successful/failed outcomes and reset pagination safely.
6. Verify delayed stale behavior and an out-of-order list request if time remains.

A candidate who completes the backend core plus a credible cross-page UI slice and can explain the remaining race handling can still perform strongly. Cosmetic completion should not compensate for incorrect access decisions.

## Walkthrough inspection points

Ask the candidate to show:

- Where selection-time revisions are stored and why later page reloads do not silently overwrite them.
- The exact function that decides `high` and `critical` approval eligibility.
- How the idempotency fingerprint is normalized and why item ordering does not matter.
- Where global dataset revision increments and why it happens once.
- How a delayed note mutation makes only one bulk item stale.
- What happens to cursor/history after successful decisions remove rows from `pending`.
- How an older list response is prevented from repainting current filters.
- Which tests they chose and what failure each test would catch.

## Complexity / scalability notes

This is not primarily an algorithm puzzle. With a maximum request size of 50, an `O(k)` bulk pass over selected IDs with `O(1)` map lookups is sufficient. The interesting scale issue is preserving server-side pagination semantics and avoiding unsafe cursor reuse after mutation, not inventing a complex data structure. Idempotency storage is in-memory and may grow with successful request keys for the process lifetime; bounded eviction is a defensible extension but not required for the interview unless the candidate raises it.
