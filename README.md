# TransitShield — HARD 60-Minute AI-Assisted Customer Interview

## Customer request

A regional transit agency wants to publish weekly ridership summaries without exposing tiny, identifying combinations of station, trip time, and fare product. The agency can make published data less specific and can suppress entire small groups, but cannot silently change or fabricate trips. Its prototype searches all trips for every proposed release, then chooses the least detailed summary even when a less destructive option is available. Analysts need an **exact and reproducible release recommendation** for many geographic scopes and reporting windows.

Build one release planner. You own the technical strategy: deterministic, heuristic, LLM-assisted, or hybrid are possible, but the observable optimality and privacy-threshold requirements are non-negotiable. No external service, credential, model, or paid API is required. Inspect the supplied data before choosing an approach. This is a simplified **minimum-group-size disclosure policy**, not a claim of comprehensive rider anonymity.

## Data you are given

- `fixtures/stations.csv`: `station_id,route_id,sector_id`. Every station belongs to one route and one sector. A route is an intermediate reporting category; a sector is the coarsest.
- `fixtures/fares.csv`: `fare_id,family`. Different fare products may share one family.
- `fixtures/rides.csv`: `trip_id,station_id,slot,fare_id`. Each unique `trip_id` counts as **one trip**, not one person. A `slot` is a quarter-hour index from `0` to `671` inclusive in a fixed seven-day week. Rows are unordered. Identical repeats are delivery retries and count once.
- `fixtures/requests.jsonl`: one independent review per **physical line**. Repeated request IDs are independent. Intentionally invalid records are present.
- `transitsafe.py`: working catalog loader, query parser, CLI, and unfinished `ReleasePlanner.plan(query)`.
- `tests/test_starter.py` and `scripts/`: green baseline smoke tests, not full acceptance tests.

CSV columns have exactly the named headers, in any order. All CSV identifiers and query `sector_id` use 1–48 ASCII letters, numbers, underscores or hyphens; request IDs permit 1–128 characters. CSV slot integers are canonical unsigned base 10 (no leading zeros except `0`). Duplicate catalog IDs with identical fields count once. Conflicting IDs, malformed catalog fields/headers, and references to missing stations or fares invalidate the **entire snapshot before any query output**. Malformed JSONL requests instead cause one isolated error and do not block subsequent lines.

A valid JSON request has these required fields (extra fields are ignored):

```json
{"request_id":"demo","sector_id":"BAY","from_slot":40,"until_slot":64,"k":3,"max_suppressed":5,"geo_weight":7,"time_weight":4,"fare_weight":2,"suppress_penalty":30}
```

The window is **half-open** `[from_slot,until_slot)`, with `0 <= from_slot < until_slot <= 672`. `k` is 2..10,000; `max_suppressed` is 0..1,000,000,000; the three weights are each 0..100; and `suppress_penalty` is 0..1000. These must be actual JSON integers, not numeric strings, booleans, or floats. Query sectors must exist. A query includes only trips in the specified sector and original time window. **Never expand the filtered population** when generalizing.

## Required capability

Implement `ReleasePlanner.plan(query)` and any justified preprocessing. A release plan chooses one **global level** for each of three dimensions; each level applies to **every trip in that review**:

| Dimension | Level 0 | Level 1 | Level 2 | Level 3 |
| --- | --- | --- | --- | --- |
| `geo_level` | station ID | route ID | sector ID | — |
| `time_level` | original 15-min slot | hour (`slot // 4`) | day (`slot // 96`) | entire week |
| `fare_level` | fare ID | fare family | all fares | — |

For a proposed plan, partition all **selected original trips** by their three generalized values. A group containing **fewer than `k` trips must be suppressed in its entirety**. A group containing `k` or more must be retained in its entirety. Suppression is neither optional nor permitted for larger groups. A plan is feasible only if `suppressed <= max_suppressed` **and at least one trip is retained**. No partial-group removal or cross-sector aggregation.

For any feasible plan, compute the exact integer information loss:

```text
loss = released * (geo_weight * geo_level
                   + time_weight * time_level
                   + fare_weight * fare_level)
       + suppressed * suppress_penalty
```

Choose the plan minimizing the tuple `(loss, suppressed, geo_level, time_level, fare_level)` in **that strict order**. Exact counts and deterministic tie breaking are required; approximate guesses do not satisfy the contract. Return exactly this JSON shape for a feasible plan (values are illustrative, not fixture answers):

```json
{"request_id":"demo","status":"ok","records":13,"released":11,"suppressed":2,"geo_level":1,"time_level":2,"fare_level":0,"loss":121}
```

If the request contains no trips, return `status:"empty"`; if it has trips but no feasible plan, return `status:"no_release"`. Both have `records` equal to the actual selected count, `released:0`, `suppressed:0`, and `geo_level`, `time_level`, `fare_level`, `loss` set to `null`. No plan is selected and no suppression has been authorized. Do not emit raw trip identifiers or small group memberships.

Malformed requests yield `{"request_id":null,"status":"invalid","reason":"invalid_query"}`, recovering an otherwise valid request ID where possible. Valid-format requests for an undeclared sector use `reason:"unknown_sector"`. The CLI must emit **one compact JSON object per physical request line** in file order, even for duplicate request IDs; no diagnostics on stdout. Bad catalogs fail before any output, with a diagnostic on stderr and nonzero exit status.

## Observable acceptance criteria

- Exactly one record per unique trip ID; identical retries do not inflate counts, and conflicting IDs invalidate the catalog. Row order must not matter.
- Geography and fare grouping follow the station/route/sector and fare/family declarations, including multiple stations on one route and multiple fares in one family.
- Slot 3 and slot 4 are in **different hours**. Slot 95 and slot 96 are in **different days**. Filter using the original half-open query window **before** generalization.
- Groups of size `k-1` are suppressed in full; those of size `k` survive. For an `ok` response, `released+suppressed=records`.
- A plan that suppresses **all** trips is invalid even if it fits the budget. An originally empty window is a distinct `empty` case.
- Optimize loss before suppression count. With zero weights, zero penalty and equal loss, the remaining tuple elements break ties deterministically.
- A malformed request, invalid numeric type or window, unknown sector, or repeated request ID does not poison later independent lines. CSV errors fail atomically.

## Production constraints

The checked-in fixture is compact. A production export may have **1.2 million distinct trips, 900 stations, 80 fare products, 60 sectors, and 70,000 release reviews**. Trips skew toward commuter intervals and busy sectors; reviews have arbitrary quarter-hour boundaries and different `k`, weights and budgets. Aim for **768 MB memory and under 100 ms p95 per typical review after snapshot load**, on one worker. These are design targets rather than fixture benchmarks.

Scanning every trip for every candidate plan on every request is not credible at this scale. Explain how to reuse computation and reason about indexing/preprocessing cost, per-query complexity, dense and sparse windows, worst-case skew, and memory bounds. Correct verified slices and transparent tradeoffs are preferable to unverified one-shot implementations.

## Deliverable, scope, commands

Deliver the planner, focused tests you derive, and an explanation of correctness and complexity. Refactoring is allowed if CLI/error semantics remain unchanged. In scope: trip reconciliation, global generalization, entire-group suppression, exact optimization, input isolation and verification. Out of scope: actual identity-level anonymity guarantees, differential privacy, individual-level tracking, live updates, distributed infrastructure, UI, authentication and cross-week reporting.

Python **3.11+**, standard library only:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 transitsafe.py check --stations fixtures/stations.csv --fares fixtures/fares.csv --rides fixtures/rides.csv
python3 transitsafe.py plan --stations fixtures/stations.csv --fares fixtures/fares.csv --rides fixtures/rides.csv --queries fixtures/requests.jsonl
```

The provided planner returns `not_implemented` for valid queries; passing the baseline tests **does not** meet the customer contract.

## 60-minute AI-assisted interview

**You have 60 minutes. AI use is explicitly encouraged** (Claude Code, Codex, ChatGPT, etc.). Inspect fixtures and requirements first, choose and defend your approach, implement incrementally, verify adversarial examples you devise, and explain runtime, memory, edge cases, and any AI-generated code you accepted or rejected. This is a customer issue, not an algorithm memorization exercise.
