# CaseFold — HARD 60-minute AI-assisted full-stack interview

## Context

CaseFold is a customer-support operations console serving three SaaS organizations. Support agents open cases for customer accounts. Each case has a status, a priority, searchable subject, tags, internal note, optimistic revision, and a timeline of external/customer/agent activity. Separate cases sometimes refer to the same underlying customer problem after two employees contact different support channels.

## Existing behavior (already working)

The starter is a **Go 1.22+ standard-library HTTP server** with in-memory domain state and a dependency-free browser JavaScript frontend. Operators can switch organizations, search cases, filter by status, paginate, inspect detail and timeline, and edit internal notes. Cases are sorted by case ID, and list `total` counts **before** pagination. Notes are trimmed; saving unchanged text preserves revision, but stale edits return 409 with authoritative case information. Cross-organization case details return 404. Late list/detail responses cannot overwrite a newer selection. **Preserve these behaviors.** State resets when the process restarts.

## Supplied data

`fixtures/workspace.json` contains three organizations, eight customers and fifteen support cases. Cases include timeline records with externally supplied activity identifiers, timestamps, authors, text, and overlapping customer conversations. IDs and casing matter. Inspect records before coding, particularly cases opened through different channels for the **same customer**. `internal/workspace/` owns the current domain model; `internal/httpapi/` provides the API; `web/` contains the working browser console; tests cover current behavior.

## Customer/business problem

Two agents may unknowingly work on separate cases describing the same incident. A support lead needs to consolidate one case into another while retaining the complete trustworthy activity history, without confusing two customers or losing another agent's edits. Activity from a CRM integration sometimes appears in both cases, and sometimes the same external identifier has contradictory contents. A merge may succeed but its response may be lost; repeating the request must not consolidate twice. The user interface must recover when either case changes while a support lead is preparing a merge.

## Primary feature request

**Add ONE end-to-end duplicate-case consolidation workflow.** From the browser, select a source case and another case in the same organization, consolidate the source into the chosen canonical target, and show the authoritative merged target with an auditable receipt. Implement the necessary HTTP contract, domain updates, browser interactions, and focused verification. The starter does **not** implement consolidation.

## Acceptance criteria (observable behavior)

1. Add `POST /api/cases/:sourceId/merge` receiving JSON `{orgId,targetId,expectedSourceRevision,expectedTargetRevision,requestKey}`. The two expected revisions are nonnegative JSON integers. `requestKey` must be 8–64 ASCII letters, digits, `-`, or `_`. Return an authoritative receipt `{requestKey,sourceId,targetId,sourceRevision,targetRevision,mergedActivityCount,duplicateActivityCount,priority,tags}` plus current canonical target information. A successful non-replayed consolidation increments **both affected case revisions exactly once**.
2. Source and target must be different existing cases belonging to the selected organization **and the same customer ID**. Source may be `open`, `pending`, or `resolved`; target must be `open` or `pending`. Unknown or cross-organization case IDs return 404 without exposing details. Cross-customer attempts return 400. Never mutate a case on validation failure.
3. On success the target remains the chosen canonical case: preserve its ID, customer, organization, subject, current status and internal note. **Priority becomes the stronger of the two** according to `high > medium > low`; target tags become the **sorted, unique union** of both sets. The source becomes `merged` with an exposed `mergedInto` target ID; its original timeline and note remain readable but cannot be edited. Existing target internal notes and timeline must not be silently lost.
4. Construct the canonical target timeline from both cases. Activity identity is `id`. Identical IDs with **identical canonical** `{id,at,actor,text}` count once. If two records share an ID but disagree in any field, return HTTP 409 with a meaningful conflict and **no mutations**. Sort the canonical timeline by RFC3339 instant ascending and then activity ID lexicographically. Deterministic results must not depend on which case was read first or fixture event ordering. `mergedActivityCount` is the target timeline length after consolidation; `duplicateActivityCount` is the number of discarded identical repeated occurrences. Do not rewrite or erase activity provenance fields.
5. A merged case must be absent from normal case directory results, including status `all`, but remains addressable by case ID with its `status`, `mergedInto`, original note and activity. A normal note edit on a merged source must return 409 without mutation. The total list count and pagination must reflect these changes correctly. A source already merged, or a target already merged, cannot participate in a new merge (except for an identical retry described below).
6. `requestKey` identifies an attempted merge within an organization. An identical logical retry must return the **original receipt and canonical-target snapshot from the successful operation** even after unrelated edits to either case or a changed case list. Reusing a key with any different field must return 409 without mutation. Scope receipt lookup to the organization and verify source/target visibility **before** disclosing a stored receipt. Make the state change and receipt durable together for the lifetime of the server process.
7. A fresh merge with stale `expectedSourceRevision` **or** `expectedTargetRevision` returns 409 with useful current-case information; an internal-note update must invalidate an outdated merge. Two concurrent merges involving a case must not both succeed. Parsing or state errors must not leave one half of a pair updated.
8. In the browser, enable choosing a canonical target for the selected source, display its relevant customer/priority/status and save revisions, and perform the merge. Handle validation, stale 409 and uncertain network failures without silently losing the selected source/target. For an uncertain failure, retry the **same** key and original payload; for an actual conflict, refresh authoritative details before a new attempt. On success, refresh directory counts and selected detail without reloading the page, select the canonical target and ignore late responses for the previous selection or organization.
9. Preserve directory search/filter/pagination, note editing, organization isolation, and stale-response protections. Add focused API/domain tests, including repeated requests, failures that do not mutate, merged-case visibility, and consistency after unrelated note edits.

## Constraints

- One Go process with concurrent HTTP handlers; use only the standard library and existing fixture format. No database, Redis, queue, external CRM, LLM, or third-party frontend framework required.
- Production may have 100,000 cases, 20,000 activity records per case, and repeated merges. Do not rely on polling, global rescans of all customer history for each merge, or a browser-calculated canonical timeline.
- All server-owned state is authoritative. A client may not submit arbitrary canonical timeline data or priority overrides.
- Validate RFC3339 timestamps as instants; two timestamps with different offsets may represent the same instant for ordering, while their original strings remain unchanged in output.
- The task is designed for a strong 60-minute implementation with reasonable prioritization. Document any deliberate tradeoffs in your walkthrough.

## Out of scope

Authentication provider, distributed multi-process consistency, permanent disk persistence, undoing a completed merge, fuzzy NLP duplicate detection, merging across customers or organizations, arbitrary chained merges of previously merged sources, and visual polish.

## Setup and running

Requires Go 1.22+; Python 3 is used by the fixture smoke verification script, and Node.js is optional for the JavaScript syntax check.

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
bash scripts/run.sh
```

Open http://localhost:8080. The app should already work before your changes. For a manual API smoke check:

```bash
curl 'http://localhost:8080/api/cases?org=northstar&status=all&offset=0&limit=6'
```

## 60-minute AI-assisted interview instruction

You have **exactly 60 minutes**. Claude Code, Codex, ChatGPT or another AI assistant is allowed and encouraged. Explore existing behavior and fixtures before choosing an approach. Implement one coherent vertical slice across domain, HTTP and UI; verify it with the provided scripts and your own targeted tests. Be ready to explain assumptions, correctness, concurrency/retry handling, complexity, unimplemented edge cases and the tradeoffs behind your design. The intended implementation is **not** supplied.
