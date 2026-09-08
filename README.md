# ShiftBoard — HARD One-Hour Full-Stack Interview Exercise

## Context

ShiftBoard is an internal scheduling console for a regional retail operations team. Staffing coordinators use it to inspect published shifts across two sites and make occasional one-off assignment corrections when coverage changes.

The starter application already works. It uses Ruby 3.3 with WEBrick for the HTTP API and static app, an in-memory domain store loaded from JSON fixtures, a dependency-free browser ES-module frontend with explicit client state, and existing tests for current assignment behavior.

## Existing behavior

- The dashboard lists published shifts ordered by start time, site, then shift ID.
- Coordinators can filter shifts by site.
- Selecting a shift shows its current assignee and revision.
- A coordinator can reassign one shift to another employee.
- Single-shift reassignment validates that the employee is qualified for the shift's site and role.
- A reassignment is rejected if it would overlap another shift currently assigned to that employee.
- Writes use the shift revision for optimistic concurrency; stale writes fail without mutation.
- A successful changed assignment increments that shift revision and the global schedule revision exactly once.
- Restarting the server resets the fixture-backed schedule.

## Customer/business problem

Employees frequently trade published shifts with each other. Today those swaps are coordinated in chat, then a staffing coordinator performs two separate assignments in ShiftBoard. That is unsafe: the first reassignment can succeed while the second fails, a different coordinator can edit one shift in between, or a swap can accidentally leave an employee with an invalid schedule.

Operations wants ShiftBoard to track the swap request itself and finalize both assignment changes as one logical operation. The workflow must remain understandable when requests expire, users retry after network failures, or the underlying schedule changes while a request is pending.

## Primary feature request

**Add a two-shift swap-request workflow that validates the resulting schedules, tracks the request lifecycle, and atomically exchanges the two assignees when the request is accepted, with stale-state and retry protection.**

## Acceptance criteria

1. Add a UI workflow for creating a swap request between two distinct currently assigned shifts and for viewing pending/recent swap requests. A pending request can be accepted or rejected.
2. A request may only be created for two existing shifts with two different current assignees. A shift may not participate in more than one still-active swap request at a time.
3. At request creation, validate the schedule that would result from the swap. Each employee must be qualified for the destination shift's site and role.
4. In the proposed post-swap schedule, neither employee may overlap another shift they would continue to own. When validating, the two shifts participating in the swap must be treated as being replaced, not as extra shifts layered on top of the current schedule.
5. In the proposed post-swap schedule, each employee must have at least **8 hours of rest** between the destination shift and their immediately adjacent other shifts. Exactly 8 hours is allowed. Evaluate using the timestamps in the shift data rather than browser-local formatted times.
6. Creation must capture the revisions of both shifts plus the current global schedule revision and return a server-generated swap-request ID. A new request is `pending` and expires **30 minutes** after creation according to server time.
7. Creation must accept a client-generated request key. Retrying the same key with the same normalized pair of shift IDs must return the original successful request without creating another request. The pair is unordered for idempotency purposes: requesting A/B and then retrying B/A with the same key is the same logical payload. Reusing the key for a different pair must fail clearly.
8. Rejecting a still-pending, non-expired request changes only the request lifecycle state; it must not change either shift assignment or the schedule revision.
9. Accepting a request must re-check expiration and the captured revisions before changing any shift. If either captured shift assignment/revision or the captured global schedule revision no longer matches current state, reject the acceptance before any shift mutation and return enough current state for the UI to recover.
10. A successful acceptance must swap the two assignees atomically, increment each changed shift revision exactly once, increment the global schedule revision exactly once for the logical swap, and mark the request accepted. There must never be an observable state where only one side of the swap was applied.
11. Acceptance must be retry-safe using a client-generated request key. Retrying a previously successful acceptance with the same key must return the prior result without swapping back or incrementing any revision again. Reusing the acceptance key for a different swap request must fail clearly.
12. An expired request cannot be accepted. The API/UI must distinguish `expired` from `rejected`, `accepted`, and a stale/conflicted acceptance outcome. Do not require a background worker solely to make expiration work.
13. The accept endpoint must support an optional bounded `delay_ms` query parameter so a stale acceptance can be reproduced locally by starting accept, changing one involved shift through the existing reassignment flow, and letting accept finish afterward.
14. While a create/accept/reject operation is in flight, prevent accidental duplicate submission of that same operation, while keeping unrelated shift browsing usable.
15. After a successful accepted swap, reconcile the visible shift list/details and request state without a browser reload. Preserve the current site filter and keep the selected shift when it still exists.
16. On a stale/conflicted acceptance, preserve the visible request and current filter/selection, refresh the relevant shift/schedule state, and present a clear path to create a new request. Do not make the UI appear as though the swap succeeded.
17. A transient create/accept/reject failure must leave the last known-good schedule and request list usable and show an actionable error rather than clearing the screen.
18. Existing shift ordering, site filtering, single-shift qualification/overlap validation, single-shift optimistic concurrency, and revision behavior must continue to work.

## Constraints

- Keep the current Ruby + WEBrick + browser ES-module stack and dependency-free setup.
- Keep state in one process and in memory; no database, Redis, queue, auth provider, websocket service, or external API.
- The backend is authoritative for swap lifecycle, validations, permanent request IDs, revisions, expiration, and idempotency results.
- You may add service/store modules, API routes, frontend state/actions, and focused tests.
- Keep the feature interview-sized; do not replace the application with a framework.

## Out of scope

- More than two shifts per swap request.
- Open-shift bidding or finding suggested swap partners.
- Authentication or modeling which employee clicked accept.
- Persisting swap requests across server restarts.
- Notifications, email, SMS, or real-time push.
- Multi-process/distributed locking.
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

Existing tests cover the current single-shift workflow only. Add focused feature tests based on the requirements; there are intentionally no feature TODOs or solution-shaped starter tests.

## 60-minute interview instruction

You have **60 minutes**. Treat this as an AI-assisted live product-engineering interview. Inspect the existing store mutation boundary, reassignment rules, API behavior, fixtures, and frontend state flow before changing code. Choose a correctness-first core path, implement incrementally, and verify ordinary plus stale/retry behavior.

A polished request board that can partially apply a swap, mishandle rest boundaries, double-apply on retry, or accept against stale shift state should score poorly. Prioritize the most dangerous invariants and observable verification over cosmetic completeness.
