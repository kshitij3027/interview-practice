# EntitleOps — HARD One-Hour Full-Stack Interview Exercise

## Context

EntitleOps is an internal subscription-operations tool for a B2B SaaS company. Support and billing operators use it to inspect an account's plan timeline and, when necessary, change the plan that is effective today.

The starter application already works. It uses a small Ruby 3.3/WEBrick HTTP API, in-memory state loaded from JSON fixtures, a browser ES-module frontend with explicit client state, and existing tests for current subscription behavior.

## Existing behavior

- The dashboard lists customer accounts and their subscription revision.
- Selecting an account shows its effective-dated plan timeline.
- A plan segment has a `start_on`, an optional exclusive `end_on`, and a `plan_key`.
- Operators can change the plan that is effective on the configured business date.
- An immediate plan change preserves already-scheduled future boundaries and increments the account revision exactly once.
- Immediate changes use optimistic concurrency: a stale expected revision is rejected without mutation.
- The plan catalog and business date are loaded from fixtures.
- Restarting the backend resets state.

## Customer/business problem

Enterprise customers often negotiate temporary upgrades, launch-period entitlements, or future downgrades. Today those changes are coordinated manually and then applied on the effective date. That creates missed changes and makes overlapping commitments difficult to reason about.

Operations wants to schedule a future plan interval in advance and see exactly how it will alter the account's existing timeline before anything is persisted. Existing future changes may already be present, so inserting a new interval must produce one deterministic, non-overlapping timeline rather than simply appending another row.

## Primary feature request

**Add a server-authoritative preview-and-apply workflow for scheduling one future plan interval, with deterministic timeline overlay semantics, stale-revision protection, and retry-safe apply behavior.**

## Acceptance criteria

1. Add UI controls for an operator to choose an account, target plan, `start_on`, and optional `end_on`, then request a preview before applying anything.
2. Dates use `YYYY-MM-DD` business-date semantics. `start_on` must be on or after the configured business date. If `end_on` is provided it is exclusive and must be strictly after `start_on`.
3. The target plan must exist in the supplied plan catalog and be active. Invalid input must return a useful non-2xx response without changing state.
4. Preview must overlay the requested plan onto the account's existing timeline for `[start_on, end_on)`, or from `start_on` onward when `end_on` is omitted. Existing timeline portions outside that interval must remain semantically unchanged.
5. If `end_on` is provided, the plan that would have been effective at `end_on` **before this request** must resume at `end_on`, even when an existing scheduled boundary falls inside the temporary interval.
6. The resulting timeline must be deterministic, sorted, gap-free from the first existing segment onward, and contain no overlaps or zero-length segments. Adjacent segments with the same `plan_key` must be coalesced.
7. Preview must not mutate the live account timeline or revision. It must return the account revision it was based on and enough information for the UI to render the proposed resulting timeline.
8. Treat the preview as server-owned state. Applying must reference an opaque preview identifier; the server must not trust a client-submitted replacement timeline as authoritative.
9. Apply must atomically replace the account timeline with exactly the previewed timeline only if the account revision still matches the revision captured by that preview. A stale preview must apply nothing.
10. A successful apply increments the account revision exactly once, regardless of how many timeline segments change.
11. Re-applying the same successfully applied preview must be retry-safe: it must not mutate again or increment the revision again, and the client must be able to distinguish this retry from a new stale/invalid request.
12. An existing immediate plan change made after preview must invalidate that preview through the normal revision mechanism.
13. After successful apply, the UI must reconcile the account list and selected account timeline without requiring a browser reload.
14. If apply fails because the preview is stale, preserve the operator's entered plan/dates, refresh the selected account, show a useful conflict message, and make generating a fresh preview straightforward.
15. Existing account listing, timeline display, plan catalog loading, immediate plan change, validation, and stale-write behavior must continue to work.

## Constraints

- Keep the existing Ruby/WEBrick + browser ES-module stack.
- Keep state in memory; do not add a database, Redis, queue, auth provider, or external API.
- Use the configured business date from `fixtures/system.json`; do not make exercise correctness depend on the machine's wall clock.
- Treat the backend as the source of truth for timeline semantics.
- You may add service/domain modules, routes, client state, and tests as needed.
- Keep the implementation interview-sized.

## Out of scope

- Billing/proration calculations.
- Time zones or timestamps finer than a business date.
- Editing multiple accounts in one operation.
- Persistent state across server restarts.
- Authentication/authorization.
- Distributed locking or multiple backend processes.
- Visual design polish beyond a clear usable workflow.

## Setup / run

```bash
./scripts/run.sh
```

In a second terminal:

```bash
python3 -m http.server 5173 -d web
```

Open `http://localhost:5173`.

## Tests / build

```bash
./scripts/test.sh
./scripts/build.sh
```

Existing tests cover current behavior only. Add feature-specific tests based on the requirements. There are intentionally no TODOs or starter tests that encode the scheduling solution.

## 60-minute interview instruction

You have **60 minutes**. Treat this like a demanding AI-assisted product-engineering/FDE live build. Inspect the repository and existing timeline/revision behavior first, choose the highest-risk correctness path, implement incrementally, and verify both the domain semantics and the browser flow.

A polished UI with incorrect interval boundaries, resume semantics, stale protection, or retry behavior is not a strong solution. Prioritize correctness, targeted verification, and time management.
