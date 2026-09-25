# WindowFinder — One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

A cloud infrastructure provider sells short, guaranteed blocks of accelerator capacity to enterprise customers. Each compute pool has a fixed accelerator SKU, region, capability tags, a base number of units, and a unit price. Operations also records planned capacity changes (maintenance removals, repaired hardware, temporary expansions) and existing reservations.

A customer request asks: **what is the earliest contiguous window in which we can promise this workload without moving any existing reservation?** Today, operators answer by opening several dashboards and manually checking candidate pools. That is slow and error-prone, especially for long booking windows and busy pools.

You have been asked to build an in-process resolver for one immutable planning snapshot. It must answer many independent availability requests quickly and deterministically.

## Supplied data

### `fixtures/pools.csv`

Each row contains:

- `pool_id` — globally unique pool identifier.
- `region` — exact region, such as `us-west`.
- `sku` — exact accelerator SKU.
- `tags` — `|`-separated capability tokens. Empty means no extra capabilities.
- `unit_price_micros` — non-negative integer price metadata used only for deterministic pool choice.
- `base_capacity` — non-negative integer number of units available before any capacity events.

### `fixtures/capacity_events.csv`

Each row contains:

- `event_id` — globally unique logical event identifier.
- `pool_id` — pool whose capacity changes.
- `effective_at` — RFC3339 timestamp with an explicit offset.
- `delta_units` — signed integer added to that pool's capacity from `effective_at` onward.

The file is not guaranteed to be ordered. Several different events may become effective at the same instant. Exact duplicate rows with the same `event_id` are harmless delivery replays and behave as one event. Reusing an `event_id` with different fields is invalid.

### `fixtures/reservations.csv`

Each row contains:

- `reservation_id` — globally unique logical reservation identifier.
- `pool_id` — pool that is already committed.
- `start_at` — inclusive RFC3339 start.
- `end_at` — exclusive RFC3339 end.
- `units` — positive integer number of units consumed while the reservation is active.

Reservations are fixed. The planner may not move, shrink, or cancel them. Exact duplicate rows are harmless replays; conflicting reuse of one `reservation_id` is invalid.

### `fixtures/queries.jsonl`

Each line contains one independent request:

- `request_id` — unique request identifier.
- `region` — required exact region.
- `sku` — required exact SKU.
- `required_tags` — array of capability tokens; the chosen pool must contain all of them.
- `units` — positive number of units required for the entire booking.
- `duration_minutes` — positive duration, divisible by 5.
- `earliest_start` — earliest allowed start, inclusive.
- `latest_finish` — latest allowed finish, inclusive.

All planning requests are read-only and independent. A result for one request must not consume capacity for later requests.

## Time and availability semantics

All capacity-event, reservation, and query boundaries must be aligned to **5-minute UTC boundaries** after parsing as instants.

For a pool and instant `t`:

- every capacity event with `effective_at <= t` contributes its `delta_units`;
- a reservation consumes units exactly while `start_at <= t < end_at`;
- free capacity is `base_capacity + active capacity deltas - active reservation units`.

A candidate booking starting at `s` with duration `d` is feasible only when:

1. `s >= earliest_start`;
2. `s + d <= latest_finish`;
3. `s` is aligned to a 5-minute boundary; and
4. the pool's free capacity is at least `units` for **every instant** in `[s, s + d)`.

Capacity changes or reservation boundaries exactly at `s` take effect for the candidate. A capacity change exactly at `s + d` does not affect that candidate because the booking has already ended.

## Goal

For every valid query, find the best feasible promise across all eligible pools.

Choose the winner using these rules in order:

1. earliest `start_at`;
2. if several eligible pools can start at that same instant, lower `unit_price_micros`;
3. if still tied, lexicographically smaller `pool_id`.

A successful result must have this shape:

```json
{
  "request_id": "q-001",
  "status": "resolved",
  "pool_id": "west-a100-02",
  "start_at": "2026-09-25T09:35:00Z",
  "finish_at": "2026-09-25T10:05:00Z"
}
```

If no eligible pool has a feasible window, emit:

```json
{"request_id":"q-009","status":"unavailable"}
```

Malformed query values (non-positive units, invalid duration, misaligned boundaries, or `earliest_start >= latest_finish`) produce a query-level result:

```json
{"request_id":"q-010","status":"invalid","reason":"invalid_query"}
```

An invalid query does not stop later queries from being processed.

## Acceptance criteria and edge cases

1. Emit exactly one result per query in the original query-file order.
2. Compare timestamps as instants. Different RFC3339 offsets representing the same instant are equivalent.
3. Normalize successful output timestamps to UTC with a `Z` suffix.
4. Reordering any input file must not change results.
5. Pool eligibility requires exact `region`, exact `sku`, and set containment of every `required_tags` token. `ib` does not match `infiniband`.
6. An empty `required_tags` array is valid.
7. Capacity events at the same instant are cumulative; row order at that timestamp must not matter.
8. Exact duplicate event/reservation rows are deduplicated. Conflicting reuse of an ID fails dataset validation.
9. Reservation intervals are half-open. Back-to-back reservations do not overlap at the shared boundary.
10. A candidate may start exactly when a reservation ends or a positive capacity event becomes effective.
11. A negative capacity event effective exactly at the candidate finish does not invalidate the candidate.
12. The baseline dataset is invalid if a pool's effective capacity ever becomes negative, or if fixed reservations ever consume more units than effective capacity at any instant.
13. Unknown pools referenced by capacity events or reservations, duplicate pool IDs, negative base capacity/prices, empty identifiers, malformed timestamps, unaligned boundaries, non-positive reservation units, or `start_at >= end_at` fail dataset validation.
14. Query `duration_minutes` must be positive and divisible by 5; `earliest_start` and `latest_finish` must be aligned. A window too short for the requested duration is valid input but resolves as `unavailable`.
15. A query with a syntactically valid region/SKU for which no pool exists resolves as `unavailable`, not a dataset error.
16. Planning requests must not mutate baseline capacity or reservations.
17. Diagnostic logging belongs on stderr so stdout remains a JSONL result stream.

## Production constraints

The checked-in fixture is intentionally small. Design and explain your approach for approximately:

- 20,000 pools across 24 regions and 14 accelerator SKUs;
- 1.5 million capacity events over a 90-day planning horizon;
- 8 million fixed reservations over the same horizon;
- 2 million independent availability queries per snapshot;
- most pools have fewer than 500 timeline changes, but a few hot shared pools have 200,000+;
- query durations range from 5 minutes to 7 days;
- requested units range from 1 to 512;
- the same `(region, sku, required_tags)` combinations repeat heavily, but requested units, durations, and windows vary;
- 1.5 GB process memory budget;
- target p95 under **40 ms** per typical query after snapshot preprocessing.

A production-credible solution should not scan all 20,000 pools for every request, scan every reservation in a pool for every candidate start, or expand every pool into a dense 5-minute array for the full 90-day horizon.

Hot pools and long windows matter. A solution that merely increments the candidate start by 5 minutes and rechecks the entire booking window can appear correct on the fixture while becoming unusable on production-shaped data.

## Expected deliverable

Implement the planning capability behind `planner.Resolver.ResolveAll(...)` in `internal/planner/resolver.go` and add supporting code as needed. The supplied loader/validator and starter tests establish input semantics but deliberately do not encode the full acceptance contract.

Your walkthrough should explain:

- what reusable representation you build for each pool;
- how you find a candidate's earliest feasible contiguous window without repeatedly rescanning unchanged time ranges;
- how you narrow the eligible pool set;
- preprocessing, per-query, and worst-case complexity;
- memory behavior for sparse pools versus the hottest pools;
- the correctness boundaries you verified;
- why output is deterministic;
- whether deterministic, heuristic, LLM-assisted, or hybrid techniques belong in the critical path, and any correctness tradeoff they introduce.

## Verification / run commands

Go 1.23+ and the standard library are sufficient.

Baseline checks before changing anything:

```bash
bash scripts/test.sh
bash scripts/build.sh
bash scripts/verify.sh
```

Fixture validation is equivalent to:

```bash
go run ./cmd/windowfinder validate \
  --pools fixtures/pools.csv \
  --events fixtures/capacity_events.csv \
  --reservations fixtures/reservations.csv \
  --queries fixtures/queries.jsonl
```

After implementing the resolver:

```bash
go run ./cmd/windowfinder resolve \
  --pools fixtures/pools.csv \
  --events fixtures/capacity_events.csv \
  --reservations fixtures/reservations.csv \
  --queries fixtures/queries.jsonl
```

## Scope / out of scope

In scope: immutable in-memory snapshot preprocessing, exact fixture semantics, deterministic planning, focused tests, and production-scale reasoning.

Out of scope: mutating reservations, distributed locking, persistence, billing, authentication, provisioning real accelerators, or calling external APIs.

## 60-minute AI-assisted interview instruction

You have **60 minutes**. Use AI tools as you would on the job. First inspect the repository and representative fixtures yourself, identify the failure modes of a simplistic solution, then implement incrementally and verify the risky boundaries. Be ready to explain the design at a systems level rather than only presenting code that happens to pass the visible fixture.
