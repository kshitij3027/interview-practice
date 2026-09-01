# MergeDesk — HARD One-Hour Full-Stack Interview Exercise

## Context

MergeDesk is an internal customer-operations console for a B2B SaaS company. Operations teams use it to inspect customer profiles that arrive from several business systems and to maintain a small amount of locally-owned lifecycle state.

The starter application already works. It uses a Go 1.23 HTTP API, an in-memory domain store loaded from JSON, a dependency-free browser ES-module frontend with explicit client state, and existing tests for current list/detail/status behavior.

## Existing behavior

- The dashboard lists customer profiles sorted by name, then ID.
- Operators can filter the list by customer segment.
- Selecting a customer shows field provenance, external-system IDs, tags, and activity history.
- Operators can change one customer's lifecycle status among `prospect`, `active`, and `paused`.
- Status writes use the customer revision for optimistic concurrency; stale writes fail without mutation.
- Every successful status change increments both that customer's revision and the global dataset revision exactly once.
- Restarting the backend resets state from `fixtures/customers.json`.

## Customer/business problem

Imports from CRM, billing, support, and event systems sometimes create two customer profiles for the same real company. Operations can identify a duplicate pair, but today there is no safe way to consolidate the records. A careless merge could discard a verified field, erase a source-system identifier, duplicate activity, overwrite a newer status edit, or produce different results depending on which record happened to be loaded first.

The sample fixture intentionally contains profiles that exercise realistic overlap and conflict cases.

## Primary feature request

**Add a preview-and-apply customer-profile merge workflow that consolidates one source profile into a chosen survivor with deterministic field/data semantics, blocks unsafe conflicts, and remains atomic and retry-safe when either profile changes after preview.**

## Acceptance criteria

1. Add UI controls that let an operator choose two distinct profiles: a **survivor** that remains after the merge and a **source** that is consolidated into it. The operator must be able to request a merge preview before applying anything.
2. Preview is server-authoritative and must not mutate customer state. The response must include enough categorized detail for the UI to explain what would be kept, combined, deduplicated, or blocked.
3. The survivor's `status` is always preserved. The source status must never overwrite it.
4. For the mergeable contact fields `email` and `phone`, empty values never beat non-empty values. When both profiles have non-empty values, a verified value beats an unverified value; if verification is equal, the field with the later `updated_at` wins; if both timestamps are equal, the survivor's value wins. The preview must show the chosen value and its provenance.
5. Tags are combined after trimming surrounding whitespace and deduplicated case-insensitively. Preserve the survivor's spelling for a tag it already contains; otherwise preserve the source spelling. Output order must be deterministic.
6. External IDs are keyed by namespace (for example `crm`, `billing`, `support`). A namespace present on only one profile is carried forward. If both profiles contain the same non-empty value for a namespace, keep one. If both contain different non-empty values for the same namespace, that namespace is a **blocking conflict** and the merge cannot be applied.
7. Activity is combined by `event_id`. Exact duplicate events count once. If the same `event_id` appears with different `type`, `occurred_at`, or `summary`, report a blocking conflict rather than guessing which payload is correct. The merged activity list must have deterministic ordering by `occurred_at`, then `event_id`.
8. Preview must distinguish blocking conflicts from non-blocking deduplication/selection decisions. An apply attempt for a preview with any blocking conflict must fail without mutating either customer.
9. A successful merge updates the survivor with the previewed contact fields, external IDs, tags, and activities; preserves its existing status and segment; and marks/removes the source so it no longer appears in the normal customer list. The source ID must not silently become a second independent live profile again during that process.
10. The preview must capture the revisions of both profiles and the global dataset revision used to calculate it. Apply must reject the entire merge before any mutation if either profile revision or relevant merge state has changed since preview.
11. Apply must use an opaque server-owned preview identifier. Do not trust the browser to send back a client-authored merged profile or selected field values as the authoritative plan.
12. Apply must also accept a client-generated request key. Retrying the same request key for the same successful preview must return the prior result without applying the merge twice or incrementing revisions twice. Reusing a request key for a different preview must return a clear non-2xx error.
13. On successful apply, increment the survivor revision exactly once, change the source's revision/state exactly once, and increment the global dataset revision exactly once for the logical merge, regardless of how many fields/tags/activities were consolidated.
14. If apply is rejected as stale, the UI must preserve the operator's survivor/source choices, refresh the current profile data/revisions, and make re-previewing straightforward. It must not leave the screen looking as though the merge succeeded.
15. While preview or apply is in flight, prevent accidental duplicate submission of that operation. Transient failures must leave the last known-good customer list/details or merge preview visible when available and show an actionable error.
16. After a successful merge, keep the current segment filter, select/show the surviving profile, reconcile the customer list without a browser reload, and clear only merge state that is no longer meaningful.
17. Existing segment filtering, detail rendering, lifecycle-status validation, optimistic concurrency, and revision behavior must continue to work for non-merged profiles.

## Constraints

- Keep the existing Go + browser ES-module stack.
- Keep state in one process and in memory; no database, Redis, queue, auth provider, or external API.
- The backend is the source of truth for merge decisions and apply semantics.
- You may add domain/service modules, endpoints, client state/actions, and focused tests.
- Do not rewrite the app into a frontend framework or make setup the primary challenge.

## Out of scope

- Automatic duplicate detection or similarity scoring.
- Merging more than two profiles at once.
- Undoing a completed merge.
- Persisting state across server restarts.
- Authentication/authorization.
- Distributed locking or multiple backend processes.
- Visual polish beyond a clear usable workflow.

## Setup / run

```bash
go run ./cmd/server
```

Open `http://localhost:8080`.

## Tests / build

```bash
go test ./...
go build ./...
node --check web/api.js
node --check web/store.js
node --check web/app.js
```

Existing tests cover current behavior only. Add feature-specific tests based on the requirements; there are intentionally no starter TODOs or solution-shaped tests.

## 60-minute interview instruction

You have **60 minutes**. Treat this as an AI-assisted live full-stack interview. Inspect the existing model, store, service, HTTP boundary, frontend state flow, and fixture before making changes. Choose a correctness-first implementation path, add focused verification around the highest-risk semantics, and keep the existing status workflow working.

A polished UI with unsafe merge semantics, client-authored merge authority, stale partial writes, or retry duplication should score poorly. Prioritize a credible end-to-end core path and the most dangerous correctness cases over cosmetic completeness.
