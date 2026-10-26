# AidLink — HARD 60-minute AI-assisted customer interview

## Customer / business context

A regional disaster-response organization distributes portable oxygen cylinders from emergency depots to clinics. Roads are represented as approved **direct shipment lanes**, each with its own carrying limit and transport cost. A clinic has two quantities of unmet demand: **critical** (patients at immediate risk) and **routine**. During a shortage, filling cheap or convenient destinations first can strand critical patients elsewhere.

Dispatch coordinators repeatedly run *what-if* plans as roads close, depots report updated stock, and clinics revise their needs. Their spreadsheet prototype simply chooses the cheapest available lane for each clinic in order; it routinely produces plans that look reasonable but waste capacity or neglect critical demand. They need an exact, explainable planning result, not just a plausible allocation.

You own the technical approach. AI/LLM-based, deterministic, heuristic, or hybrid implementations are all permitted, provided the observable contract is met. No external service or credentials are required.

## Supplied data

- `fixtures/depots.csv`: `depot_id,stock` — units currently available at each depot.
- `fixtures/clinics.csv`: `clinic_id,critical,routine` — each clinic's independent demand tiers.
- `fixtures/lanes.csv`: `lane_id,depot_id,clinic_id,capacity,cost_cents` — a one-way approved lane from one depot directly to one clinic. `capacity` is the maximum units on **that lane**, not a global per-destination cap. `cost_cents` is the integer cost **per shipped unit**. Separate lane IDs may connect the same endpoints, with independent limits/costs. There is no clinic-to-clinic or depot-to-depot movement.
- `fixtures/requests.jsonl`: one independent planning scenario per physical line. A valid object has `request_id` (nonempty string, at most 128 characters) and optional `disabled_lanes` (list of lane IDs), `stock_overrides` (object mapping depot ID to replacement stock), and `need_overrides` (object mapping clinic ID to an object with **both** `critical` and `routine` replacement quantities). Missing optional fields mean no changes. Duplicate entries in `disabled_lanes` have no additional effect. Overrides replace the base value; they are not increments. Scenario requests do not consume inventory for later requests, and repeated `request_id` values remain independent.

IDs in the CSVs and override references are case-sensitive, 1–40 ASCII letters, digits, `_`, or `-`. All catalog quantities and request override quantities are nonnegative integers at most 1,000,000; lane capacities are strictly positive. CSV integers must use ordinary base-10 digits without a sign or leading zeroes, except `0`. `cost_cents` may be zero. JSON numeric fields must be actual integers, never booleans, decimal numbers, or numeric strings. Extra JSON request fields may be ignored.

Identical duplicate catalog records (same ID and same full data) are harmless replay deliveries. Reusing an ID with conflicting data, malformed rows, missing required CSV headers, unknown lane endpoints, or malformed numeric fields invalidates the **entire** catalog before any responses. CSV header order may vary. Query failures instead affect only their own physical line.

## Primary customer request

Implement `plan(catalog, request)` in `aidlink_pkg/planner.py`, with supporting changes/tests as needed. For every scenario, provide a feasible shipment plan that satisfies **all three** business priorities, in order:

1. **Maximize total critical demand served** across every clinic.
2. Among plans with that maximal critical service, **maximize total routine demand served**.
3. Among plans satisfying both service priorities, **minimize total shipping cost** in integer cents.

Each cylinder shipped on a lane consumes one unit of that depot's stock, one unit of that lane's capacity, and one unit of the receiving clinic's total demand. At each clinic, incoming units cover its critical demand first, then its routine demand. Sending more than its combined need is invalid. Unused stock may remain at a depot; unmet demand is allowed when unavoidable. A cheaper plan is **not** better if it serves fewer critical units. No partial credit is given for proposing a non-optimal allocation.

Several different lane allocations may be equally optimal at all three priority levels; any such allocation is accepted, but your implementation must make a **repeatable, input-order-independent** choice (including when CSV row orders change). The `shipments` array itself must always be sorted by case-sensitive `lane_id`. Include **only** lanes receiving a positive integer quantity.

For a valid scenario emit exactly one compact JSON object with these fields (numbers below illustrate format only):

```json
{"request_id":"scenario-A","status":"planned","critical_served":8,"routine_served":3,"unmet_critical":2,"unmet_routine":4,"shipping_cost_cents":41,"shipments":[{"lane_id":"L-01","units":5},{"lane_id":"L-12","units":6}]}
```

Totals must match the shipment plan. `unmet_*` counts demand still uncovered after assigning each clinic's incoming units to critical first. `shipping_cost_cents` is the exact sum of lane units multiplied by each lane's per-unit cost. If nothing can ship, return zero served, all demand unmet, zero cost, and `shipments:[]`, still with `status:"planned"`.

## Observable acceptance criteria

- Emit one JSON object **per physical query line**, preserving the original order. No diagnostic logs on stdout. Invalid lines never block later scenarios.
- Malformed JSON, non-object requests, invalid `request_id`, invalid field types, malformed IDs, invalid numbers, or incomplete clinic-need overrides produce `{"request_id":null,"status":"invalid","reason":"invalid_request"}`. Preserve `request_id` instead of `null` whenever it is already a valid string.
- A syntactically valid request mentioning an unknown lane, depot, or clinic produces `status:"invalid",reason:"unknown_reference"` and preserves its `request_id`.
- Honor both stock limits and **individual** lane limits, including when parallel lanes share the same endpoints. Treat disabled lanes as unusable only for that request.
- Never allocate beyond a clinic's total critical-plus-routine need. Credit its critical need before routine; globally protect the critical tier even when a routine shipment would be cheaper.
- Find the best **whole-network** plan across all three priorities, even when taking a cheap lane early would prevent a better final allocation elsewhere.
- Handle zero-stock depots, zero-demand clinics, unreachable clinics, zero-cost lanes, supply shortages, excess stock, equal-cost alternatives, duplicate catalog deliveries, and revised scenario inputs.
- Make plans independent of CSV row ordering and prior request processing. All numeric arithmetic is exact integer arithmetic; identical inputs produce identical plans.
- Reject invalid catalogs promptly with a nonzero exit code and a useful stderr message, without emitting partial planned results.

## Production constraints

The checked-in snapshot is compact and designed for exploration. A realistic disaster response deployment may have **200 depots, 500 clinics, and 8,000 approved lanes**, with up to **1,000 independent what-if scenarios** using largely shared base data. Capacity and demand values may be large; an implementation that loops once per cylinder or exhaustively enumerates possible allocations is not credible. Aim for an in-memory solution (approximately **1 GB** available) and discuss what you would measure to determine whether typical scenarios can be answered within **2 seconds** on commodity hardware. If your chosen method needs preprocessing or degrades on skewed inputs, explain that explicitly.

## Scope / expected deliverable

In scope: the exact planner, feasible positive-quantity shipments, ordered business priorities, scenario overrides, deterministic output, invalid-request isolation, focused edge-case tests, and a defensible complexity/scaling discussion. The catalog loader, request parser, CLI, and starter tests are provided and already run. The core planner intentionally returns `not_implemented` for valid requests.

Out of scope: real route-finding on road maps, trucks/driver schedules, shipments between depots or between clinics, multi-day deliveries, persistence across runs, authentication, live supplier integrations, and a browser UI. Do not modify fixture rows to make a proposed plan pass.

## Setup, execution, and verification

Python 3.11+ and standard library only. From the repository root:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
```

After implementing the requested planner:

```bash
python3 aidlink.py plan \
  --depots fixtures/depots.csv \
  --clinics fixtures/clinics.csv \
  --lanes fixtures/lanes.csv \
  --requests fixtures/requests.jsonl
```

The green starter tests cover the catalog, query boundary, and CLI, **not** the requested planning optimization. Add independent tests for the business priorities and difficult allocation cases.

## 60-minute AI-assisted interview instruction

You have **60 minutes** to solve this customer issue. Use Claude Code, Codex, ChatGPT, or other AI tools as you would during a real engineering engagement. Inspect the data and constraints before choosing an approach, get a credible implementation working incrementally, verify outputs on nontrivial cases, and be prepared to explain tradeoffs to the interviewer. A happy-path or cheapest-lane-first implementation that ignores global constraints is intentionally insufficient.
