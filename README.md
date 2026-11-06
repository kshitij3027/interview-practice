# PulseRank — HARD 60-minute AI-assisted customer interview

## Customer / business context

An API platform provider supports enterprise customers in several regions. After a latency incident, its support team must answer questions like "Was the slow tail concentrated in our US gateway during this exact deployment window?" The telemetry export contains delayed revisions, retried rows, request cancellations, and calls that move between a service's regions after attribution corrections. A current diagnostic reads every request record for each investigation and becomes too slow when an enterprise drills into hundreds of overlapping time windows.

You own the technical strategy. Deterministic, heuristic, LLM-assisted, or hybrid techniques are all permitted if you can justify correctness, latency, memory use, explainability, and cost. No external credentials, network service, or SDK are required.

## Supplied data

- `fixtures/scopes.csv`: `service_id,region,budget_us`. Each row declares one service/region pair and its latency budget, measured in integer **microseconds**. The budget is inclusive: a call exceeding (not equaling) it is a breach.
- `fixtures/observations.csv`: `request_id,revision,op,service_id,region,at_ms,latency_us`. Records may be in any order. Every request ID denotes one logical API request; its **highest numeric revision** determines whether and where it contributes to investigations. `upsert` supplies all fields, while `cancel` requires all four fields after `op` to be blank. Cancellation without an earlier upsert is valid. An updated request may move into another service/region, change its timestamp, or change its latency. Revision numbers need not be consecutive.
- `fixtures/queries.jsonl`: one independent investigation per **physical** line, with intentional invalid examples. Every valid query contains `query_id,service_id,region,from_ms,until_ms`. Query results must be emitted in the same physical input order, even for duplicate `query_id` values.

IDs (`request_id`, `query_id`, `service_id`, `region`) are case-sensitive ASCII letters, digits, hyphens, or underscores, 1–48 characters long (`query_id` up to 128). CSV integers are canonical unsigned decimal digits, without leading zeros except `0`. `revision` is in `[1,10^9]`, `at_ms` in `[0,10^12]`, `latency_us` and `budget_us` in `[0,10^9]`. Each query window is nonempty, with JSON integer endpoints satisfying `0 <= from_ms < until_ms <= 10^12`. JSON floats, numeric strings, and booleans are **not** integers. CSV column order can vary.

Identical scope rows and identical replays of `(request_id,revision)` are harmless. Conflicting values for an identical scope or request/revision pair, malformed CSV rows, bad references, or invalid observation fields fail the **whole snapshot** before producing any query output—even if a higher revision later supersedes the bad row. A syntactically valid query referencing an undeclared service/region pair is an **isolated** `unknown_scope` error; malformed query lines are isolated `invalid_query` errors and do not suppress later queries. Additional JSON keys may be ignored.

## Primary customer request

Implement `LatencyAudit.assess(query)` in `pulserank/engine.py`, with other changes as needed. For the exact `(service_id,region)` and half-open investigation period `[from_ms,until_ms)`, consider only the **latest live revision** of each request. A request at `from_ms` is included; one at `until_ms` is excluded. Return **exactly** these fields:

```json
{"query_id":"illustrative","status":"ok","count":5,"p50_us":90000,"p95_us":420000,"over_budget":2,"slowest_request_id":"req_9"}
```

The values above are illustrative, **not fixture answers**. Define percentiles by nearest rank: for `n > 0`, sort all included latency values ascending and choose the element at **one-based position `ceil(p*n/100)`**, for p=50 and p=95. Do not interpolate or average. `over_budget` counts observations with `latency_us > budget_us` of the requested service/region. `slowest_request_id` is the included request with greatest latency, breaking ties by **earlier `at_ms`**, then by case-sensitive lexicographically smaller `request_id`. For an empty window, return `count:0`, `p50_us:null`, `p95_us:null`, `over_budget:0`, and `slowest_request_id:null`.

For valid queries the existing CLI calls your method and emits one compact JSON object per line. Errors must have exactly `{"query_id":null,"status":"invalid","reason":"invalid_query"}` or `{"query_id":"q","status":"invalid","reason":"unknown_scope"}` as appropriate; preserve a syntactically valid `query_id` when possible. No diagnostics on stdout. For bad catalog input, exit nonzero and print a useful stderr diagnostic **without emitting any query results**.

## Observable acceptance criteria

- Results are independent of observation CSV order, identical delivery retries, query order, and duplicate query IDs. Each logical request contributes at most once at its newest live revision; a newer cancellation removes it entirely.
- A newer upsert can move a request between service/region pairs or from inside one query window to outside it. Older revisions must not reappear.
- The exact half-open timestamp boundary matters, including windows with no data, many tied timestamps, a single observation, and calls exactly at `until_ms`.
- Nearest-rank p50/p95 are computed on **all matching latencies, including ties and zeros**; rank and breach counts are exact integers, not floating-point approximations. Equal-to-budget latency is not a breach.
- Tied slowest durations use the earliest observation timestamp and then the smaller request ID; never rely on input order, language iteration order, or an arbitrary winner.
- Invalid catalog entries reject the entire snapshot without partial output. Invalid JSON, invalid query fields and numeric types, unknown pairs, and empty windows produce one correctly categorized error each while later valid queries still work.
- Query results are stable for broad, narrow, overlapping, repeated, and totally idle windows. Large percentile populations must not overflow fixed-width arithmetic.

## Scale / constraints

Production exports may contain **2 million revision rows**, **600,000 latest live requests**, **6,000 service/region scopes**, and **250,000 independent investigation windows**, heavily skewed to several busy scopes. Timestamp domains are sparse and can span the full stated range. Aim for approximately **1 GB working memory** and **p95 under 30 ms for ordinary investigation queries after snapshot preparation** on a commodity host; these are targets for defending a design, not fixture benchmarks. Full data preparation in advance is allowed. Re-reading every observation or sorting all matching requests from scratch for every query is not credible at production query volumes. Explain preprocessing cost, per-query complexity, memory use, bottlenecks, and when any tradeoffs are acceptable.

## Deliverable and scope

Build a correct, explainable audit capability, add adversarial tests beyond the starter tests, and be prepared to walk through complexity and edge cases. You may refactor the supplied parser, CLI, and interfaces if needed but must preserve the observable contract and scripts. The starter validates catalogs and requests and handles output-line isolation; percentile audit behavior is deliberately **not** implemented.

In scope: snapshot reconciliation, exact range statistics, deterministic tie breaking, robust input boundaries, repeat-query performance, and verification. Out of scope: live event ingestion after startup, streaming websockets, visualization, database or network infrastructure, authentication, approximate quantiles, forecasting, and distributed systems.

## Setup / run / verification

Python **3.11+**, **standard library only**. From this branch's root:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 pulserank.py check --scopes fixtures/scopes.csv --observations fixtures/observations.csv
```

After implementing the audit engine, run:

```bash
python3 pulserank.py audit --scopes fixtures/scopes.csv --observations fixtures/observations.csv --queries fixtures/queries.jsonl
```

The baseline tests check existing parsing, revision selection, interfaces, and CLI behavior; they are intentionally **not** comprehensive acceptance tests for the requested feature.

## 60-minute AI-assisted interview instruction

You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or another AI tool as you would with a real customer problem. Inspect the actual fixture and interfaces first, choose and explain a solution strategy, implement an incrementally verifiable slice, run realistic and adversarial checks, and be ready to defend runtime, memory, correctness invariants, error handling, and any AI-produced code you retain. The goal is customer-worthy problem solving, not memorizing a particular technique.
