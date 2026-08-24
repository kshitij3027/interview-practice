# RoutePolicy — One-Hour AI-Assisted Problem-Solving Interview

## Customer context

A payments platform lets enterprise customers configure routing policies for transaction events. A policy can send a matching transaction to a processing lane (for example `risk-review`, `low-cost`, or `premium`) or block it.

Policies match a hierarchical transaction path such as:

`payments/card/visa/recurring`

Customers need broad policies ("all card traffic") and narrow overrides ("Visa recurring only"), so the policy language supports literal path segments plus wildcards. The current implementation scans every policy for every transaction. That has become unusable as several customers approach production scale.

You are given representative policies and requests and asked to build the resolver that chooses the single effective policy for each request.

## Supplied data

### `fixtures/rules.csv`

Each row contains:

- `rule_id` — unique identifier
- `tenant` — exact tenant ID or `*`
- `region` — exact region or `*`
- `path_pattern` — slash-separated pattern
- `valid_from` — inclusive UTC timestamp
- `valid_to` — exclusive UTC timestamp, or empty for no expiry
- `priority` — integer
- `action` — `route` or `block`
- `destination` — required for `route`, empty for `block`

Path-pattern syntax:

- a literal segment matches itself;
- `*` matches exactly one segment;
- `**` matches zero or more complete segments;
- a pattern contains at most one `**`;
- matching is against the entire path, not merely a prefix.

Examples:

- `payments/card/*/recurring`
- `payments/**/chargeback`
- `**`
- `payments/card/visa/recurring`

### `fixtures/requests.jsonl`

Each line contains:

- `request_id`
- `tenant`
- `region`
- `event_time` — UTC timestamp
- `path`

## Goal

Implement the policy resolver in `resolver.py`.

For each request, return the single policy that wins according to the matching and precedence rules below. The same static rule set is used for many requests, so you may preprocess it once before resolving requests.

The intended deliverable is code you could plausibly explain to a customer and evolve toward the production constraints below.

## Observable requirements

A rule is eligible only when all of the following are true:

1. Its tenant is either `*` or exactly the request tenant.
2. Its region is either `*` or exactly the request region.
3. `valid_from <= event_time < valid_to`; an empty `valid_to` means no expiry.
4. Its `path_pattern` matches the request path using the wildcard semantics above.

If multiple rules are eligible, choose exactly one using this precedence order:

1. Higher `priority`.
2. More literal path segments.
3. Fewer `**` segments.
4. Fewer `*` segments.
5. Exact tenant scope over tenant `*`.
6. Exact region scope over region `*`.
7. Lexicographically smaller `rule_id`.

All comparisons above are applied in order. Input row order must never affect the result.

For every request, emit one JSON object:

```json
{
  "request_id": "req-001",
  "matched_rule_id": "r-102",
  "action": "route",
  "destination": "risk-review"
}
```

If no rule matches, emit:

```json
{
  "request_id": "req-002",
  "matched_rule_id": null,
  "action": "default",
  "destination": null
}
```

Additional required behavior:

- Duplicate rows with the same `rule_id` and identical contents should be accepted once.
- Reusing the same `rule_id` with conflicting contents is invalid input and must fail fast with a useful error.
- Empty path segments are invalid (`payments//visa`) in both rules and requests.
- `*` and `**` are wildcard tokens only when the entire segment is exactly that token. A segment like `visa*` is a literal string.
- Rules whose `valid_to <= valid_from` are invalid.
- Timestamps must be interpreted as UTC-aware times. Reject malformed or timezone-less timestamps rather than silently guessing.
- A `route` rule without a destination, or a `block` rule with a destination, is invalid.
- The resolver must be deterministic across repeated runs.

## Production shape

The fixture is intentionally small. Design the core for approximately:

- 1,500,000 policies loaded at process startup;
- 20,000,000 request resolutions per day;
- typical path depth: 4–12 segments, hard maximum 32;
- about 65% literal-only patterns, 25% containing `*`, 10% containing one `**`;
- 30,000 tenants and 12 regions;
- many broad wildcard policies shared across tenants;
- memory budget: 512 MB;
- target p95 resolver latency after startup: under 5 ms on typical requests.

A production-credible design should not scan all policies for each request or precompute all possible concrete paths. Be prepared to explain the preprocessing/query-time tradeoff and what behavior could become pathological.

## Expected deliverable

Complete `resolver.py`. You may add focused tests and small helper modules.

Your walkthrough should explain:

- how you model matching and precedence;
- how preprocessing avoids a full policy scan per request;
- expected startup memory/time and per-request complexity;
- how your design handles `**` without producing incorrect duplicate matches or unbounded work;
- which fixture cases you used to verify correctness;
- what you would measure before claiming the production target is met;
- whether an LLM, heuristic, or hybrid component would help this problem, and why.

## In scope

- Python standard library.
- Preprocessing/indexing of the static policy set.
- Focused unit or integration tests.
- A deterministic, heuristic, or hybrid design if you can justify its correctness against the stated behavior.

## Out of scope

- Persistent databases.
- Distributed caches.
- Network services.
- Policy mutations while the process is running.
- Authentication/authorization.
- A web UI.

## Run / verify

Baseline checks:

```bash
python3 -m unittest -v
python3 resolver.py --help
```

After implementing the resolver:

```bash
python3 resolver.py \
  --rules fixtures/rules.csv \
  --requests fixtures/requests.jsonl
```

Write one JSON object per request to stdout. Diagnostic logging should go to stderr.

## 60-minute interview instruction

You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or other AI tools as you would on the job.

Start by inspecting the fixtures and constraints. Decide what must be correct first, choose a data representation and lookup strategy, implement incrementally, and verify the difficult cases you think matter most.

The interviewer is evaluating problem decomposition, correctness, scaling judgment, test strategy, and your ability to explain and defend the code. Do not spend the hour polishing CLI ergonomics.
