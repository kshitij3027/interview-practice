# QueuePulse — HARD One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

QueuePulse is the operations layer for a large customer-support platform. Each work queue has a known open-item count at the beginning of an immutable reporting horizon. During the horizon, events add work to the queue or remove completed work. Operations frequently asks historical questions such as: **“Between these two instants, when did this queue first exceed its staffing limit, and what was the highest backlog in that window?”**

The current prototype replays a queue's entire event history independently for every request. That is fine on a tiny sample and unusable on production snapshots with tens of millions of event revisions and millions of historical queries.

You are given one immutable snapshot. Build the in-process resolver used by the operations API tier. The observable behavior is exact; the technical approach is yours.

## Supplied data

### `fixtures/queues.csv`

Each row contains `queue_id`, `snapshot_start`, and `opening_backlog`. The opening backlog is the integer number of open work items immediately before `snapshot_start`.

### `fixtures/events.csv`

Each row contains `event_id`, positive integer `revision`, `queue_id`, `occurred_at`, signed integer `delta_items`, and `state` (`posted` or `voided`). Rows are not guaranteed to be ordered.

A logical `event_id` may have multiple revisions because upstream systems can correct a count, move an event to a different timestamp, or void it. **Only the highest revision in the snapshot is effective.** If that highest revision is `voided`, the logical event contributes nothing. Lower revisions are superseded and must not also contribute.

Exact duplicate rows for the same `(event_id, revision)` are harmless replay deliveries. Reusing the same `(event_id, revision)` with different contents is invalid snapshot data. All revisions of one `event_id` must refer to the same queue.

### `fixtures/queries.csv`

Each row is one independent request containing `query_key`, `queue_id`, inclusive `start_at`, exclusive `end_at`, and integer `limit_items`. Output must preserve query-file order. One bad request must not stop later requests.

## Backlog and time semantics

All timestamps are compared as instants. Different RFC3339 offsets that identify the same instant are equivalent.

At any instant `t`, backlog is:

`opening_backlog + sum(delta_items of every effective posted event with occurred_at <= t)`

If several effective events occur at the same instant, treat their deltas as one simultaneous net change. There is no observable intermediate backlog between rows at the same instant.

A query window is `[start_at, end_at)`.

For each valid query:

1. Evaluate backlog at `start_at` after applying every effective event at or before that instant.
2. Then consider each later distinct effective-event instant `t` where `start_at < t < end_at`, after applying all events at `t`.
3. These points are the observable checkpoints.

The **first overload** is the earliest checkpoint whose backlog is strictly greater than `limit_items`.

The **maximum backlog** is the largest checkpoint backlog in the window. If the same maximum occurs at several checkpoints, report the earliest such instant.

A window with no event timestamps inside it still has the `start_at` checkpoint.

## Output contract

A successful request emits `status: "resolved"` plus `overloaded`, `overload_at`, `backlog_at_overload`, `maximum_backlog`, and `maximum_at`. Timestamps must be normalized to UTC with a `Z` suffix. Malformed query values produce a query-level `status: "invalid"` result. Unknown queue IDs are query-level errors, not snapshot errors.

## Acceptance criteria and traps

- Emit exactly one result per query line, in input order.
- Results must not depend on CSV row order, revision order, map iteration order, or process hash behavior.
- Highest revision wins before the queue timeline is built; superseded revisions never also contribute.
- A highest revision in state `voided` removes the logical event entirely.
- Corrected revisions may move an event to a different timestamp or change its delta.
- Exact duplicate `(event_id, revision)` rows deduplicate; conflicting duplicates fail snapshot validation.
- Reusing one logical event ID across queues fails snapshot validation.
- Same-instant effective events are applied atomically as one net delta.
- `start_at` is inclusive and evaluated after events exactly at start; `end_at` is exclusive.
- A backlog exactly equal to `limit_items` is **not** overloaded.
- If backlog is already above the limit at `start_at`, first overload is exactly `start_at` even if the causing event happened earlier.
- Maximum ties use the earliest checkpoint instant.
- RFC3339 offsets representing the same instant compare equal.
- `start_at` must be at or after the queue's `snapshot_start`; `end_at` must be strictly later than `start_at`.
- Integer query fields must reject booleans and numeric strings.
- Duplicate queue IDs, malformed timestamps, empty identifiers, unsupported states, non-positive revisions, negative opening backlogs, or events before a queue's snapshot start fail snapshot validation.
- Diagnostic logging belongs on stderr; stdout must remain JSONL.

## Production constraints

Design for approximately 60,000 queues, 50 million raw revision rows, 35 million effective events, and 3 million historical queries against one immutable 90-day snapshot. A few hot queues have 2–5 million effective events while most are small. Query windows overlap heavily and arrive in arbitrary order; `limit_items` varies per request. Memory budget is about 1.5 GB and target p95 is below 20 ms for a typical query after preprocessing.

A production-credible solution should not replay from `snapshot_start` per query, scan every checkpoint in every query window, or expand the horizon into a dense time grid. The sample is small enough that a linear scan may appear correct; your design must still have a defensible path to the production shape.

## Expected deliverable

Implement the historical overload capability behind `BacklogResolver.resolve_all(...)` in `queuepulse.py`, plus supporting code as needed. Add focused tests for the risks you consider most important.

Be ready to explain what you preprocess once, how revisions/voids are resolved, how backlog at arbitrary starts is obtained, how the first above-limit checkpoint and range maximum are found without scanning huge windows, startup/per-query/worst-case complexity, memory behavior for hot queues, and what guarantee you would relax if tighter latency or memory targets required it.

## Verification / run commands

Python 3.11+ and the standard library are sufficient.

```bash
bash scripts/test.sh
bash scripts/build.sh
bash scripts/verify.sh
```

Fixture validation is equivalent to:

```bash
python3 queuepulse_cli.py validate --queues fixtures/queues.csv --events fixtures/events.csv --queries fixtures/queries.csv
```

After implementation:

```bash
python3 queuepulse_cli.py resolve --queues fixtures/queues.csv --events fixtures/events.csv --queries fixtures/queries.csv
```

## Scope / out of scope

In scope: immutable snapshot loading, revision resolution, exact historical backlog semantics, deterministic query results, query-level validation, focused tests, and production-scale reasoning.

Out of scope: live ingestion while a run executes, mutating queue events, workforce scheduling, persistence, distributed coordination, authentication, notifications, or UI work.

## 60-minute AI-assisted interview instruction

You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or similar tools as you would on the job. Inspect the repository and fixtures yourself first. Restate the revision, checkpoint, and boundary semantics, implement incrementally, verify the highest-risk cases, and reserve time to defend correctness and scaling. A one-shot implementation that only scans the sample correctly is intentionally not a complete solution.
