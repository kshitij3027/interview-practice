# POST-PRACTICE ONLY — ServiceClock interviewer notes

**Evaluator-only material. Do not show or disclose before the interview.** The candidate starter must not contain this document or its contents anywhere in its history.

## Underlying problem structure

This is a time-varying state machine crossed with a weighted business-time calendar. The operator wants an event-sourced SLA budget integral (active time intersected with site working windows), plus a retry-safe revisioned state transition. It is *not* simply `now - openedAt` and is not naturally a graph-shortest-path exercise. The candidate should infer time-segment reconstruction, calendar intersection, indexed history, and transactional state changes. The challenge is cross-layer domain reasoning under constraints, not a named algorithm.

## Strong approaches

1. **Index/normalize events once**: parse offset-aware timestamps, verify minute precision and allowed state, group records by `eventId`; repeated canonical-equivalent payload is one record; conflicting canonical payloads quarantine the whole ID even if the conflict appears after a seemingly valid copy. Unknown job, earlier-than-open, invalid state/time records should not poison other jobs. Sort valid per-job events by `(occurredAt UTC, eventId)` and apply a documented state policy. A strict transition policy can ignore illegal/no-op state edges while preserving terminal resolved; alternatively return an explicit data-quality warning and exclude ambiguous records. Do not allow events after terminal resolution to restart the clock. Index jobId -> canonical event timeline, precomputing activity segments if useful. For example, `ev-conflict` is reused with incompatible states on `WO-104` and must not affect that job.
2. **Calendar windows**: use `zoneinfo.ZoneInfo(site['timeZone'])`, build each relevant local calendar day's `[openLocal, closeLocal)` mapped into offset-aware UTC instants, skip excluded weekday/holiday dates. Intersect UTC active intervals with those windows; add integer minutes. Enumerating local *days* is acceptable and usually efficient; minute-by-minute iteration across years is not. For very long queries, cache week summaries or precompute day boundaries/prefix sums. Holiday and time zone are site scoped; local Sunday is not the same as UTC Sunday. Half-open end means a start at closing time earns zero. At a DST transition, resolve nonexistent/ambiguous local boundaries with an explicit policy or, for this fixture, note site opening windows avoid transition hours.
3. **As-of evaluation**: begin at `openedAt`, initial `in_progress`; apply authoritative events effective at/before `asOf`, closing each preceding active segment before the new event. Paused segments accrue zero. Resolved is terminal, not a pause. Use event ID lexical tie to define same-instant final state. Return integer charged minutes, `remaining=max(0,budget-charged)`, `overdue=max(0,charged-budget)`. For active jobs with charge at/over budget, return `breached`; paused jobs only show `paused` if not yet breached; resolved jobs are `met` if charge<=budget, else `missed`. As-of earlier than a future event must not leak that event's state.
4. **Deadline**: when the cumulative charge first reaches the budget within an actual active segment, record its exact UTC instant (including when it is a window end). If not reached and still active at as-of, project future calendar windows with no additional pause; if paused with remaining budget or resolved before budget, `dueAt=null`. For a resolved job that exceeded budget, preserve actual crossing instant rather than resolving time. Compute only as much future calendar as needed; reject impossibly long projections or explain bounding policy.
5. **Atomic transition**: the same store lock used for notes should enclose idempotency lookup, job revision precondition, legal-state check, server time/order validation, append event, revision+dataset increments and receipt caching. Identity key `(account, requestKey)` maps to canonical intent `(jobId,to,expectedRevision)` and immutable deep-copied successful receipt. Check an existing successful replay *before* stale checks. A key collision 409 must not mutate. Failed requests must not reserve key. The server assigns unique event IDs (monotonic counter or UUID) and `occurredAt` at UTC minute. If now precedes last canonical event, reject. Cross-account ID always 404. No-op transitions should not consume keys. Intervening notes cause a stale transition; other jobs' revisions should not.
6. **UI**: preserve list/detail rendering and active search; extend detail with SLA read/display and state-action buttons based on authoritative job status. Invalidate pending operation on selection/account switch, guard asynchronous results with epoch+job+account, disable duplicate submits. Retain the exact intent/key on timeout and retry; a 409 should expose the stale condition and trigger explicit refresh/new intent, not silently reuse a stale revision. After success refresh authoritative detail/list/SLA.

## Intended complexity / scale

- Normalization/indexing: expected O(E) grouping and O(E log E) sorting total (or sum per-job sorts), space O(E+J). Per-job lookup should be O(1) to find the timeline, not O(E). Rebuilding the canonical feed from scratch on every read is a likely failure.
- For job with k relevant events and d local calendar days across considered segments: O(k log k + d) without preindex, O(k+d) after sorting; constant-time lookups per site calendar date aside from zone calculations. A cached prefix could accelerate repeated same-job/as-of reads; update/invalidations must happen after transitions.
- A full minute-step computation over the 500k-event production feed or years of calendar history is not acceptable. A bounded day-based walk is a defensible 60-minute solution; production-grade caching is optional if complexities are clear.
- Single-process `RLock` is sufficient for exercise atomicity; it does not imply real distributed transactions.

## Why naïve approaches fail

- `(asOf-openedAt)` ignores customer waiting, weekends, public holidays and daylight saving.
- Sorting by ingestion time, or letting the first delivered duplicate ID win, changes answers when files are reordered.
- Per-minute advancing through multi-year timelines can exceed latency budgets and boundary precision.
- Comparing ISO strings instead of UTC instants fails for offset-equivalent timestamps.
- Treating pauses as if they restart the SLA budget gives customers extra time; treating terminal resolution as a pause could allow a later reopen.
- Computing dueAt from local start without projecting over a holiday can yield a calendar-closed deadline.
- Validating revision before checking a successful retry returns stale 409 after the first request actually succeeded.
- Frontend generating a fresh request key on a timeout can double-apply if server already committed.
- Non-atomic check+append+revision makes concurrent requests double-transition.
- Reading status from fixture rather than reconstructed historical state can produce inconsistent as-of answers.

## Subtle traps / hidden checks

1. `WO-101` spans the U.S. fall DST transition (Nov 1, 2026) and has a waiting period across local days. Verify local weekday semantics, not a 24h daily arithmetic shortcut.
2. `WO-102` pauses during an otherwise open business window; the waiting time cannot be charged.
3. `WO-103` is resolved after pause/resume, with a deadline that may be reached before the resolution; check `met`/`missed` at the correct as-of.
4. `WO-104` has a conflicting `ev-conflict` ID; neither copy should change state. An implementation that uses last-write-wins by ingestion order fails.
5. `WO-204` has distinct same-timestamp events where lexical event ID ordering chooses which state persists.
6. `WO-205` has event receipt time far later than effective time; time-order by occurredAt is mandatory.
7. A holiday on Nov 5 is specific to `LA1` and `LON1`, not the Chicago or New York site. Test site isolation.
8. Two UTC instants can land on different local dates across sites, including during DST. Test opening exactly, closing exactly, touching pauses, and full-day closure.
9. An event after asOf must not affect an earlier snapshot; an event at asOf takes effect immediately but contributes no time before itself.
10. Check at exactly SLA budget: still active => `breached`, resolved at budget => `met`, overdue=0.
11. A duplicate key with altered to/job/revision must be 409 even if same account; retry response must be byte-identical in content after subsequent updates.
12. A stale revision caused by note editing must reject without activity append or dataset change. Two near-concurrent transitions using same revision: only one success.
13. Invalid timezone or malformed offsetless timestamp should be explicit error or isolated bad record, not local-machine interpretation.
14. Losing network response after a successful transition must leave UI able to retry with same key and show actual final state; old detail responses after account switch must not repaint the wrong customer.

## Defensible alternatives

- Precomputing event-derived active segments or computing them on demand from a sorted per-job index are both defensible. Cache cost and invalidation must be described.
- Bisecting sorted event instants for as-of truncation is a good improvement but not mandatory for the compact fixture.
- Static schedule windows per local day versus weekly templates plus holiday exceptions are both valid. A date-lookup cache is reasonable.
- A conservative data-quality error response for a job with illegal transitions may be defensible if it is deterministic, account-isolated and documented. Silent arbitrary state fixes are weaker.
- Frontend may use direct DOM updates or a small explicit store; no React build is required.
- A prototype may compute per-job windows daily without full optimized indexes if it documents complexity and avoids per-minute work.

## Likely AI-agent failure modes

Generated code often (a) uses `datetime.replace(tzinfo=...)` incorrectly in ambiguous local hours, (b) counts every weekday hour without excluding site holidays, (c) uses an inclusive close window, (d) trusts `job.status` instead of historical as-of state, (e) deduplicates only adjacent event IDs, (f) loses account scope for request keys, (g) uses `Date.now()` as the sole authority, (h) returns a new success receipt for retries, or (i) adds UI buttons but forgets to refresh existing note and list revisions. Verify the candidate actually inspected `activity.jsonl` rather than implementing solely from README.

## Discovery and suggested 60-minute prioritization

- Minutes 0–10: run baseline; inspect fixtures, API, store, client; articulate event semantics and key traps.
- Minutes 10–30: implement canonical feed and basic SLA calendar computation, a read endpoint, focused tests against a pause, opening boundary, and holiday.
- Minutes 30–45: implement atomic transition and immutable retry receipts, test stale keys and revisions.
- Minutes 45–55: add UI status and state controls, reconcile list/detail/SLA, preserve retry key.
- Minutes 55–60: build/test/smoke run, walkthrough known limitations and complexities.

A different sequence is acceptable if the candidate clearly prioritizes a correct vertical slice.

## Walkthrough inspection points

Ask the candidate to identify the source-of-truth revision, show before/after on a pause across a weekend, compare the `WO-104` conflicting ID handling, calculate a deadline through a holiday, demonstrate a note-change stale transition, retry a successful key after another edit, explain how `currentDetail`/selection epochs prevent stale UI repaint, and estimate runtime for 100k jobs plus half a million historical rows. Inspect what was actually tested; do not infer correctness from generated explanations alone.
