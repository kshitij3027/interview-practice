# MergeGuard — One-Hour AI-Assisted Problem-Solving Interview

## Customer context

A B2B commerce platform ingests customer records from CRM, billing, support, and product systems. The same real-world customer can appear under several source-specific IDs, so downstream teams maintain **link events** saying two records refer to the same customer.

The platform also receives **separation constraints** saying two records must never be merged. These come from verified account boundaries, contractual tenant isolation, fraud investigations, or explicit human review.

Today, every link event triggers a slow rebuild of the entire customer map. Worse, a bad link can silently connect two groups that contain a forbidden pair and corrupt downstream billing and permissions.

You are given representative records, initial separation constraints, and an ordered stream of link/query events. Build the in-memory reconciliation engine that can process the stream safely and deterministically.

## Supplied data

### `fixtures/records.csv`

- `record_id` — globally unique source record ID
- `source` — origin system such as `crm`, `billing`, `support`, or `product`
- `created_at` — UTC timestamp
- `quality_score` — integer 0–100; higher means more trusted
- `display_name` — descriptive text only; do not assume names are unique

### `fixtures/separations.csv`

Each row contains `record_a,record_b`.

The two records are known to represent different customers. Separation is symmetric. Duplicate rows and reversed duplicates may appear.

### `fixtures/events.jsonl`

Events are processed strictly in file order.

`link` event:

```json
{"event_id":"e-001","type":"link","left":"crm:100","right":"billing:900"}
```

`query` event:

```json
{"event_id":"e-002","type":"query","record_id":"crm:100"}
```

## Goal

Complete `merge_guard.py` so the process consumes the initial data once and then handles the event stream incrementally.

A successful link declares that the two records and **all records already connected to either one** represent the same customer.

A link must be rejected if accepting it would place any known separated pair in the same customer group.

Rejected links must be atomic: they may not partially change group membership, canonical IDs, or future behavior.

For each query, return the current group for that record and its deterministic canonical record.

## Observable requirements

For a `link` event, emit exactly one JSON object:

```json
{"event_id":"e-001","status":"accepted","group_size":3,"canonical_record_id":"billing:900"}
```

or:

```json
{"event_id":"e-007","status":"rejected","reason":"separation_conflict"}
```

For a `query` event, emit:

```json
{
  "event_id":"e-008",
  "record_id":"crm:100",
  "canonical_record_id":"billing:900",
  "members":["billing:900","crm:100","support:44"]
}
```

Rules:

1. Link events are transitive. If A is already linked to B and B is linked to C, A/B/C are one group.
2. A link between records already in the same group is accepted as a no-op and must not change the canonical record.
3. A link is rejected when **any** separation constraint crosses the two groups being joined, including a constraint between non-endpoint members.
4. Rejected links are fully atomic and must not alter later query results.
5. Separation rows are symmetric. Duplicate and reversed-duplicate rows must not create duplicate work or change behavior.
6. Self-separation (`A,A`) is invalid input and must fail fast.
7. Every record referenced by a separation or event must exist in `records.csv`; unknown IDs must fail fast with a useful error.
8. Link/query events have unique `event_id` values. Duplicate event IDs are invalid input.
9. Output member lists are lexicographically sorted.
10. The canonical record for a group is the member with the highest `quality_score`; ties choose the earliest `created_at`; remaining ties choose lexicographically smaller `record_id`.
11. Canonical choice must remain deterministic regardless of input row ordering.
12. The engine must preprocess static data once and process events incrementally. Rebuilding all groups or rescanning every separation row after each link is not production-credible.
13. The event stream may contain long chains of accepted links, many repeated no-op links, and rejected links between large existing groups.
14. If a link is rejected, a later different link may still be valid; rejection does not poison either group.

## Production shape

Design for approximately:

- 8,000,000 records;
- 22,000,000 accepted historical links loaded at startup;
- 4,000,000 separation pairs;
- 500,000 new link events per day;
- 15,000,000 group queries per day;
- median group size under 5, but a small number of enterprise groups may contain 100k+ records;
- 2 GB memory budget for this service;
- target p95 under 10 ms for typical link and query operations after startup.

A solution that scans every record, every group member on both sides, or all separation pairs for each link will not meet the intended production shape. Large-group edge cases matter even though the fixture is small.

You may choose deterministic, heuristic, LLM-assisted, or hybrid techniques, but observable correctness is exact. Be prepared to explain why any probabilistic or model-driven component is safe for the guarantees above.

## Expected deliverable

Implement the engine and CLI in `merge_guard.py`. You may add focused tests or small helper modules.

Your walkthrough should explain:

- how group membership is represented and updated;
- how you detect whether two existing groups can be safely joined;
- what work happens on successful versus rejected links;
- how canonical records stay correct as groups grow;
- expected startup, link, and query complexity;
- which fixture cases you used to verify atomicity and non-endpoint conflicts;
- where your design could become pathological at production scale;
- whether an LLM or heuristic component belongs in this solution, and why.

## In scope

- Python standard library.
- In-memory preprocessing/indexing.
- Focused tests.
- Additional small fixture cases if useful.

## Out of scope

- Persistent databases.
- Distributed coordination or cross-process consistency.
- Online modification of separation constraints.
- Fuzzy matching that invents new links from names.
- Authentication or UI work.

## Run / verify

Baseline checks:

```bash
python3 -m unittest -v
python3 merge_guard.py --help
```

After implementation:

```bash
python3 merge_guard.py \
  --records fixtures/records.csv \
  --separations fixtures/separations.csv \
  --events fixtures/events.jsonl
```

Write one JSON object per event to stdout. Diagnostic logging, if any, should go to stderr.

## 60-minute interview instruction

You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or other AI tools as you would on the job.

Start by inspecting the fixtures and constraints. Decide which invariants must never be violated before choosing an implementation. Work incrementally and verify both successful and rejected links.

The interviewer is evaluating problem decomposition, correctness under adversarial constraints, scaling judgment, test strategy, and your ability to explain and defend the implementation. Prioritize the reconciliation core over CLI polish.
