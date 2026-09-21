# BurstRank — One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

A payments platform operates a credential-abuse response service. During card-testing or bot attacks, investigators care less about raw traffic than about which customer accounts are suddenly touching many distinct payment credentials in a short period. The service therefore produces a rolling regional leaderboard of customer accounts by recent credential velocity.

The current prototype answers each investigator request by rescanning every event in the requested time window and recomputing every customer's distinct credential count from scratch. That worked on samples. Production traffic is now large enough that historical investigations with thousands of independent lookups take far too long.

You have been asked to build an in-process resolver for one immutable batch of clients, regional policies, access events, and investigation queries. The observable behavior is specified; the implementation strategy is yours.

## Supplied data

### `fixtures/clients.csv`

Each row contains:

- `client_id` — globally unique customer identifier.
- `region` — the client's fixed policy region.
- `display_name` — metadata only; it does not affect ranking.

### `fixtures/policies.csv`

Each row contains:

- `region` — globally unique policy region.
- `window_minutes` — rolling lookback window for that region.
- `max_k` — largest leaderboard size allowed for an individual query.

Every client's region must have a policy.

### `fixtures/events.csv`

Each row is one observed credential-touch event:

- `event_id` — globally unique logical delivery identifier.
- `client_id` — customer that generated the event.
- `credential_id` — credential fingerprint observed on that request.
- `occurred_at` — RFC3339 timestamp with an explicit offset.

The file is not guaranteed to be ordered by time.

An exact duplicate row with the same `event_id` is a harmless delivery retry and behaves as one event. Reusing an `event_id` with different fields is invalid data.

A credential may appear repeatedly for the same client and may also appear for different clients. Distinctness is measured per client within the query window.

### `fixtures/queries.jsonl`

Each line contains:

- `request_id` — unique query identifier.
- `region` — policy region to inspect.
- `as_of` — historical instant for the leaderboard.
- `k` — requested number of leaders.

Queries are read-only and independent. They may be supplied in any order and may move backward or forward in time.

## Rolling-window semantics

For a query at `as_of` in a region whose policy window is `W` minutes, an event is in scope exactly when:

`as_of - W < event.occurred_at <= as_of`

The left boundary is exclusive and the right boundary is inclusive. For example, with a 10-minute window and `as_of = 10:00:00Z`, an event at exactly `09:50:00Z` is out of scope, while an event at exactly `10:00:00Z` is in scope.

Timestamps are compared as instants. Different RFC3339 offsets representing the same instant are equivalent.

For each client in the query's region, calculate:

- `distinct_credentials` — number of different `credential_id` values having at least one in-window event for that client.
- `request_count` — number of deduplicated in-window events for that client.

Only clients with `request_count > 0` participate in the leaderboard.

Rank participating clients by these rules in order:

1. higher `distinct_credentials` first;
2. if tied, higher `request_count` first;
3. if still tied, lexicographically smaller `client_id` first.

## Goal

For each valid query, emit one JSON object containing the top `k` clients after applying the exact rolling-window and ranking semantics.

Example shape:

```json
{
  "request_id": "q-us-base",
  "status": "resolved",
  "leaders": [
    {"client_id": "c-a", "distinct_credentials": 2, "request_count": 3},
    {"client_id": "c-b", "distinct_credentials": 2, "request_count": 2}
  ]
}
```

If no client has an in-window event, return an empty `leaders` array with `status = "resolved"`.

If a query references an unknown region, emit:

```json
{"request_id":"q-x","status":"invalid","reason":"unknown_region"}
```

If `k < 1` or `k > max_k` for that region, emit:

```json
{"request_id":"q-y","status":"invalid","reason":"invalid_k"}
```

An invalid query does not stop later queries from being processed.

## Acceptance criteria and edge cases

1. Emit exactly one result per query in the original query-file order.
2. Reordering `events.csv` must not change results.
3. Compare timestamps as instants, not timestamp strings or local wall-clock text.
4. Apply the rolling window exactly as `(as_of - W, as_of]`.
5. Exact duplicate event rows are deduplicated by `event_id`; conflicting reuse of one `event_id` fails dataset validation.
6. Repeated events for the same `(client_id, credential_id)` count individually toward `request_count` but contribute only once to `distinct_credentials` while at least one such event remains in the window.
7. When one occurrence of a repeated credential leaves the window, the credential must remain distinct if another occurrence is still in scope.
8. Events after `as_of` never influence that query, even if they appear earlier in the CSV.
9. A credential may be shared by different clients; distinctness is per client, not global.
10. Ranking ties must follow the exact precedence above and must not depend on map iteration order or CSV ordering.
11. Unknown client IDs in events, duplicate client IDs, duplicate policy regions, missing client policies, non-positive policy windows/maxima, empty identifiers, malformed timestamps, or timestamps without offsets fail dataset validation.
12. Unknown query regions and out-of-range `k` values are query-level invalid results rather than whole-dataset failures.
13. Load and validate the immutable snapshot once. Do not reread all source files for every query.
14. Diagnostic logging belongs on stderr so stdout remains a JSONL result stream.

## Production constraints

The checked-in fixture is intentionally small. Design and explain your approach for approximately:

- 600,000 clients across 18 regions;
- 40 million deduplicated events in a 24-hour investigation batch;
- 300,000 historical queries in one batch;
- regional windows between 5 and 60 minutes;
- query timestamps spread across the full 24 hours and not supplied chronologically;
- a few extremely hot clients producing millions of events, while most clients produce fewer than 100;
- some hot credentials repeated thousands of times for one client inside a window;
- requested `k` values typically 10–50, with regional `max_k <= 100`;
- 1.5 GB memory budget;
- total batch completion expected in minutes, with individual leaderboard extraction remaining small relative to rescanning the event corpus.

A production-credible solution should not rescan all 40 million events for each query, rebuild a fresh per-client credential map independently for every query, or sort all active clients from scratch for every leaderboard.

Think carefully about what work can be shared when many historical queries use the same regional rolling-window policy, what has to happen when events enter and leave a window, and how repeated credentials affect incremental counts.

The candidate owns the solution strategy. An exact deterministic solution is a natural fit, but heuristic, approximate, LLM-assisted, or hybrid approaches may be defended if you clearly identify any correctness, latency, memory, or explainability tradeoffs. No external model or API is required.

## Expected deliverable

Implement `VelocityResolver.resolve_all()` in `burstrank/resolver.py` and add or change supporting code as needed so:

```bash
python3 velocity_rank.py resolve \
  --clients fixtures/clients.csv \
  --policies fixtures/policies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.jsonl
```

emits one JSON object per query.

Add focused tests for the correctness risks you consider most important. Be prepared to explain how you model the rolling window, how repeated credentials enter and leave the distinct count, how you reuse work across out-of-order historical queries, how you obtain the top `k` without sorting every client for every query, expected preprocessing/update/query complexity, memory behavior under skew, and which boundary cases you verified.

## Verification / run commands

Python 3.11+ and the standard library are sufficient.

Baseline checks before making changes:

```bash
bash scripts/test.sh
bash scripts/build.sh
bash scripts/verify.sh
```

Fixture validation is equivalent to:

```bash
python3 velocity_rank.py validate \
  --clients fixtures/clients.csv \
  --policies fixtures/policies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.jsonl
```

After implementing the resolver:

```bash
python3 velocity_rank.py resolve \
  --clients fixtures/clients.csv \
  --policies fixtures/policies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.jsonl
```

## Scope / out of scope

In scope: one immutable batch, exact event-time window semantics, exact per-client distinct and request counts, deterministic top-`k` ranking, query-level validation, reusable preprocessing/state, focused tests, and scalability reasoning.

Out of scope: live streaming ingestion, distributed state stores, persistent databases, approximate sketches unless explicitly defended as a tradeoff, credential risk scoring, authentication, a web UI, changing client regions during the batch, and external APIs.

## 60-minute AI-assisted interview instruction

You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or other AI tools as you would on the job, but inspect the fixture, boundary semantics, and ranking contract yourself before delegating implementation.

First write down the exact window boundaries and how one repeated credential should affect state as its individual events enter and leave the window. Then implement the smallest credible solution, verify a few adversarial timestamps and ranking ties, and leave time to explain how your design behaves for many historical queries and highly skewed clients.

The interviewer is evaluating how you translate a customer investigation workflow into a precise data problem, whether you identify the reusable work across queries, how you use AI without trusting a one-shot answer, and whether you can defend correctness and scalability.
