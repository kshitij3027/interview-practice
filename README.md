# GateQueue — HARD One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

An enterprise incident-management platform coordinates remediation runbooks for customers during outages. A runbook is a set of tasks such as isolating a failing dependency, validating data, notifying a partner, or restoring traffic. Some tasks cannot begin until specific prerequisite tasks are complete.

Operators frequently **reopen** previously completed tasks when a verification fails. The event feed is at-least-once and is not guaranteed to arrive in timestamp order. During a live incident, the operations UI repeatedly asks:

> “As of this historical instant, which tasks in this runbook are runnable next?”

The current prototype recomputes every task from scratch for every request. That worked for small customers, but it falls over on large runbooks and long incident histories.

Build the in-process resolver for one immutable snapshot.

## Supplied data

### `fixtures/workflows.csv`

Columns:

- `workflow_id` — globally unique workflow identifier.
- `customer_id` — customer that owns the runbook.
- `name` — display-only label.

### `fixtures/tasks.csv`

Columns:

- `task_id` — globally unique task identifier.
- `workflow_id` — owning workflow.
- `priority` — signed integer; larger values are more urgent.
- `due_at` — RFC3339 timestamp with explicit offset.

Every task belongs to exactly one workflow.

### `fixtures/dependencies.csv`

Columns:

- `task_id`
- `prerequisite_task_id`

A row means `task_id` is runnable only while `prerequisite_task_id` is complete.

Dependencies must remain inside one workflow. Exact duplicate rows are harmless. A task cannot depend on itself. The dependency snapshot must not contain a cycle.

### `fixtures/events.csv`

Columns:

- `event_id` — globally unique logical delivery identifier.
- `task_id`
- `occurred_at` — RFC3339 timestamp with explicit offset.
- `version` — positive integer used to order state changes for the same task at the same instant.
- `action` — `complete` or `reopen`.

The file is not guaranteed to be ordered.

An exact duplicate row with the same `event_id` is an at-least-once delivery replay and behaves as one event. Reusing an `event_id` with different fields is invalid.

For one task, if multiple events have the same `occurred_at`, increasing `version` defines their order. Reusing the same `(task_id, occurred_at, version)` for different logical events is invalid.

### `fixtures/queries.jsonl`

Each line contains:

- `request_id` — unique request identifier.
- `workflow_id`
- `as_of` — historical instant.
- `limit` — positive integer, at most 50.

Queries are read-only, independent, and may move backward or forward in time.

## State and readiness semantics

A task starts **incomplete**.

For a query at `as_of`, apply every event whose `occurred_at <= as_of`. For each task, process those state changes by `(occurred_at, version)`:

- `complete` makes the task complete.
- `reopen` makes the task incomplete.
- Repeating an action that already matches the current state is a valid no-op.

A task is **runnable** at `as_of` exactly when:

1. the task itself is incomplete; and
2. every direct prerequisite is complete at `as_of`.

A completed task is never returned as runnable.

Completion events are authoritative observations. Do **not** reject an event merely because that task's prerequisites were incomplete when the event occurred. Dependencies gate what is runnable; they do not retroactively invalidate the event feed.

If a prerequisite later reopens, an unfinished dependent may become blocked again. No completion state is cascaded or automatically undone.

All timestamp comparisons are by instant. Different RFC3339 offsets representing the same instant are equivalent.

## Goal

For every valid query, return up to `limit` runnable tasks for that workflow, in this deterministic order:

1. higher `priority`;
2. then earlier `due_at`;
3. then lexicographically smaller `task_id`.

A resolved output object has this shape:

```json
{
  "request_id": "q-001",
  "status": "resolved",
  "task_ids": ["pay-check-ledger", "pay-contact-bank"]
}
```

If the workflow exists but no task is runnable, return an empty `task_ids` array.

If a query references an unknown workflow, emit:

```json
{"request_id":"q-009","status":"invalid","reason":"unknown_workflow"}
```

Malformed query values, invalid timestamps, non-positive limits, or `limit > 50` produce:

```json
{"request_id":"q-010","status":"invalid","reason":"invalid_query"}
```

An invalid query must not stop later queries.

## Acceptance criteria

- Emit exactly one result per query in original query-file order.
- Results must be independent of row order in every CSV file.
- Exact duplicate dependency rows and exact duplicate event deliveries behave as one logical record.
- Conflicting reuse of an `event_id` fails dataset validation.
- Conflicting reuse of `(task_id, occurred_at, version)` fails dataset validation.
- Unknown task/workflow references, duplicate workflow/task IDs, empty identifiers, malformed timestamps, invalid event actions, and non-positive event versions fail dataset validation.
- Dependencies cannot cross workflows and cannot contain self-edges or cycles.
- Events exactly at `as_of` are visible to that query.
- Same-instant state changes for one task follow ascending `version`.
- A `reopen` can make a previously runnable dependent become blocked again.
- A later `complete` can make that dependent runnable again.
- Repeated `complete` or `reopen` actions are valid no-ops.
- A task with no prerequisites is runnable whenever it is incomplete.
- Completed tasks are never returned.
- Ordering is exactly priority descending, due time ascending, then task ID ascending.
- Timestamp offsets that denote the same instant must produce the same result.
- Diagnostic logging belongs on stderr; stdout must remain JSONL.

## Production constraints

The checked-in fixture is intentionally small. Design for approximately:

- 250,000 workflows;
- 2,000,000 tasks;
- 8,000,000 dependency rows after deduplication;
- 50,000,000 state events over a 90-day incident-history horizon;
- 3,000,000 historical queries per immutable snapshot;
- most tasks have 0–6 dependents, but a few gate tasks have 100,000+ direct dependents;
- queries for the same workflow often cluster around nearby timestamps, but query order is arbitrary;
- `limit` is at most 50;
- 1.5 GB memory budget;
- target p95 under 25 ms for a typical query after preprocessing.

A production-credible design should not rebuild the state of an entire workflow for every query, rescan all 50 million events independently for each request, or traverse the full dependency graph on every lookup.

The fixture is small enough that a simplistic approach may appear correct. Your solution should still have a defensible path to the production shape.

## Expected deliverable

Implement the historical readiness capability behind `ReadinessResolver.resolve_all(...)` in `readiness/planner.py`, plus supporting code as needed.

Add focused tests for the correctness risks you consider most important. Be prepared to explain:

- what state you preprocess once;
- how historical event changes affect unfinished dependents;
- how you answer arbitrarily ordered historical queries without restarting from an empty snapshot every time;
- how you produce the first few runnable tasks in deterministic business order;
- startup, event-processing, and per-query complexity;
- memory behavior around very high-fanout gate tasks;
- which malformed-data and timestamp-boundary cases you verified;
- whether a deterministic, heuristic, LLM-assisted, or hybrid design belongs in the critical path and what guarantees it would preserve or give up.

## Run / verify

Python 3.11+ is sufficient; there are no third-party dependencies.

Baseline checks before changing anything:

```bash
bash scripts/test.sh
bash scripts/build.sh
bash scripts/verify.sh
```

Fixture validation is equivalent to:

```bash
python3 gatequeue.py validate \
  --workflows fixtures/workflows.csv \
  --tasks fixtures/tasks.csv \
  --dependencies fixtures/dependencies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.jsonl
```

After implementing the resolver:

```bash
python3 gatequeue.py resolve \
  --workflows fixtures/workflows.csv \
  --tasks fixtures/tasks.csv \
  --dependencies fixtures/dependencies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.jsonl
```

## Scope / out of scope

In scope: immutable snapshot loading, validation, historical readiness queries, deterministic result ordering, focused tests, and production-scale reasoning.

Out of scope: mutating the source files, distributed coordination, live event ingestion during a run, persistence, authentication, notification delivery, UI work, or external APIs.

## 60-minute AI-assisted interview instruction

You have **60 minutes**. You may use Claude Code, Codex, ChatGPT, or similar tools as you would in a real engineering workflow. Inspect the repository and fixture data yourself first, write down the state/readiness semantics in your own words, then implement incrementally and verify the risky boundaries. A one-shot implementation that only matches the sample data is not sufficient; be ready to defend correctness and scale.
