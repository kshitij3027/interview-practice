# FreshClaim — HARD 60-minute AI-assisted customer interview

## The customer problem

A grocery pickup platform promises shoppers **complete orders**, not partial bags. Fresh batches arrive throughout the day and must be allocated before they expire. The current tool totals stock once per SKU and occasionally promises three pickups that cannot all be filled: some stock arrives after an earlier pickup, some expires before a later one, and an order only counts if **all** of its units can be reserved.

Build **one pickup-promise assessment capability**: for an independent what-if basket of scheduled orders for a single store and SKU, determine the **best subset of complete orders that can be fulfilled** from that store's batch inventory. You choose the technical strategy. Exact deterministic, heuristic, LLM-assisted or hybrid approaches may be proposed, but a successful response must satisfy the exact optimization and feasibility contract. No external API or model is required.

## Data to inspect

- `fixtures/lots.csv`: `lot_id,store_id,sku,ready_min,expiry_min,units` is a fixed inventory snapshot. A batch may be used across several pickups, up to its total units, but cannot be used before `ready_min` or at or after `expiry_min`. Distinct lots may have identical metadata; their units are additive.
- `fixtures/requests.jsonl`: independent hypothetical order baskets, one request per *physical line*. Some lines are intentionally invalid. Repeated request IDs are independent.
- `freshclaim/catalog.py`, `freshclaim/cli.py`, `freshclaim/engine.py`, `freshclaim.py`: running loader, CLI, validation and unfinished assessor.
- `tests/`, `scripts/`: working baseline verification, not full customer acceptance tests.

A stock batch is identified by a case-sensitive ASCII ID (letters, digits, underscore or hyphen, 1–48 chars). Store and SKU use the same syntax. A valid lot has canonical unsigned decimal `ready_min`, `expiry_min`, `units`; `0 <= ready_min < expiry_min <= 1000000000`, `0 <= units <= 1000000`. CSV columns must be **exactly** those listed, in any order. Repeated *identical* rows for a `lot_id` are delivery retries and do not double stock. Reusing the same lot ID with different data, malformed rows, or invalid numeric notation invalidates the **whole catalog** before any request produces output. Every store/SKU pair in the lot catalog is known even when its current units sum to zero. The CSV may contain lots in arbitrary order.

## Your one primary deliverable

Implement `FreshClaim.assess(request)` in `freshclaim/engine.py` (plus justified preprocessing). A valid request looks like:

```json
{"request_id":"offer-17","store_id":"OAK","sku":"APPLE","orders":[{"order_id":"ORD-A","pickup_min":4,"units":5},{"order_id":"ORD-B","pickup_min":9,"units":7}]}
```

`request_id` is a valid ASCII ID of length 1–128. Each `orders` array has **0–12** objects. Each order has a **unique** `order_id` (1–48 character ID), an actual JSON integer `pickup_min` in `[0,1000000000]`, and an actual JSON integer `units` in `[1,1000000]`. JSON booleans, floats and numeric strings are **not integers**. Extra object fields may be ignored. All orders in a request concern the same store/SKU; no standing reservations from other requests are carried over. There are no within-day transfers between stores or SKU substitutions.

For each order that is accepted, reserve all its units from one or more eligible lots at its *fixed* `pickup_min`. A lot is eligible exactly when `ready_min <= pickup_min < expiry_min`; its capacity is shared across all accepted orders in the basket. A lot may be split across different accepted orders, but **an order may not be partially fulfilled**. You may allocate inventory to an earlier scheduled order before a later order; the chosen subset must admit a consistent allocation across *every* accepted order, regardless of the input array order. No inventory is consumed by rejected orders.

Among **all feasible subsets of orders**, choose, in this strict order:

1. The **maximum number of complete orders**.
2. Among those, the **maximum sum of units in accepted orders**.
3. Among remaining ties, the **lexicographically smallest sorted array of accepted order IDs**, comparing case-sensitive strings.

For a valid basket from a known store/SKU, return exactly the following fields:

```json
{"request_id":"offer-17","status":"ok","fulfilled_order_ids":["ORD-A"],"fulfilled_units":5,"unfilled_order_ids":["ORD-B"]}
```

This is illustrative of the **shape**, not an expected answer for the sample request. Both ID arrays must be sorted by case-sensitive lexicographic order; `fulfilled_units` must be exact. For empty orders the unique optimum is the empty subset, with zero units.

A malformed request, bad JSON line, duplicate order ID, wrong type, missing field, out-of-range value, or invalid identifier yields `{"request_id":null,"status":"invalid","reason":"invalid_query"}` (retain `request_id` only if its value is a syntactically valid request ID). A structurally valid request with no `(store_id,sku)` in the catalog returns `{"request_id":"...","status":"invalid","reason":"unknown_stock"}`. Unknown store/SKU takes precedence only **after** all request-structure validation. One bad line does not affect later lines. Emit **one compact JSON object per physical input line**, including empty lines, in order; stdout must contain no diagnostics. A bad catalog exits nonzero, reports stderr, and emits **no partial JSONL**.

## Observable acceptance criteria

- A batch arriving exactly at pickup time is usable; a batch expiring exactly at pickup time is not.
- A batch's units can be split but not reused beyond capacity across several pickup times; duplicate CSV retries are not new stock.
- Earlier promises cannot consume stock that is not yet ready; later promises cannot use expired stock. Input order must not change the optimum.
- Maximize **complete-order count before units**; a larger single order may lose to two smaller complete orders.
- For equal counts compare summed units, then compare sorted IDs. Repeated request IDs and harmless catalog reordering do not change results.
- Independent what-if baskets each start with the full immutable snapshot. Lots never transfer between stores or SKUs.
- Empty orders and zero-unit stock are valid. An order is never partially accepted. Infeasible baskets still return `ok` with their best feasible subset, possibly empty.
- Bad request lines are isolated; bad catalog input is atomic. Bounds, bool-as-int, malformed CSV, conflicting lot retries and duplicate order IDs matter.

## Scale, tradeoffs, and scope

Representative fixtures are small. Production contains up to **2 million lots**, **1,500 stores**, **60,000 store/SKU partitions**, and **50,000 independent baskets/day** of at most 12 orders each. A few hot SKUs have hundreds of thousands of lots; expiry and readiness times are highly skewed, and many orders share a pickup time. Target approximately **1.5 GB resident memory** and **p95 under 100 ms for typical baskets after inventory load** (design targets, not enforced by small fixture tests). Naively enumerating every possible lot-to-order allocation or rescanning all global stock for every basket is not adequate. Discuss worst-case behavior separately from typical workloads.

Use **Python 3.11+ standard library only**. Implement the assessor, add focused tests of your own, and defend correctness, indexing, worst-case work, ties, tradeoffs and limitations. You may refactor internals without breaking CLI contracts. Out of scope: user authentication, online inventory changes, shipping routes, real-time multi-request reservations, substitutions, UI and third-party platform integrations.

## Run and verify

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 freshclaim.py check --lots fixtures/lots.csv
```

Once the assessor is implemented:

```bash
python3 freshclaim.py assess --lots fixtures/lots.csv --requests fixtures/requests.jsonl
```

The supplied starter returns `not_implemented` for structurally valid requests. Green starter tests verify the plumbing, **not** correct customer fulfillment.

## 60-minute AI-assisted interview instruction

**You have exactly 60 minutes; using Claude Code, Codex, ChatGPT or similar tools is encouraged.** Inspect the actual fixture and constraints before coding. Own the solution choice rather than accepting an AI-generated architecture by default. Implement incrementally, test carefully chosen adversarial baskets, and explain the optimization rule, capacity correctness, complexity, scaling options and any AI-generated code you retained. You should be able to walk a customer through your design without relying on a black box.
