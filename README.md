# SignalMesh — One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

A marketplace trust-and-safety team investigates coordinated seller abuse. Their strongest signals are not individual risk scores but temporary relationships between accounts: two sellers may share a payout instrument, device, or operating address for some period of time. Analysts often ask, “As of this exact moment, what exposure cohort was this seller connected to?”

Today the investigation service replays relationship events and rebuilds a graph separately for every analyst lookup. That is acceptable on a tiny dataset, but production now contains millions of accounts, many expiring or retracted signals, and large batches of historical lookups.

You have been asked to build an in-process resolver for one immutable snapshot of accounts, signal policies, relationship events, and investigation queries. This is a customer-style systems problem: the observable behavior is specified, but the implementation strategy is yours.

## Supplied data

### `fixtures/accounts.csv`

Each row contains:

- `account_id` — globally unique account identifier.
- `risk_tier` — `standard` or `high`.
- `risk_points` — non-negative integer used only for cohort aggregation.

### `fixtures/policies.csv`

Each row contains:

- `relation_type` — globally unique signal type, such as `device` or `payout`.
- `ttl_minutes` — positive integer lifetime for an asserted piece of evidence.

### `fixtures/events.csv`

Each row is one relationship-state event:

- `event_id` — globally unique logical event identifier.
- `evidence_id` — identifier for one continuing piece of relationship evidence.
- `account_a`, `account_b` — the two accounts linked by this evidence. Relationship direction does not matter.
- `relation_type` — determines the evidence TTL.
- `action` — `ASSERT` or `RETRACT`.
- `occurred_at` — RFC3339 timestamp.

The file is not guaranteed to be ordered by time.

An exact duplicate row with the same `event_id` is a harmless delivery retry and behaves as one event. Reusing an `event_id` with different fields is invalid data.

For one `evidence_id`, the unordered account pair and `relation_type` never change. Violating that rule is invalid data. Two different evidence IDs may connect the same account pair at the same time.

### `fixtures/queries.csv`

Each row contains:

- `request_id` — unique query identifier.
- `account_id` — seed account.
- `as_of` — RFC3339 timestamp.

Queries are read-only and independent. They may arrive in any order and may ask about historical times.

## Relationship semantics

Each `evidence_id` has its own state over time.

- `ASSERT` makes that evidence active at `occurred_at` and sets its expiry to `occurred_at + ttl(relation_type)`.
- A later `ASSERT` while the same evidence is still active refreshes its expiry. It does not create a gap.
- `RETRACT` makes that evidence inactive at `occurred_at` if it is active then. Retracting already-inactive evidence is a valid no-op.
- Expiry is exclusive: evidence asserted at `09:00` with a 60-minute TTL is active at `09:59:59...` and inactive at exactly `10:00` unless refreshed before then.
- A query at the same instant as an `ASSERT` sees that assertion. A query at the same instant as a `RETRACT` does not see the retracted evidence.
- Events for one `evidence_id` must have distinct `occurred_at` instants after exact retry deduplication. If two distinct events for one evidence occur at exactly the same instant, dataset validation fails.

At a particular instant, an undirected relationship exists between two accounts if **at least one** evidence ID connecting that pair is active. Active relationships are transitive: if A is linked to B and B is linked to C, all three accounts are in one exposure cohort even when A and C have no direct evidence.

## Goal

For every query, report aggregate information about the seed account's complete exposure cohort at `as_of`.

For a valid seed account, output one JSON object containing:

```json
{
  "request_id": "q-001",
  "status": "resolved",
  "component_size": 4,
  "high_risk_count": 2,
  "risk_points": 165,
  "representative": "A100"
}
```

The fields mean:

- `component_size` — number of accounts in the connected cohort, including the seed.
- `high_risk_count` — number of cohort accounts whose `risk_tier` is `high`.
- `risk_points` — sum of `risk_points` across the cohort.
- `representative` — lexicographically smallest `account_id` in the cohort.

An account with no active relationships is a valid one-account cohort.

If a query references an unknown account, emit:

```json
{"request_id":"q-999","status":"invalid","reason":"unknown_account"}
```

Continue processing later queries normally.

## Acceptance criteria and edge cases

1. Emit exactly one result per query in the original query-file order.
2. Compare timestamps as instants. Different RFC3339 offsets representing the same instant must produce the same answer.
3. Reordering `events.csv` must not change results.
4. Exact duplicate `event_id` rows are deduplicated. Conflicting reuse of one `event_id` fails validation.
5. The pair attached to an `evidence_id` is unordered: `A100,A101` and `A101,A100` describe the same pair. Changing either account or the relation type for one evidence ID fails validation.
6. Different evidence IDs may overlap on the same account pair. One evidence expiring or retracting must not remove the relationship while another evidence for that pair remains active.
7. Re-asserting active evidence refreshes its TTL from the new assertion time.
8. Expiry and retraction boundaries are half-open as described above.
9. Cycles in the active relationship network are valid and must not duplicate accounts in cohort metrics.
10. A `RETRACT` of already-inactive evidence is valid and changes nothing.
11. Unknown accounts referenced by relationship events, self-links, unknown relation types, non-positive TTLs, negative risk points, duplicate account IDs, duplicate relation types, or ambiguous same-instant events for one evidence ID fail dataset validation.
12. Output must be deterministic and independent of CSV row order, map iteration order, or process hash behavior.
13. Load and validate the immutable snapshot once. Do not reread every CSV for each query.
14. Diagnostic logging belongs on stderr so stdout can remain a JSONL result stream.

## Production constraints

The checked-in fixture is intentionally small. Design and explain your approach for approximately:

- 5 million accounts;
- 2 million distinct evidence IDs active or recently active in a 24-hour investigation window;
- 25 million relationship events in that window, including delivery retries;
- 250,000 historical queries per batch;
- query timestamps spread across the same 24-hour window and not supplied in chronological order;
- a few abuse rings with 100,000+ accounts, but most components below 50 accounts;
- highly skewed pairs that may have hundreds of overlapping evidence IDs;
- 1.5 GB memory budget;
- target p95 under 20 ms per query after the batch and static files are loaded, with total batch completion expected in minutes rather than hours.

A production-credible solution should not rebuild the entire active relationship graph independently for each query, replay all 25 million events from the beginning for each query, or materialize a full copy of the graph at every distinct query timestamp.

A simple forward-only connectivity structure also deserves scrutiny because evidence can expire or be retracted. Think carefully about what work can be shared across many historical queries and what state really has to exist at each instant.

The candidate owns the solution strategy. An exact deterministic solution is a natural fit for the observable contract, but heuristic, approximate, LLM-assisted, or hybrid approaches may be defended if you clearly state where they do or do not preserve correctness, latency, cost, and explainability. No external model or API is required.

## Expected deliverable

Implement `ExposureResolver.resolveAll(...)` in `src/main/java/signalmesh/ExposureResolver.java` and add or change supporting code as needed so:

```bash
java -cp out signalmesh.Main resolve \
  --accounts fixtures/accounts.csv \
  --policies fixtures/policies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.csv
```

emits one JSON object per query.

Add focused tests for the correctness risks you consider most important. Be prepared to explain how you model evidence lifetimes, how you handle multiple evidence IDs for one pair, how you answer historical queries without independently rebuilding the world each time, how you preserve exact cohort aggregates, expected preprocessing/query complexity, worst-case skew, memory use, and which correctness boundaries you verified.

## Verification / run commands

Java 21+ is sufficient; no third-party dependencies are required.

Baseline checks before making changes:

```bash
./scripts/test.sh
./scripts/build.sh
./scripts/verify.sh
```

The validation command used by `verify.sh` is:

```bash
java -cp out signalmesh.Main validate \
  --accounts fixtures/accounts.csv \
  --policies fixtures/policies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.csv
```

After implementing the resolver:

```bash
java -cp out signalmesh.Main resolve \
  --accounts fixtures/accounts.csv \
  --policies fixtures/policies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.csv
```

## Scope / out of scope

In scope: one immutable batch of files, exact event-time semantics, relationship expiry/retraction, cohort aggregation, deterministic output, reusable preprocessing, focused tests, and scalability reasoning.

Out of scope: live streaming ingestion, distributed graph storage, persistent databases, account-level ML scoring, changing risk metadata over time, authentication, a web UI, and calling external APIs.

## 60-minute AI-assisted interview instruction

You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or other AI tools as you would on the job, but inspect the event semantics and fixture yourself before delegating implementation.

First write down the exact state transitions and timestamp boundaries in your own words. Then choose the smallest credible implementation, verify cases involving overlap, expiry/retraction, and historical query ordering, and leave time to explain how your design changes when moving from the fixture to production scale.

The interviewer is evaluating how you translate a customer investigation workflow into a temporal systems model, whether you recognize where naive graph rebuilding breaks down, how you use AI without trusting it blindly, and whether you can defend correctness and scalability.
