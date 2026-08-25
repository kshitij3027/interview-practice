# CaseBridge — HARD One-Hour Full-Stack Interview Exercise

## Context

CaseBridge is an internal support-operations workspace for a B2B SaaS company. Support engineers use it to inspect customer cases, filter their queue, and add internal notes while coordinating with a separate CRM.

The starter application already works. It uses a dependency-free Python 3 HTTP API, an in-memory domain store loaded from JSON fixtures, a browser ES-module frontend with explicit client state, and existing tests for current case/note behavior.

## Existing behavior

- The dashboard lists support cases with status, priority, owner, customer, and a per-case revision.
- Cases can be filtered by status and priority.
- Selecting a case shows its current details and internal notes.
- An operator can add a non-empty internal note to the selected case.
- Adding a note uses the case revision for optimistic concurrency; stale note writes are rejected.
- Notes increment the case revision exactly once and do not change CRM-owned fields.
- Restarting the backend resets state from fixtures.

## Customer/business problem

A partner CRM delivers case updates as an append-only JSONL feed. Operations currently asks engineers to refresh cases manually after CRM changes, so owner/status/priority changes can lag behind for hours.

The feed is not perfectly clean: events can be duplicated, rows can be malformed, several updates for the same case can arrive out of order, customer identifiers have inconsistent casing/whitespace, stale CRM versions can appear after newer ones, and an event can contain a mix of valid and invalid field values.

A representative feed is provided in `fixtures/inbound_updates.jsonl`.

## Primary feature request

**Add a cursor-based “Sync CRM updates” workflow that processes the next feed batch into canonical case state with deterministic version semantics, partial-error reporting, retry safety, and race-safe client reconciliation.**

## Acceptance criteria

1. Add a backend sync API and a corresponding UI action that processes the next batch of feed rows after the server's current cursor. The batch size must be configurable from 1–10 rows; default to 5.
2. The feed is append-only and cursor positions are based on physical JSONL row positions, including malformed or duplicate rows. A successful sync of N available rows advances the cursor by exactly N rows, even when some rows do not mutate a case.
3. Valid events contain `event_id`, `case_ref`, `source_version`, and `changes`. `event_id` and `case_ref` must be non-empty strings; `source_version` must be a positive integer; `changes` must be an object. Malformed rows/events must be reported individually without aborting other rows in the batch.
4. Resolve `case_ref` by trimming surrounding whitespace and comparing case-insensitively with each case's `external_ref`. Unknown cases must be reported as row-level errors, not created implicitly.
5. Duplicate CRM events are identified globally by `event_id`. An event ID that has already been successfully processed in an earlier sync, or that repeats later in the same batch, must not mutate state twice. Its outcome must be distinguishable from a malformed/stale event.
6. For each case, valid non-duplicate events in the batch must be evaluated in ascending `source_version`, regardless of feed/file order. When two events for the same case have the same `source_version`, break the tie deterministically by `event_id` lexicographically.
7. A case stores its latest applied `external_version`. An event whose `source_version` is less than or equal to the case's current external version at the time that event is evaluated is stale: report it and do not mutate CRM-owned fields or revisions.
8. Supported CRM-owned changes are `status`, `priority`, and `owner_email`. Missing keys leave the field unchanged. `owner_email: null` explicitly clears the owner. Reject the entire event (without partially applying any of its fields) if a supplied value is invalid. Valid statuses are `open`, `pending`, `resolved`; valid priorities are `low`, `normal`, `high`, `urgent`; a non-null owner must be a non-empty string containing `@`.
9. Each successfully applied CRM event updates all supplied valid CRM-owned fields atomically, sets `external_version` to that event's `source_version`, and increments the case revision exactly once. Internal notes must remain unchanged.
10. The sync request must include the feed cursor the client observed plus a client-generated request key. If the expected cursor no longer matches the server cursor, reject the whole sync before processing any row so two operators cannot silently consume overlapping batches.
11. Retrying the same request key with the same expected cursor and batch size after a successful sync must return the same prior sync result without advancing the cursor or mutating cases again. Reusing a request key with different sync parameters must return a clear non-2xx error.
12. A successful response must expose the old/new cursor, whether more feed rows remain, per-row outcomes, a useful batch summary, and enough updated case information for the client to reconcile visible state.
13. If the feed has no rows after the current cursor, return a distinguishable no-work result that does not change cursor or case state and that the UI presents as such rather than as a generic failure.
14. While a sync is in flight, prevent accidental double submission. After success, keep the current filters and selected case, reconcile the case list/detail without a browser reload, and show a concise applied/stale/duplicate/error summary.
15. If the backend rejects the sync because the client's cursor is stale, refresh the current server cursor/cases, preserve the user's selected batch size and filters, and make retrying straightforward. A transient request failure must leave the last known-good case data visible.
16. Existing case filtering, case detail, internal notes, note validation, and note stale-write behavior must continue to work.

## Constraints

- Keep the existing dependency-free Python + browser ES-module stack.
- Keep state in one process and in memory; no database, Redis, queue, auth provider, or external API.
- Treat the backend as the source of truth for feed cursor, deduplication, version ordering, and merge semantics.
- Do not rewrite the app into a framework.
- You may add service/domain modules, routes, client state/actions, and focused tests.
- Keep the implementation interview-sized.

## Out of scope

- Polling on a timer or background workers.
- Writing updates back to the CRM.
- Creating cases that are unknown locally.
- Persisting cursor/deduplication state across server restarts.
- Authentication/authorization.
- Multi-process/distributed coordination.
- Visual design polish beyond a clear usable workflow.

## Setup / run

```bash
./scripts/test.sh
./scripts/build.sh
./scripts/run.sh
```

In another terminal:

```bash
python3 -m http.server 5173 -d web
```

Open `http://localhost:5173`.

## Tests / build

```bash
./scripts/test.sh
./scripts/build.sh
```

Existing tests cover current behavior only. Add feature-specific tests based on the requirements; there are intentionally no TODOs or starter tests that encode the sync solution.

## 60-minute interview instruction

You have **60 minutes**. Treat this as an AI-assisted product-engineering/FDE live build. Inspect the existing data model, API flow, frontend state, and feed fixture before changing code. Identify the highest-risk semantics, implement incrementally, and verify both the core path and at least a few failure/retry cases.

A visually complete sync button that mishandles cursor races, event ordering, duplicates, atomic validation, or retry behavior is not a strong solution. Prioritize correctness, observable verification, and time management.
