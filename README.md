# EdgeRoute — One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

A B2B API platform runs a multi-tenant edge gateway in front of hundreds of internal services. Teams register routing rules that match an incoming request by hostname, HTTP method, and path. The gateway then forwards the request to the winning upstream service.

The original implementation linearly scanned a small routing table. The platform now has enough customer-specific, wildcard, and legacy fallback rules that this approach is consuming noticeable CPU and creating tail-latency spikes on hot hosts.

You have been asked to build an in-process route resolver that loads one immutable routing snapshot and answers many independent requests quickly and deterministically.

This is a customer-style systems problem, not a memorization exercise. Use AI tools as you would on the job, but you own the technical approach and must be able to explain its correctness and scaling behavior.

## Supplied data

### `fixtures/routes.csv`

Each row defines one logical route:

- `route_id` — globally unique logical identifier.
- `host_pattern` — one of an exact host such as `api.acme.com`, a suffix wildcard such as `*.acme.com`, or `*` for all hosts.
- `method` — an uppercase HTTP method such as `GET`, or `ANY`.
- `path_pattern` — a canonical path pattern described below.
- `priority` — signed integer business priority.
- `upstream` — destination service name returned to the caller.

An exact duplicate row with the same `route_id` is a harmless catalog replay and behaves as one definition. Reusing a `route_id` with different fields is invalid data.

### Path pattern language

A path is split into `/`-separated segments. A pattern segment may be a literal such as `orders`, a named parameter such as `{order_id}` which matches exactly one segment and captures it, `*` which matches exactly one segment without capturing it, or `**` which matches zero or more remaining segments and may appear only as the final pattern segment.

`/` is the root path and has zero segments. Patterns and request paths are canonical: they start with `/`, contain no repeated `/`, contain no query string or fragment, and have no trailing slash except for `/` itself. Literal path matching is case-sensitive. No URL-decoding step is required; compare the supplied segment strings as they appear. Named parameters within one pattern must have unique names.

### `fixtures/queries.jsonl`

Each line is one independent request containing `request_id`, `host`, `method`, and `path`. Requests do not mutate the catalog or affect one another.

Host matching is case-insensitive. Ignore one terminal `.` on a request host before matching. A suffix wildcard such as `*.acme.com` matches `shop.acme.com` and `eu.shop.acme.com`, but does not match the bare host `acme.com`.

## Goal

For each request, return the single winning route and any named path-parameter captures. A route is a candidate only if its host pattern, method, and path pattern all match the request. Method `ANY` matches every valid request method. An exact method matches only itself.

### Winner precedence

If multiple routes match, choose one by applying these rules in order:

1. higher `priority` wins;
2. subject to equal priority, a more specific host wins: exact host > suffix wildcard > global `*`;
3. subject to the rules above, among matching suffix-wildcard hosts, the one with the longer literal suffix wins;
4. subject to the rules above, an exact HTTP method beats `ANY`;
5. subject to the rules above, compare path-pattern segments from left to right using this specificity order: literal > named parameter > `*` > `**`; the first differing segment decides;
6. if one path-specificity sequence is otherwise an exact prefix of another, prefer the route with more non-`**` pattern segments; if those are still tied, prefer the route without `**`;
7. if everything above is still tied, choose the lexicographically smallest `route_id`.

Priority deliberately comes before specificity. A broad high-priority emergency route can therefore beat a more specific lower-priority route.

## Observable behavior

For a successful match, emit one JSON object like:

```json
{"request_id":"q-001","status":"matched","route_id":"r-users","upstream":"user-service","params":{"id":"42"}}
```

For a matched route with no named parameters, return an empty object for `params`. If no route matches, emit `{"request_id":"q-009","status":"no_match"}`. If an individual query has an invalid host, method, or non-canonical path, emit `{"request_id":"q-010","status":"invalid","reason":"invalid_request"}` and continue processing later queries normally.

## Required behavior and edge cases

1. Output one result per query in input order.
2. Reordering `routes.csv` must not change any result.
3. Host matching is case-insensitive; path matching is case-sensitive.
4. `*.example.com` requires at least one label before `example.com`.
5. `**` may match zero segments; `/files/**` matches `/files` as well as `/files/a/b`.
6. Named parameters capture exactly the segment they match. `*` and `**` do not create captures.
7. A higher-priority catch-all route can beat a lower-priority literal route.
8. Exact-method specificity matters only after priority and host specificity tie.
9. Path specificity follows the stated left-to-right order rather than a total count of literal segments.
10. Two routes may remain tied until `route_id`; that is valid and must resolve deterministically.
11. Exact duplicate route rows are deduplicated. Conflicting reuse of one `route_id` fails catalog validation.
12. Invalid path patterns, duplicate parameter names within one pattern, malformed host patterns, empty upstreams, and non-integer priorities fail catalog validation.
13. Parse and preprocess the immutable route snapshot once, then reuse it across all queries.
14. Do not compile new regular expressions or rebuild the full route catalog for every request.
15. Diagnostic logging goes to stderr rather than corrupting the JSONL result stream.

## Production constraints

The checked-in fixture is intentionally small. Design for approximately 2 million route definitions after deduplication; 300,000 distinct exact or suffix-wildcard host scopes; a few hot hosts with 100,000+ path rules; typical path depth 3–8 segments and maximum 30; 100,000–250,000 resolution requests per second per process during peak traffic; immutable snapshots replaced atomically outside this process; a 1.2 GB memory budget; and target p95 lookup latency under 2 ms after startup.

A production-credible solution should not scan all routes for every request, scan every route attached to a hot host, or create query-sized copies of the catalog. Think about which dimensions can be indexed once, which matching branches a request can possibly follow, and what metadata can help avoid unnecessary work.

Path patterns overlap: at one request segment, a literal branch, a named-parameter branch, and a single-segment wildcard branch can all potentially match. `**` adds a suffix match. Priority is evaluated before specificity, so simply returning the first structurally most-specific match is not generally correct.

The candidate owns the solution strategy. Exact deterministic indexing is a natural direction, but a heuristic, generated-code, AI-assisted, or hybrid design can be defended if it still satisfies the observable contract and you clearly explain the latency/correctness tradeoffs. An external model or API is not required.

## Expected deliverable

Implement `RouteResolver.resolve(query)` in `src/resolver.js` and add or change supporting structures as needed. Wire the existing CLI path so:

```bash
node routeforge.js resolve --routes fixtures/routes.csv --queries fixtures/queries.jsonl
```

emits one JSON object per query.

Add focused tests for the risks you think matter most. Be prepared to explain what reusable structures you build when loading the snapshot; how you narrow host and method candidates; how you process overlapping path-pattern alternatives without scanning a hot host's entire rule set; how captures are recovered for the final winning rule; how you preserve the exact precedence order; startup complexity, per-query complexity, worst-case behavior, and memory use; malformed catalog/request cases; and whether an AI/heuristic component belongs in the critical routing path.

## Verification / run commands

No third-party dependencies are required. Node.js 20+ is sufficient.

Baseline checks before making changes:

```bash
npm test
npm run verify
node --check routeforge.js
node --check src/catalog.js
node --check src/patterns.js
node --check src/resolver.js
```

Fixture validation:

```bash
node routeforge.js validate --routes fixtures/routes.csv --queries fixtures/queries.jsonl
```

After implementing the resolver:

```bash
node routeforge.js resolve --routes fixtures/routes.csv --queries fixtures/queries.jsonl
```

## Scope / out of scope

In scope: one immutable in-process snapshot, catalog/query validation, exact route matching, deterministic precedence, parameter capture, reusable preprocessing, focused tests, and scalability reasoning.

Out of scope: proxying actual HTTP traffic, TLS, authentication, header-based routing, query-parameter routing, live route mutation, distributed coordination, persistent databases, deployment orchestration, and a web UI.

## 60-minute AI-assisted interview instruction

You have 60 minutes. Use Claude Code, Codex, ChatGPT, or other AI tools as you would on the job, but inspect the route language, precedence rules, starter code, and fixture yourself before delegating implementation.

First make sure you can explain why a simple linear scan and a naive `most specific first` traversal both have problems under the stated contract. Then implement the smallest credible approach, verify several adversarial overlaps, and be ready to discuss how the design behaves on hot hosts and deeply overlapping patterns.
