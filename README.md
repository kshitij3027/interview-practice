# Incident Desk — HARD One-Hour Full-Stack Interview Exercise

## Context

Incident Desk is an internal incident-response console used by an infrastructure team during active production incidents. Responders use it to see current incidents, inspect the action items created during an incident, and keep a small amount of incident state current while several people are working at once.

The starter application already works. It uses a dependency-free TypeScript/Node.js HTTP API, an in-memory domain store loaded from JSON, shared TypeScript contracts, and a browser ES-module frontend with explicit client state.

## Existing behavior

- The dashboard lists incidents sorted by severity and start time.
- Operators can filter incidents by severity.
- Selecting an incident shows responders and its current action items.
- Action items are currently read-only and have their own revision numbers.
- Operators can change an incident's severity between `sev1`, `sev2`, and `sev3`.
- Severity writes use the incident revision for optimistic concurrency; stale writes fail without mutation.
- Successful severity changes increment the incident revision and global dataset revision exactly once.
- Restarting the backend resets state from `fixtures/incidents.json`.

## Customer/business problem

During a live incident, responders continuously create and finish action items while the incident commander keeps the board filtered to what still needs attention. Today they have to coordinate those changes outside Incident Desk and refresh the page manually.

The team wants the action board to feel immediate even when the connection is slow, but it cannot silently duplicate a newly created action, overwrite a newer update made by another responder, or let a delayed response from an old incident corrupt the incident currently on screen.

## Primary feature request

**Add an optimistic action-item workflow that lets responders create action items and mark existing items done or open immediately in the UI, while remaining retry-safe, concurrency-safe, and correct when requests complete slowly or out of order.**

## Acceptance criteria

1. Add action-item controls to the selected incident: create a new action item and toggle an existing item's status between `open` and `done`.
2. A new action accepts `summary`, optional `owner`, `priority` (`p0`, `p1`, `p2`), and optional `dueAt`. Trim textual fields. `summary` must be 1–120 characters after trimming. A non-empty owner must be one of the selected incident's responders. `dueAt`, when present, must be a valid timestamp at or after the incident's `startedAt`.
3. Creating an action must feel optimistic: the row appears immediately before the network response finishes. The UI must have a stable way to reconcile that optimistic row with the server-created item without briefly showing both or losing the user's draft on an error.
4. Each logical create must use a client-generated request key. Retrying the same request key with the same normalized create payload must return the original successful result and must not create a second action item or increment revisions again. Reusing that request key with a materially different payload must fail clearly.
5. New server action IDs must be unique within the process. The exact ID format is your choice; correctness must not depend on browser-generated temporary IDs becoming the permanent server IDs.
6. Creating an action increments the parent incident revision and global dataset revision exactly once. The new action starts at revision 1.
7. Toggling an existing action is also optimistic in the UI and must send the action revision observed by the client. A successful status change increments that action's revision, the parent incident revision, and global dataset revision exactly once.
8. A stale action toggle must fail without mutation and return enough current server state for the client to reconcile that row. The UI must recover only the affected action/incident state rather than clearing unrelated incident-list state.
9. Prevent unsupported double-toggling of the same action while its prior toggle is still in flight. Other rows may remain usable.
10. Add an action-item status filter (`all`, `open`, `done`) and text search over action summaries. Filtering is client-side over the currently selected incident. An optimistic status change may make a row leave the current filter immediately; if that request later fails, the row must reappear when its reconciled server status matches the filter again.
11. Keep action ordering deterministic after successful reconciliation: priority `p0` before `p1` before `p2`, then earlier non-null `dueAt`, then items without due dates, then action ID as final tie-break.
12. The create and toggle endpoints must support an optional bounded `delay_ms` query parameter so slow-response behavior can be exercised locally without external services.
13. Switching incidents while an action create/toggle request is in flight must not let the older response mutate or render action state for the newly selected incident. The mutation may still complete on the server; the client must reconcile only the matching incident context.
14. A create/toggle network or server failure must keep the last known-good incident list/detail usable, show an actionable error, and preserve enough local intent to retry safely. Do not require a full browser reload.
15. After an action mutation succeeds for the incident still selected, update its visible action list, open-action count, incident revision, and global dataset revision without losing the current severity filter, action-status filter, or search text.
16. Existing incident ordering, severity filtering, detail rendering, severity validation, severity optimistic concurrency, and revision behavior must continue to work.

## Constraints

- Keep the existing TypeScript + Node.js + browser ES-module stack and dependency-free setup.
- Keep state in one process and in memory; no database, queue, websocket service, auth provider, or external API.
- The backend remains authoritative for permanent action IDs, validation, revisions, and idempotency outcomes.
- Do not solve the feature by forcing full-page reloads after every mutation.
- You may add service/store methods, routes, shared contracts, frontend state/actions, and focused tests.

## Out of scope

- Authentication/authorization.
- Multi-process or distributed locking.
- Persisting state across server restarts.
- Real-time push/websockets or polling for other responders' changes.
- Editing action fields after creation; only creation and status toggle are required.
- Deleting actions.
- Visual polish beyond a clear usable workflow.

## Setup / run

```bash
npm run start
```

Open `http://localhost:8080`.

## Tests / build

```bash
npm test
npm run build
```

The existing tests cover current behavior only. Add focused tests for the new behavior you consider highest risk.

## 60-minute interview instruction

You have **60 minutes**. Treat this as an AI-assisted live coding interview. Inspect the current data model, revision behavior, API boundaries, shared types, and client state before changing code. Implement incrementally and verify both ordinary and delayed/error paths.

A polished UI that duplicates creates, loses optimistic state, overwrites stale actions, or corrupts the selected incident when responses complete out of order should score poorly. Prioritize correctness and observable verification over cosmetic completeness.
