# BridgePlan — One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

A data-integration company helps enterprise customers move datasets between schema versions used by CRMs, warehouses, billing systems, and analytics tools. The platform has a catalog of reusable **adapters**. Each adapter converts one schema into another and has measurable tradeoffs: execution latency, per-record cost, and expected fidelity loss.

A customer may need to migrate from one schema to another while staying inside contractual limits on latency and data-quality loss. Several conversion chains may exist, and an adapter that looks attractive locally can lead to a dead end or make the final chain violate a budget.

Today, engineers inspect the adapter catalog by hand. The customer wants an in-process planner that can answer many migration requests against the same catalog quickly and deterministically.

## Supplied data

### `fixtures/schemas.csv`

Each row contains:

- `schema_id` — globally unique schema/version identifier.
- `system` — source product family, such as `crm`, `warehouse`, or `billing`.
- `status` — `active` or `deprecated`.

Deprecated schemas may still appear as a request's source or target and may still participate in a chain; the field is informational for this exercise.

### `fixtures/adapters.csv`

Each row describes one directed conversion:

- `adapter_id` — globally unique logical adapter identifier.
- `from_schema`
- `to_schema`
- `region` — an exact region such as `us` / `eu`, or `*` for globally available.
- `latency_ms` — non-negative integer added to total chain latency.
- `quality_loss_ppm` — non-negative integer added to total expected fidelity loss, in parts per million.
- `cost_micros` — non-negative integer execution cost in micro-dollars per representative batch.

The same pair of schemas can have several distinct adapters with different tradeoffs. Cycles in the catalog are allowed. The fixture also contains an exact duplicate row representing a harmless catalog replay.

### `fixtures/requests.jsonl`

Each line is an independent planning request:

- `request_id`
- `from_schema`
- `to_schema`
- `region`
- `max_latency_ms` — inclusive total latency budget.
- `max_quality_loss_ppm` — inclusive total fidelity-loss budget.
- `max_adapters` — inclusive maximum number of adapters in the chain.
- `disabled_adapters` — adapter IDs temporarily unavailable for this request; duplicates may appear.

Requests are independent. Do not carry state from one request into another.

## Goal

Implement the migration planning capability so each request returns the best feasible adapter chain under that request's constraints.

An adapter is eligible for a request only when:

1. its `region` is `*` or exactly matches the request region;
2. its `adapter_id` is not disabled for the request; and
3. both endpoint schemas exist in the supplied schema catalog.

For a candidate chain, totals are the sum of the adapters' `latency_ms`, `quality_loss_ppm`, and `cost_micros`. A chain is feasible only when all three request limits are satisfied: total latency, total quality loss, and number of adapters.

Among all feasible chains, choose the winner using these objectives **in order**:

1. minimize total `cost_micros`;
2. subject to (1), minimize total `quality_loss_ppm`;
3. subject to (1–2), minimize total `latency_ms`;
4. subject to (1–3), minimize adapter count;
5. if still tied, choose the lexicographically smallest sequence of `adapter_id` values.

The empty chain is valid when `from_schema == to_schema`; its totals are all zero.

## Observable requirements

For a successful request, emit one JSON object like:

```json
{
  "request_id": "req-001",
  "status": "planned",
  "adapter_ids": ["a-12", "a-44"],
  "schemas": ["crm-v1", "bridge-v2", "warehouse-v3"],
  "total_cost_micros": 6100,
  "total_quality_loss_ppm": 120,
  "total_latency_ms": 88
}
```

If no feasible chain exists, emit:

```json
{"request_id":"req-009","status":"unreachable"}
```

If the request references an unknown source or target schema, emit:

```json
{"request_id":"req-010","status":"invalid","reason":"unknown_schema"}
```

Additional rules:

1. Budget boundaries are inclusive: totals equal to a maximum are allowed.
2. Disabled-adapter IDs that are unknown to the catalog are ignored; duplicate IDs behave like one disabled ID.
3. An exact duplicate adapter row must not cause duplicate work or duplicate output choices.
4. If the same `adapter_id` appears with conflicting field values in the input catalog, dataset validation must fail rather than silently choosing one definition.
5. Cycles must not make planning non-terminating.
6. Output must be deterministic and independent of CSV row order, dictionary iteration order, or process hash randomization.
7. A request with `max_adapters = 0` can succeed only when source and target are the same schema.
8. The planner must consider tradeoffs between intermediate states. A partial chain that is cheaper to an intermediate schema is not automatically preferable if it consumes more latency or quality budget needed later.
9. Parse and preprocess the static schema/adapter catalog once, then answer all requests using that reusable state.

## Production constraints

The checked-in fixture is intentionally small. Design for this production shape:

- ~50,000 schemas;
- ~400,000 adapter definitions after deduplication;
- 5,000–20,000 migration requests per planner process;
- typical `max_adapters`: 4–12;
- latency budgets usually below 5,000 ms and quality-loss budgets below 50,000 ppm;
- 512 MB memory budget;
- target p95 request planning latency under 150 ms after startup for typical requests.

A solution that enumerates every simple chain, copies the full catalog per request, or keeps only one globally "best" partial route for each schema without accounting for remaining budgets is not production-credible.

You may preprocess reusable indexes at startup and may cache exact repeated queries if you can defend invalidation and memory behavior.

## Expected deliverable

Implement `MigrationPlanner.plan(request)` in `migration/planner.py` and wire the existing `plan` CLI path so every request in a JSONL file emits one JSON result in input order.

Your solution strategy is yours. A deterministic algorithmic solution, a heuristic with a clearly stated correctness tradeoff, or another approach can be discussed, but the observable requirements above are the evaluation contract.

Add focused tests for the correctness risks you consider most important. Be prepared to explain your data structures, why your search state is sufficient, and the expected time/memory behavior.

## Setup and verification

No third-party dependencies are required.

Baseline checks:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q migration bridge_plan.py tests
python3 bridge_plan.py validate \
  --schemas fixtures/schemas.csv \
  --adapters fixtures/adapters.csv \
  --requests fixtures/requests.jsonl
```

After implementing the planner:

```bash
python3 bridge_plan.py plan \
  --schemas fixtures/schemas.csv \
  --adapters fixtures/adapters.csv \
  --requests fixtures/requests.jsonl
```

## Scope / out of scope

In scope: deterministic in-process planning against the supplied static catalog, request-specific region/disable/budget constraints, and production-credible complexity reasoning.

Out of scope: executing adapters, distributed scheduling, persistent databases, live catalog mutation while the process is running, authentication, UI work, and external LLM/API calls.

## 60-minute interview instruction

You have **60 minutes**. Use AI tools as you would on the job, but inspect the repository and fixtures yourself before delegating changes. Identify the failure modes of a simplistic approach, implement incrementally, run focused verification, and be ready to explain why your solution remains correct under the simultaneous constraints rather than only on the fixture's happy path.
