# PromoScope — One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

A commerce platform serves millions of product-detail and checkout requests per hour. Merchandising teams define promotions at different levels of the catalog: some target one product, while others target an entire category subtree. Promotions also have regional scope and active time windows.

Today, the pricing service evaluates promotions with a slow fallback that scans too many definitions. That worked when there were a few thousand rules, but the catalog and campaign count have grown enough that tail latency is now visible to customers.

You have been asked to build an in-process promotion resolver that can load one static catalog snapshot and answer many independent quote-time lookup requests quickly and deterministically.

## Supplied data

### `fixtures/categories.csv`

Columns:

- `category_id` — globally unique category identifier.
- `parent_id` — empty for a root category, otherwise the immediate parent category.
- `name` — display-only label.

The hierarchy may contain multiple roots. A product belongs to exactly one category. A promotion targeting a category applies to products in that category and all of its descendants.

### `fixtures/products.csv`

Columns:

- `product_id` — globally unique product identifier.
- `category_id` — the product's current category in this snapshot.
- `seller_id` — informational for this exercise.

### `fixtures/promotions.csv`

Columns:

- `promotion_id` — globally unique logical promotion identifier.
- `target_type` — `product` or `category`.
- `target_id` — a product ID or category ID according to `target_type`.
- `region` — an exact region such as `us` / `eu`, or `*` for all regions.
- `starts_at` — inclusive RFC3339 timestamp.
- `ends_at` — exclusive RFC3339 timestamp.
- `priority` — signed integer business priority; larger wins earlier in the precedence rules below.
- `discount_bps` — integer basis points from 0 through 10000. It is output metadata; a larger discount does not automatically win.

An exact duplicate row with the same `promotion_id` is a harmless replay and should behave as one definition. Conflicting rows that reuse the same `promotion_id` are invalid data.

### `fixtures/queries.jsonl`

Each line is one independent request:

- `request_id`
- `product_id`
- `region`
- `as_of`

Queries do not mutate the catalog or affect one another.

## Goal

For each query, return the single winning active promotion for that product, region, and timestamp.

A promotion is a candidate when all of the following are true:

1. its target is either the queried product itself or a category that contains the product through the supplied category hierarchy;
2. its region is `*` or exactly equals the query region; and
3. `starts_at <= as_of < ends_at`.

If several promotions are candidates, choose one using these precedence rules **in order**:

1. higher `priority` wins;
2. subject to equal priority, a direct `product` target beats every category target;
3. subject to the first two rules, among category targets the deeper matching category wins;
4. subject to the rules above, an exact-region promotion beats a `*` promotion;
5. subject to the rules above, the promotion with the later `starts_at` wins;
6. if still tied, choose the lexicographically smallest `promotion_id`.

These rules deliberately do **not** choose the largest discount.

## Observable behavior

For a successful match, emit one JSON object:

```json
{
  "request_id": "q-001",
  "status": "matched",
  "promotion_id": "promo-123",
  "discount_bps": 750,
  "scope": "category:laptops"
}
```

If the product exists but no promotion is active and applicable:

```json
{"request_id":"q-009","status":"no_match"}
```

If the query references an unknown product:

```json
{"request_id":"q-010","status":"invalid","reason":"unknown_product"}
```

Additional requirements:

1. Promotion windows are half-open. A promotion is active exactly at `starts_at` and inactive exactly at `ends_at`.
2. Category applicability is inherited through all ancestors, not only the product's immediate category.
3. Exact region matching is case-sensitive; `US` and `us` are different regions.
4. A direct product promotion still loses to a category promotion with strictly higher priority because priority is evaluated first.
5. A deeper category wins only after priority and direct-product specificity have tied appropriately.
6. Reordering any input CSV must not change results.
7. Exact duplicate promotion rows behave as one logical promotion. Conflicting definitions for one `promotion_id` must fail validation.
8. Duplicate category IDs or product IDs are invalid.
9. Category parent references must exist. Cycles in the category hierarchy are invalid and must fail validation.
10. Products must reference known categories.
11. Promotion targets must exist, windows must have positive duration, and `discount_bps` must be within 0–10000.
12. Timestamps with offsets must be compared as instants, not as raw strings.
13. Parse and preprocess the static catalog once, then reuse that state across all queries.
14. Output one result per query in input order. Diagnostic logging should go to stderr rather than corrupting JSON output.

## Production constraints

The checked-in fixture is intentionally small. Design for approximately:

- 250,000 categories across multiple trees;
- 8 million products;
- 1.5 million active/future promotion definitions in one process snapshot;
- category depth usually below 12, but up to 40;
- 5–15 million resolution queries per hour per process;
- a few root or high-level categories may each have 100,000+ promotion windows because of campaign history and scheduled future campaigns;
- promotion snapshots are rebuilt outside this process; you do not need live mutation support;
- memory budget: 768 MB;
- target p95 resolution latency: under 10 ms after startup.

A production-credible solution should not scan all promotions for every query, rebuild category ancestry per request, or linearly scan the complete promotion history of a hot root category. Think about what can be indexed once and what information a single query actually needs.

You may choose an exact deterministic strategy, a carefully bounded heuristic, or a hybrid approach if you can explain the correctness/performance tradeoff. An LLM is not required for the critical lookup path, but you may argue for one if you believe it adds value without violating the observable contract and latency target.

## Expected deliverable

Implement `Resolver.Resolve` in `internal/resolver/resolver.go` and wire/extend supporting structures as needed so:

```bash
go run ./cmd/promoscope resolve \
  --categories fixtures/categories.csv \
  --products fixtures/products.csv \
  --promotions fixtures/promotions.csv \
  --queries fixtures/queries.jsonl
```

emits one JSON result per query.

Add focused tests for the correctness risks you consider most important. Be prepared to explain:

- what reusable indexes you build at startup;
- how you identify all applicable scopes for one product;
- how you find promotions active at one timestamp without scanning large histories;
- how the precedence rules are represented without accidentally changing their order;
- startup complexity, per-query complexity, and memory use;
- how skewed high-level categories affect your design;
- which malformed-data and boundary cases you verified;
- whether an approximate, heuristic, or AI-assisted design is appropriate here and why.

## Verification / run commands

No third-party dependencies are required.

Baseline checks before making changes:

```bash
go test ./...
go vet ./...
go run ./cmd/promoscope validate \
  --categories fixtures/categories.csv \
  --products fixtures/products.csv \
  --promotions fixtures/promotions.csv \
  --queries fixtures/queries.jsonl
```

After implementing the resolver:

```bash
go run ./cmd/promoscope resolve \
  --categories fixtures/categories.csv \
  --products fixtures/products.csv \
  --promotions fixtures/promotions.csv \
  --queries fixtures/queries.jsonl
```

## Scope / out of scope

In scope: one immutable catalog snapshot, hierarchy validation, reusable in-memory preprocessing, exact observable resolution semantics, focused tests, and complexity reasoning.

Out of scope: applying discounts to money values, stacking multiple promotions, seller-specific targeting, persistent databases, distributed caches, live campaign mutation, authentication, and web UI work.

## 60-minute AI-assisted interview instruction

You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or other AI tools as you would on the job, but inspect the fixtures and starter code yourself before delegating changes.

First write down the precedence rules and boundary semantics in your own words. Then choose the smallest implementation that can be made correct and explain how you would evolve it to the production constraints. Verify at least one hierarchy-specific case, one time-boundary case, and one precedence tie before finishing.

The interviewer is evaluating how you translate a customer latency problem into a technical model, how you recognize which data should be preprocessed, how you use AI without trusting it blindly, and whether you can explain both correctness and scalability.
