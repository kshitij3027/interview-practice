# RedactDesk — HARD One-Hour Full-Stack Interview Exercise

## Context

RedactDesk is an internal compliance-review console used by a financial-services operations team before documents are shared outside the company. Reviewers inspect page text, see existing redactions, and make occasional manual redactions when they spot sensitive information.

The starter application already works. It uses a Java 21 HTTP API with an in-memory fixture-backed domain store, a dependency-free browser ES-module frontend with explicit client state, and existing tests for the current manual-redaction workflow.

## Existing behavior

- The dashboard lists documents ordered by title, then document ID.
- Reviewers can filter documents by `reviewing` or `approved` status.
- Selecting a document shows its page text, revision, and current redactions.
- A reviewer can add one manual redaction to a `reviewing` document using a zero-based half-open range `[start, end)` on a page.
- Manual redactions require a valid category (`personal`, `financial`, or `credentials`) and a non-empty note.
- A manual redaction may not overlap an existing redaction on the same page.
- Manual writes use the document revision for optimistic concurrency. A stale write fails without mutation.
- A successful manual redaction increments the document revision and global dataset revision exactly once.
- Approved documents are locked against manual redaction.
- Restarting the server resets fixture-backed state.

## Customer/business problem

A document-scanning service now produces candidate redaction ranges before a reviewer opens a document. Representative output is checked in at `fixtures/suggestions.csv`. The suggestions are intentionally imperfect: some are duplicates, some overlap one another, some overlap existing manual redactions, and some point at invalid page/range data.

Reviewers want a fast way to preview what the scanner suggestions would become after policy normalization and then apply the reviewed batch safely. They cannot risk modifying existing manual redactions, applying a stale preview after another reviewer edits the document, or producing different redaction geometry just because the scanner changes row order.

All supplied page text is ASCII. Offsets in the fixtures are zero-based half-open character ranges `[start, end)` into the corresponding page text.

## Primary feature request

**Add a machine-suggestion preview-and-apply workflow that deterministically normalizes scanner ranges around existing redactions, explains excluded/problematic suggestions, and applies the preview safely with stale-state and retry protection.**

## Acceptance criteria

1. Add UI controls on the selected document for a minimum confidence threshold from `0.00` through `1.00`, a preview action, and an apply action. The scanner data comes from `fixtures/suggestions.csv`; the browser must not be the authoritative source of suggestion rows.
2. Preview is server-authoritative and must not mutate the document. It must use only suggestions for the selected document whose confidence is at least the requested threshold.
3. Suggestion identity is `suggestion_id`. Exact duplicate rows for the same ID count once. If the same ID appears with materially different page/range/category data, preview must report a blocking duplicate-ID conflict rather than choosing one payload based on row order.
4. A suggestion with an unknown page, an empty/non-positive range, an end beyond the page text, or an unsupported category is invalid. Invalid suggestions must be reported individually and must not crash preview or hide otherwise usable suggestions.
5. Existing redactions are authoritative and immutable during this workflow. A machine suggestion must never overwrite, resize, recategorize, or duplicate an existing redaction.
6. A suggestion fully covered by existing redaction geometry creates no new proposed range and must be reported as already covered. A suggestion that only partially overlaps existing redaction geometry contributes only its uncovered characters; clipping may produce more than one fragment.
7. Normalize the remaining proposed machine geometry deterministically per page. When multiple machine fragments cover the same character positions, category precedence is `credentials` over `financial` over `personal`. Lower-precedence geometry survives outside the higher-precedence overlap. Adjacent or overlapping final fragments of the same category must coalesce.
8. The normalized preview must be independent of CSV row order and sorted by page, start offset, end offset, then category. It must include enough counts/detail for a reviewer to distinguish proposed ranges, already-covered suggestions, invalid suggestions, and blocking duplicate-ID conflicts.
9. A preview containing a blocking duplicate-ID conflict is not applyable. Invalid independent suggestions do not by themselves block applying the valid normalized ranges.
10. Preview must capture the document revision and global dataset revision it was calculated from and return an opaque server-generated preview identifier. Apply must reference that server-owned preview rather than trusting client-authored normalized ranges.
11. Apply is allowed only for a still-`reviewing` document. Before any mutation, it must reject if the document revision no longer matches the previewed revision. A stale rejection must apply zero machine redactions.
12. Applying a valid preview creates the normalized machine redactions exactly once, leaves all pre-existing manual redactions byte-for-byte unchanged, increments the document revision exactly once for the logical batch, and increments the global dataset revision exactly once regardless of the number of created ranges.
13. Apply must accept a client-generated request key. Retrying the same key for the same successfully applied preview must return the prior result without creating duplicate redactions or incrementing revisions again. Reusing that key for a different preview must fail clearly.
14. Applying a preview that produces zero new ranges must still be well-defined and retry-safe. It must not fabricate redactions merely to make the operation look successful.
15. The apply endpoint must support an optional bounded `delay_ms` query parameter so stale behavior can be reproduced locally by starting apply, adding a manual redaction through the existing workflow, and letting the older apply finish afterward.
16. While preview/apply is in flight, prevent accidental duplicate submission of that operation while keeping normal document browsing usable.
17. After a successful apply, reconcile the visible document, redaction list, document revision, dataset revision, and document summary without a browser reload. Preserve the current status filter and selected document when it still exists.
18. On stale apply, preserve the reviewer's confidence setting and last preview explanation, refresh current document state, and make re-previewing straightforward. Do not leave the UI appearing as if machine ranges were applied.
19. A transient preview/apply failure must leave the last known-good document and preview visible when available and show an actionable error rather than clearing the review workspace.
20. Existing document ordering/filtering, detail rendering, manual-redaction validation, overlap protection, approved-document locking, optimistic concurrency, and revision behavior must continue to work.

## Constraints

- Keep the Java 21 + browser ES-module stack and dependency-free setup.
- Keep state in one process and in memory; no database, queue, object store, auth provider, websocket service, or external API.
- The backend is authoritative for suggestion data, normalization, preview state, permanent redaction IDs, revisions, and idempotency results.
- You may add domain/service classes, store methods, routes, frontend state/actions, and focused tests.
- Do not replace the starter with a framework or make environment setup the main challenge.

## Out of scope

- OCR or extracting text from actual PDF/image files.
- Editing or deleting existing redactions.
- Reviewer-by-reviewer permissions.
- Persisting previews or redactions across server restarts.
- Distributed locking or multiple backend processes.
- Configurable category precedence.
- Visual PDF rendering or pixel-coordinate redaction.
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

Existing tests cover current behavior only. Add focused feature tests around the correctness risks you consider highest priority.

## 60-minute interview instruction

You have **60 minutes**. Treat this as an AI-assisted live product-engineering interview. Inspect the fixture geometry, current mutation/revision behavior, HTTP boundary, and frontend state before changing code. Choose a correctness-first core path, implement incrementally, and verify both ordinary and stale/retry behavior.

A polished preview that depends on row order, mishandles overlap geometry, mutates manual redactions, or double-applies after a retry should score poorly. Prioritize dangerous invariants and observable verification over cosmetic completeness.
