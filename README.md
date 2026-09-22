# AccessQ — HARD One-Hour Full-Stack Interview Exercise

## Context

AccessQ is an internal quarterly access-review console used by a security operations team. Reviewers inspect application grants, filter the queue by review state, system, and risk, open individual grants, and leave an owner note while they investigate whether access should remain.

The starter application already works. It uses a Node.js 20+ standard-library HTTP API, an in-memory fixture-backed store, a dependency-free browser ES-module frontend with explicit client state, and tests for the current pagination/filtering and owner-note workflow.

## Existing behavior

- The grant list is server-filtered and server-paginated.
- Rows are ordered deterministically by system, then principal, then grant ID.
- Reviewers can filter by status, system, and risk.
- Selecting a grant shows its role, risk, current status, usage/expiry data, exception window, owner note, and revision.
- Owner-note writes require the grant revision observed by the client.
- Stale note writes fail without mutation and return current grant state.
- A changed note increments that grant revision and the global dataset revision exactly once; saving the same normalized note is a no-op.
- Restarting the backend resets state from the checked-in fixtures.

Representative review data is in `fixtures/grants.json`; cycle policy inputs are in `fixtures/review_cycle.json`.

## Customer/business problem

Reviewers currently decide grants one at a time in a separate system. A typical reviewer filters the AccessQ queue to a system or risk level, pages through dozens of pending grants, and decides many of them together. The team wants that workflow inside AccessQ without forcing reviewers to keep one page open or serialize decisions manually.

This is harder than adding checkboxes. Selected grants may span several server-paginated pages. Another reviewer may change a selected grant after it was selected. Successfully decided grants may immediately disappear from the active `pending` filter, which makes old pagination positions unsafe to reuse. Some grants are not eligible for approval under the current review-cycle policy. Retries must not apply decisions twice, and a delayed response from an older list request must not repaint a newer filter/page.

## Primary feature request

**Add a cross-page bulk access-decision workflow that lets a reviewer select pending grants across server-paginated results and approve or revoke them with deterministic policy checks, per-grant conflict results, retry safety, and correct queue reconciliation after successful mutations.**

## Acceptance criteria

1. Add selection controls to grant rows and a persistent bulk-action area showing the number of selected grants. Selection must be by grant identity, not by row index, and must survive moving forward/backward through pages under the same active filters.
2. A selection snapshot must remember the grant revision that was visible when that grant was selected. Bulk execution must use those observed revisions rather than silently substituting a newer revision fetched later.
3. Only grants that were `pending` when selected may be submitted. The UI may disable selection for non-pending rows. The server must still validate every submitted item independently because state may have changed after selection.
4. A bulk request chooses exactly one decision, `approve` or `revoke`, and includes a reason. Trim the reason; after trimming it must contain 3–200 characters.
5. The server, not the browser, is authoritative for policy eligibility, current grant state, revisions, and mutation results.
6. `revoke` is allowed for any grant that is still `pending` and whose submitted revision is current.
7. `approve` is allowed only when the grant is still `pending`, its `expiresAt` is strictly later than the review cycle's `asOf`, and it satisfies the following cycle policy using the checked-in cycle timestamp:
   - `low` and `medium`: no additional usage requirement.
   - `high`: either `lastUsedAt` is at or after `asOf - staleUsageDays`, **or** `exceptionUntil` is at or after `asOf`.
   - `critical`: `exceptionUntil` must be at or after `asOf`; recent usage alone is not enough.
   Timestamp comparisons are by instant. A grant expiring exactly at `asOf` is expired; an exception ending exactly at `asOf` is still valid.
8. Missing `lastUsedAt` does not satisfy freshness. Missing `exceptionUntil` does not satisfy an exception requirement. Invalid fixture timestamps should produce a clear server-side error rather than a guessed decision.
9. A bulk request is **partially successful by grant**. One stale, missing, no-longer-pending, expired, or otherwise ineligible grant must not prevent independent valid grants in the same request from being decided.
10. Return one explicit result for every submitted grant, preserving grant identity and distinguishing at least: applied, stale revision, no longer pending, not found, expired, high-risk usage/exception failure, and critical-risk exception failure.
11. A successful decision changes that grant's status, stores the normalized decision reason, stores a deterministic reviewed-at value equal to the review cycle `asOf`, and increments that grant revision exactly once.
12. The global dataset revision increments exactly once for the overall bulk request when at least one grant changes, regardless of how many grants succeed. If zero grants change, the global dataset revision does not increment.
13. The request must include a client-generated request key. Repeating the same key with the same **normalized logical payload** must return the original per-grant result without changing any grant or revision again. Logical equality must not depend on submitted item order. Reusing the same key for a materially different decision, reason, or selected item/revision must fail clearly.
14. A request containing the same grant ID more than once is malformed and must be rejected before applying anything. Reject an empty selection and more than 50 submitted grants.
15. The bulk endpoint must support an optional bounded `delay_ms` query parameter so stale behavior can be reproduced locally: start a bulk decision, edit the owner note of one selected grant through the existing workflow, then let the bulk request execute. The changed grant must be reported stale while other eligible grants may still succeed.
16. After a bulk response, remove successfully applied grants from the current selection. Keep unsuccessful items represented in the result summary so the reviewer can understand and retry/reselect them deliberately.
17. Reconcile the visible queue without a full browser reload. Preserve the active status/system/risk filters, but do not continue from a pagination cursor whose filtered result set may have shifted after mutations. The refreshed page must not skip or duplicate surviving matching grants because earlier rows left the filter.
18. If a successfully decided grant is currently open in the detail panel, reconcile that detail/status/revision. If the grant no longer matches the active filters, the list may drop it while the outcome summary remains visible.
19. Selection must not accidentally transfer to a different filtered queue. When filters change, either clear the selection explicitly or preserve it with an unmistakable cross-filter selection model; silently keeping hidden selections without indicating them is not acceptable.
20. While list requests are in flight, changing filters or navigating again must not let a slower older response replace the newer requested page. A transient list or bulk failure must preserve the last known-good queue and selection when possible and show an actionable error.
21. Prevent accidental duplicate submission of a bulk operation while it is in flight, while keeping ordinary grant browsing usable.
22. Existing deterministic ordering, server-side filters, cursor pagination, grant detail, note validation, note no-op behavior, optimistic concurrency, and revision accounting must continue to work unchanged.

## Constraints

- Keep the Node.js standard-library backend and dependency-free browser ES-module frontend. Do not introduce a web framework, database, queue, websocket service, auth provider, or external API.
- Keep mutable state in one process and in memory.
- Use the checked-in review-cycle `asOf` for this exercise; do not replace the policy with the machine clock.
- The backend is authoritative for policy evaluation, permanent grant state, revisions, dataset revision, and idempotency outcomes.
- You may add store/service functions, API routes, frontend state/actions, rendering, and focused tests.
- Keep setup fast; do not make package/tooling work the challenge.

## Out of scope

- Authentication, reviewer identity, or permissions.
- Creating grants or changing principal/system/role/risk metadata.
- Editing review-cycle policy from the UI.
- Persisting state or request keys across process restart.
- Multi-process/distributed locking.
- Real-time push/polling for other reviewers' changes.
- Undoing a completed decision.
- Visual polish beyond a clear usable workflow.

## Setup / run

```bash
./scripts/run.sh
```

Open `http://localhost:8080`.

## Tests / build

```bash
./scripts/test.sh
./scripts/build.sh
```

The starter tests cover existing pagination/filtering and owner-note behavior. Add focused feature tests around the bulk semantics you consider highest risk.

## 60-minute AI-assisted interview instruction

You have **60 minutes**. You may use Claude Code, Codex, ChatGPT, or similar coding tools. Inspect the fixtures, current server pagination behavior, mutation/revision boundary, API routes, and browser state before changing code. Decide on a correctness-first slice, implement incrementally, and verify ordinary, partial-success, stale, retry, pagination-reconciliation, and out-of-order UI behavior.

A polished checkbox UI that sends row positions, applies stale grants, approves policy-ineligible access, double-applies a retry, or resumes an invalid cursor after rows leave the active filter should score poorly. Prioritize observable correctness and dangerous state transitions over cosmetic completeness.
