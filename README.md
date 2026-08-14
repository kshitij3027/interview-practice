# QueuePilot — HARD One-Hour Full-Stack Interview Exercise

## Context

QueuePilot is an internal sales-operations tool for a B2B software company. Ops leads use it to work a prioritized opportunity queue and occasionally reassign a single opportunity when coverage changes.

The starter app already works. It has a Go HTTP API, in-memory domain/store logic, a browser ES-module frontend with explicit client state, stable cursor pagination, composable filters, a rep roster loaded from JSON, and existing tests for current behavior.

## Existing behavior

- Opportunities are sorted by `priority_score` descending, then `id` ascending.
- The queue supports account search, owner filtering, stage filtering, and cursor pagination.
- A user can reassign one visible opportunity at a time.
- Single reassignment uses the opportunity `revision` to reject stale writes.
- Closed opportunities cannot be reassigned.
- A rep may only own opportunities in regions listed in `fixtures/rep_roster.json`.
- Each rep has a `max_active` capacity; closed opportunities do not count toward capacity.
- Restarting the backend resets sample opportunity data.

## Customer/business problem

Quarter-end territory changes require sales ops to move groups of opportunities quickly. Today an operator must open and reassign records one by one. That is slow, and it becomes dangerous when the queue is paginated: selected records may be on different pages, records may change while the operator is working, and the target rep may run out of capacity partway through a move.

Ops wants a bulk workflow that is fast but does not silently overwrite newer changes or pretend the entire batch succeeded when only some records were eligible.

## Primary feature request

**Add a cross-page bulk reassignment workflow that moves selected opportunities to one rep with deterministic partial-success behavior, stale-write protection, and accurate client reconciliation.**

## Acceptance criteria

1. Add row selection to the queue and allow selections to persist while navigating between cursor pages. A selected opportunity must retain the revision observed when it was selected.
2. Filtering/searching may hide selected opportunities, but must not silently drop them. The UI must show the total selection count even when some selected rows are not on the current page.
3. Add a bulk action that targets one rep and sends the selected opportunity IDs with their expected revisions to the backend. Duplicate IDs in a request must not cause the same opportunity to be processed twice.
4. The backend must process the unique selected opportunities in deterministic queue order: `priority_score` descending, then `id` ascending, regardless of the order supplied by the client.
5. Each opportunity is evaluated independently. One failure must not abort other valid moves. The response must make each item's outcome distinguishable and include a useful batch summary.
6. A row must fail without mutation if it no longer has the expected revision, is closed, does not exist, or the target rep does not cover its region.
7. Target-rep capacity must be enforced across the batch. Successful earlier moves in the same deterministic batch consume capacity for later rows. Moving an opportunity that is already owned by the target rep must not consume an additional capacity slot.
8. An opportunity that succeeds must change owner and increment revision exactly once. A failed opportunity must not change owner or revision.
9. Capacity decisions must use the current server state at execution time, not counts calculated by the browser.
10. After a partial-success response, the UI must remove successful opportunities from the selection, keep failed opportunities selected for correction/retry, refresh the visible page, and present a concise success/failure summary without requiring a browser reload.
11. If a selected opportunity is no longer visible because of current filters, its success or failure must still reconcile correctly in selection state.
12. Re-submitting a failed stale item after the user refreshes/reselects it with its new revision should be possible without clearing unrelated selections.
13. Existing single-opportunity reassignment, filtering, search, ordering, and cursor pagination must continue to work.
14. The client must prevent accidental double-submission of the same bulk request while it is in flight.

## Constraints

- Keep the current Go + browser ES-module stack.
- Keep storage in-memory; no database, Redis, queue, auth provider, or external API.
- Use the existing rep roster and capacity rules as the source of truth.
- You may add endpoints, service/store methods, frontend state helpers, and tests.
- Do not replace cursor pagination with offset pagination or fetch the entire dataset just to implement selection.

## Out of scope

- Authentication/authorization.
- Distributed locking or multiple backend processes.
- Persisting state across backend restarts.
- Undo/history UI.
- Visual polish beyond clear usable controls and feedback.

## Setup / run

Backend:

```bash
go run ./cmd/server
```

Frontend (separate terminal):

```bash
python -m http.server 5173 -d web
```

Open `http://localhost:5173`.

## Tests / build

```bash
go test ./...
go build ./...
node --check web/api.js
node --check web/store.js
node --check web/app.js
```

Existing tests cover current behavior only. Add feature-specific tests you consider necessary.

## 60-minute interview instruction

You have **60 minutes**. Treat this as an AI-assisted live coding interview. Inspect the repository before asking an agent to change it, identify the core correctness risks, implement incrementally, and verify both backend and UI behavior.

A complete-looking happy path with incorrect capacity, stale revision, pagination, or partial-failure semantics will score poorly. Prioritize correctness and observable verification over cosmetic completeness.

**Do not read `INTERVIEWER_NOTES.md` until after you finish.**
