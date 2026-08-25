# POST-PRACTICE ONLY — Interviewer Notes

**Candidate: do not read this before completing the exercise.**

## Intended solution outline

A strong solution introduces server-owned sync state containing the physical feed cursor, a globally processed-event-ID set, and an idempotency/request-key result map. The sync operation should first validate request-level concurrency (`expected_cursor`) and request-key reuse, then slice the next physical feed rows. Parsing/validation produces row records without mutating cases.

Within that fixed batch, valid non-duplicate known-case events should be grouped by canonical case and evaluated in deterministic `(source_version, event_id)` order. Each event is validated as an atomic unit before any of its fields are changed. Stale versions become non-mutating outcomes. Successful events update CRM-owned fields, external version, and case revision once while leaving internal notes intact.

After the fixed batch is processed, the server advances the feed cursor by the number of physical rows consumed, stores the complete successful sync result under the request key, and returns row-level outcomes plus affected cases. The exact locking mechanism can remain simple because the exercise is single-process, but request-level cursor validation and mutation should share one critical section conceptually.

The client should retain its current filters, selected case ID, and batch size, disable duplicate submission while a sync is pending, reconcile returned/refresh state after success, and on stale cursor fetch the newest case/cursor state before allowing another attempt. Transient errors should not blank the current view.

## Subtle traps / hidden checks

- **Physical cursor vs valid-event cursor:** malformed JSON and duplicates still consume feed positions after a successful sync.
- **Ordering scope:** reorder valid events for the same case by source version inside the batch; do not globally reorder physical rows for cursor purposes.
- **Duplicate timing:** an event repeated later in the same batch should be duplicate even if file order differs from evaluation order.
- **Atomic event validation:** `{status: "resolved", priority: "critical"}` applies neither field.
- **Version chain:** if versions 6 and 5 arrive in that file order for a case currently at 4, deterministic evaluation should apply 5 then 6, with two case-revision increments.
- **Same version:** tie order must be deterministic. Once the first same-version event applies, the second becomes stale because `source_version <= external_version`.
- **Unknown case:** report error; do not add the event ID to the successfully processed global dedupe set unless the candidate clearly defines and justifies a different non-retryable policy. Hidden checks should follow the README wording: globally duplicate means successfully processed event.
- **Invalid event:** do not mark its ID as successfully processed; it can appear again later with corrected payload and should be eligible then.
- **Owner clear:** missing owner means unchanged; explicit null means clear.
- **Idempotent retry:** same key/same parameters must return the exact logical prior result even though current cursor has advanced.
- **Key collision:** same key with a different batch size or expected cursor is an error, not a new sync.
- **Stale cursor:** reject before parsing/processing rows or changing dedupe/cursor/case state.
- **No work:** distinguish empty feed from transport/server failure.
- **Regression:** notes and note revisions must survive CRM merges untouched.

## Expected prioritization

1. Model feed state/cursor and deterministic pure-ish event validation/ordering.
2. Implement sync service with request-level stale/idempotency handling.
3. Add focused backend tests for ordering, duplicates, atomic invalidity, and cursor behavior.
4. Add the API route and minimal UI action/summary.
5. Add stale-cursor UI recovery and extra verification.

A candidate who secures backend semantics and a rough usable UI should score better than one who spends most of the hour polishing visuals while cursor/idempotency semantics are unsafe.

## Likely failure modes

- Processing strictly in file order and marking version 5 stale after version 6.
- Advancing cursor only for valid events.
- Dedupe scoped only to one request.
- Marking malformed/unknown events as permanently deduped without considering retry semantics.
- Partially applying a multi-field event before discovering another invalid field.
- Trusting a browser-supplied new cursor.
- Checking stale cursor after applying some rows.
- Retrying a successful request by processing the now-next batch.
- Incrementing case revision once per changed field rather than once per applied event.
- Clearing selection/filters or blanking current data on any sync error.
- Accidentally replacing or dropping internal notes while merging CRM fields.

## What to inspect after the hour

Look for a crisp distinction between physical feed position and logical event outcomes, deterministic per-case evaluation, explicit event-level atomicity, request-level mutation boundaries, durable-in-process idempotency state, and evidence that the candidate tested stale/retry paths. Also verify that the existing note workflow still passes unchanged.
