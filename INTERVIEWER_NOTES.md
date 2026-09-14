# POST-PRACTICE ONLY — Interviewer Notes

Do not read this file before completing the exercise.

## Intended underlying problem structure

This is a compiled multi-dimensional pattern-matching problem over a static rule snapshot. Strong solutions usually normalize/deduplicate once, narrow host scopes using exact/global plus matching hostname suffixes, split exact method from `ANY`, and compile path patterns into reusable segment-level structures rather than scanning route rows.

Path lookup is not a single deterministic descent: for one request segment, literal, parameter, and `*` transitions may all remain viable, while terminal `**` can match the remaining suffix. The resolver therefore needs either bounded multi-state traversal, another equivalent compiled representation, or a justified alternative. Because route priority outranks specificity, "take the most specific branch first and stop" is wrong unless the structure carries enough subtree winner metadata to prove pruning safe.

## Strong solution approaches

One strong exact design:

1. Normalize/dedupe catalog definitions and pre-parse path patterns.
2. Index host scopes in maps keyed by exact host and literal wildcard suffix; a request can enumerate its hostname suffixes in O(number of labels) plus global `*`.
3. Within host scope, separate exact method buckets and `ANY` buckets.
4. Compile each bucket's path rules into a segment matcher with literal edges plus generic parameter and single-wildcard transitions and terminal multi-wildcard candidates.
5. Traverse only matching states for the request path. Store route ranking metadata at terminals; optionally store subtree maximum-priority / upper-bound metadata to prune safely after a strong incumbent is found.
6. Compare every surviving candidate with the exact precedence tuple. Recover named captures from the winning route's parameter positions rather than duplicating a structural parameter edge solely because parameter names differ.

A radix-like representation, automaton/NFA-style state traversal, or shape-index scheme is also defensible if exact semantics and worst-case behavior are explained.

## Complexity discussion

Catalog build is roughly linear in total pattern segments plus indexing overhead. Host candidate discovery can be O(host-label count). Method alternatives are at most two per host scope. Path traversal is proportional to the number of compiled matching states visited, not simply path length in the pathological case because generic transitions overlap. Strong candidates acknowledge this and discuss mitigation: pruning with max-priority/ranking upper bounds, collapsing equivalent generic structure, caching hot exact requests, or operational limits on pathological rule sets.

A per-route regex scan is O(routes in scope × path work) and fails badly for 100k-rule hot hosts.

## Why naive approaches fail

- Global linear scan: obvious throughput failure.
- Host-only indexing then scanning 100k path rules: still fails hot-host constraint.
- First-match / file-order semantics: violates deterministic precedence.
- Most-specific-first early return: a broader higher-priority route can win.
- Counting literals globally instead of left-to-right specificity: violates the contract.
- Treating `*.acme.com` as matching `acme.com`: wrong host semantics.
- Converting each pattern to a regex on every request: avoidable CPU/allocation and still scan-heavy.
- One generic parameter child per parameter name: can explode memory for identical routing shapes.

## Subtle traps / hidden checks

- Exact duplicate route rows should collapse; conflicting same-ID definitions fail startup validation.
- Host comparison is lowercase after removing one terminal dot from the request.
- Suffix wildcard requires at least one prefix label.
- `/files/**` matches `/files` with zero remaining segments.
- `/a/{x}/c` outranks `/a/*/c` when earlier precedence dimensions tie.
- `/a/*/literal` does not outrank `/a/{x}/*` merely because it has a literal later; the first differing path segment decides.
- A priority-100 `/**` route beats a priority-99 exact literal route.
- Exact method beats `ANY` only after priority and host ranking tie.
- Parameter names affect captures, not structural specificity.
- Invalid query should produce one invalid result and not abort later queries.
- Root `/` is zero segments and distinct from `/**` only by precedence if both match.
- Route output must not depend on insertion/hash order.

## Alternative defensible designs

- Compile a deterministic dispatch program or generated decision tree per hot host/method snapshot.
- Use per-length path-shape indexing for routes without `**`, with a separate catch-all index; credible if candidate bounds shape enumeration.
- Use a carefully optimized regex-set engine if compiled once and paired with external precedence metadata, but the candidate must defend memory and candidate extraction costs.
- Cache exact `(host,method,path)` resolutions for hot traffic if snapshot immutability makes invalidation trivial; cache is an optimization, not a substitute for scalable cold lookup.

An LLM in the critical path is generally a poor fit because the contract is exact and latency is sub-millisecond-to-low-millisecond. AI can still be useful for implementation, catalog linting, or generating tests.

## Likely AI-agent failure modes

- One-shot agent writes a `routes.filter(...).sort(...)` solution that passes fixtures but ignores scale.
- Agent flattens specificity into literal counts rather than the stated left-to-right ordering.
- Regex conversion mishandles `**` zero-segment matching.
- Host wildcard regex accidentally matches the bare suffix.
- Captures are taken from a generic structural branch but mapped to the wrong parameter names for the chosen route.
- Agent optimizes traversal but stops before considering a higher-priority broad candidate.

## What should be discovered from the data

The fixture intentionally includes duplicate replay, exact-vs-parameter path overlap, parameter-vs-single-wildcard overlap, exact-host-vs-suffix overlap, exact-method-vs-ANY overlap, and a deliberately high-priority broad emergency order route. The candidate should notice that structural specificity alone does not determine the winner.

## Recommended prioritization for 60 minutes

1. Write down normalization and precedence contract.
2. Get catalog/query validation and exact matching semantics correct.
3. Build a reusable host/method/path index and focused unit tests.
4. Implement deterministic winner comparison plus capture extraction.
5. Run fixture queries and adversarial tests.
6. Use remaining time to improve pruning/caching and articulate production scaling.

## Walkthrough inspection points

Ask the candidate to explain:
- what work occurs once at snapshot load versus every query;
- how many host/method/path branches one request can explore;
- the exact comparison key and why it preserves the stated rule order;
- how `**` zero-segment matches work;
- how parameter captures remain correct if structural parameter edges are shared;
- worst-case overlapping-pattern behavior;
- a concrete optimization for a 100k-rule hot host;
- why their tests would catch a broad high-priority route beating a specific lower-priority route.
