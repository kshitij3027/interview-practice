# POST-PRACTICE ONLY — SignalMesh Interviewer Notes

Do not expose this file before the candidate finishes the exercise.

## Intended underlying structure

The core problem is **offline temporal connectivity with deletions/expiry** plus per-component aggregates. Each evidence ID creates one or more half-open active time intervals. At a query timestamp, every evidence interval covering that timestamp contributes an undirected edge between its two accounts. The answer is the connected component containing the seed account, with size, high-risk count, risk-point sum, and lexicographically smallest member.

The hard part is that edges disappear because of TTL expiry and RETRACT. A normal forward-only connectivity structure cannot undo merges, and rebuilding the graph independently for 250k historical queries is too expensive.

## Strong exact solution approach

A strong production-oriented solution can:

1. Deduplicate and validate events, then group by `evidence_id`.
2. Sort each evidence history by event time and convert ASSERT / RETRACT / TTL refresh semantics into one or more half-open active intervals `[start, end)`.
3. Normalize query timestamps and preserve original output order.
4. Compress the distinct query timestamps. For every evidence interval, determine which query-time indices fall inside it.
5. Associate that edge with a hierarchy of query-time ranges so it can be applied only while traversing the time spans where it is active.
6. Traverse those time spans with a reversible connected-component structure. Each component maintains size, high-risk count, risk-point sum, and minimum account ID. Roll back all mutations when leaving a time range.
7. At each query-time leaf, answer all queries at that instant from the current component state.

The candidate does not need to use exactly this implementation. Any exact approach with credible asymptotics and memory behavior is defensible.

### Complexity target

Let `A` be accounts, `V` be validated deduplicated events, `I` be produced evidence-active intervals, and `Q` be distinct query instants.

A strong offline design is roughly:

- validation / grouping / sorting: `O(V log V)` globally or the equivalent sum of per-evidence sorts;
- interval-to-query-range mapping: `O(I log Q)` for boundary searches;
- range registration and traversal: typically `O(I log Q)` union applications;
- component operations: near-constant or logarithmic-amortized depending on reversible structure details;
- answers: `O(number of queries)` once the relevant time state is active.

Memory is roughly `O(A + V + I log Q + Q)` in a straightforward implementation, though interval registration can be optimized.

## Why common naive approaches fail

### Rebuild per query

For each query, replay every event up to `as_of`, construct all active edges, then traverse the graph. This may be fixture-correct but is unacceptable at 25M events × 250k queries.

### Sort queries and only add edges

Sorting queries chronologically and adding ASSERT edges looks attractive, but it fails once evidence expires or is retracted because ordinary connectivity cannot simply delete an edge and split a component.

### Treat each evidence ID as the relationship

Two evidence IDs may overlap on the same unordered pair. Retracting or expiring one must not remove connectivity if another remains active. Exact connectivity approaches that apply evidence intervals independently are safe because duplicate unions are harmless, provided rollback bookkeeping handles no-op unions correctly.

### Use only the latest event for an evidence ID

This loses earlier active windows needed by historical queries.

### Expire from the first ASSERT only

Repeated ASSERT while active refreshes the expiry from the newer assertion time.

### Raw timestamp string comparison

Offset-equivalent timestamps must compare as the same instant.

## Subtle traps

1. **Half-open intervals:** query at ASSERT time sees the edge; query exactly at RETRACT or TTL expiry does not.
2. **Refresh without a gap:** an ASSERT received before current expiry extends the active period continuously.
3. **ASSERT after expiry:** closes the old interval at its expiry and starts a new interval at the later assertion.
4. **Inactive RETRACT:** valid no-op, including the fixture’s `evd-010` retraction.
5. **Overlapping evidence on one pair:** `evd-001` and `evd-004` both connect A100/A101 for part of the fixture. `evd-001` retracting at 09:40 must not disconnect the pair because `evd-004` remains active.
6. **Unordered pair identity:** A100/A101 and A101/A100 are the same relationship endpoints.
7. **Cycles:** component aggregates count accounts once.
8. **Queries are not chronological:** output still follows input order.
9. **Same-instant evidence events:** starter validation rejects ambiguous distinct events for one evidence ID at one instant.
10. **Rollback no-op unions:** if the same pair is active through overlapping evidence intervals, a reversible connectivity implementation must record enough information to undo each attempted union safely, including unions that found the endpoints already connected.
11. **Large components:** avoid enumerating every component member for every query just to compute the four requested aggregates.
12. **Unknown query account:** return per-query invalid result rather than failing the entire dataset.

## Fixture observations the candidate should discover

Without giving these away before the practice:

- `events.csv` is intentionally out of chronological order.
- `ev-002` is an exact retry and should deduplicate.
- `evd-001` links A100/A101 via `device` and retracts at 09:40.
- `evd-004` independently links A100/A101 via `address` beginning at 09:30, so the pair remains connected after 09:40.
- `evd-006` links A104/A105 at 10:00 and is reasserted at 10:45, extending its life to 11:45 instead of expiring at 11:00.
- `evd-008` connects A105/A106 from 09:35 until its RETRACT at 10:05.
- `q-005` and `q-011` represent the same instant with different offsets and should match exactly.
- `q-010` references an unknown account and should be an individual invalid result.

Useful expected cohort checks:

- q-001: size 2, high-risk 1, risk points 90, representative A100.
- q-002: size 4, high-risk 2, risk points 165, representative A100.
- q-003: still size 4 because the address evidence keeps A100/A101 connected.
- q-004: A105/A106/A107 => size 3, high-risk 1, risk points 110, representative A105.
- q-005 and q-011: all eight accounts connected => size 8, high-risk 3, risk points 280, representative A100.
- q-006: A100–A105 => size 6, high-risk 3, risk points 260, representative A100.
- q-007: A100/A101/A102 => size 3, high-risk 2, risk points 150, representative A100.
- q-008: A104/A105 remain connected because of the refreshed TTL => size 2, high-risk 1, risk points 95, representative A104.
- q-009: exactly at refreshed expiry, A104 is isolated => size 1, high-risk 0, risk points 5, representative A104.

## High-level hidden checks

Evaluator-only checks should include variants of the following without prescribing implementation:

- event rows randomly shuffled;
- query rows randomly shuffled while asserting original-order output;
- two overlapping evidence IDs for one pair, with only one retracting;
- repeated ASSERT before expiry and another ASSERT after an expiry gap;
- RETRACT exactly at a query instant;
- ASSERT exactly at a query instant;
- TTL expiry exactly at a query instant;
- multiple offset representations of the same instant;
- a cycle such as A–B–C–A with correct non-duplicated aggregates;
- a long chain to verify transitivity;
- a large synthetic batch that exposes per-query event replay or full-graph rebuilds;
- many evidence intervals on one hot pair;
- a component merge that is later undone, verifying component metadata is restored correctly;
- unknown query account mixed among valid queries;
- isolated account;
- conflicting event ID / evidence identity / same-instant evidence events rejected by validation.

## Alternative defensible designs

A candidate may propose or implement:

- block/sqrt decomposition over time with periodic rebuilds and a small delta layer;
- a more specialized fully dynamic connectivity approach;
- snapshot checkpoints plus bounded replay if the actual query-time distribution and SLA justify it;
- per-time-bucket recomputation if timestamp granularity is coarser than the given contract (but this fixture does not grant such coarsening);
- approximate or heuristic cohorting only if they explicitly acknowledge that it violates the exact observable contract.

A fixture-only brute-force implementation can still demonstrate progress, but the candidate must distinguish it from a production answer.

## Likely AI-agent failure modes

1. One-shot generation that rebuilds a graph per query because the fixture is small.
2. Treating RETRACT as permanent and forgetting a later ASSERT can reactivate evidence.
3. Refreshing TTL from the original assertion rather than the new assertion.
4. Collapsing all evidence for a pair into one boolean without correctly handling overlapping lifetimes.
5. Using a normal union-find while sorting queries chronologically and silently ignoring deletions.
6. Forgetting rollback of component aggregates or no-op union bookkeeping.
7. Returning results in timestamp order instead of input order.
8. Accidentally comparing timestamp strings rather than instants.
9. Enumerating all component members for each query even after maintaining enough aggregate metadata.
10. Over-engineering the CSV/parser layer instead of spending the hour on the temporal-connectivity problem.

## Recommended prioritization during the hour

A strong candidate should roughly:

1. Confirm event semantics and derive active intervals correctly.
2. Get exact fixture correctness with a simple approach if needed.
3. Add targeted tests for expiry, refresh, overlapping evidence, and offset timestamps.
4. Upgrade or clearly articulate the scalable historical-query strategy.
5. Preserve original query order and component aggregates.
6. Use the remaining time to verify and explain complexity / tradeoffs.

It is better to finish a correct simple implementation plus a precise production design than to leave an ambitious reversible structure half-working.

## Walkthrough inspection points

After the hour, ask the candidate to explain:

- what state exists per evidence ID and why;
- exactly what happens to `evd-006` between 10:00 and 11:45;
- why A100/A101 remain connected after 09:40;
- why a simple sorted-query union structure is insufficient;
- how their approach deals with edge disappearance and possible component splitting;
- whether repeated evidence on one pair changes correctness or only performance;
- how component aggregates are maintained without member enumeration;
- preprocessing, query complexity, worst-case hot-pair behavior, and memory;
- which visible and adversarial cases they actually ran;
- what they would change if queries were online rather than available as a batch.
