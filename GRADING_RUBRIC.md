# FiberWatch — Grading Rubric (100 points)

**POST-PRACTICE ONLY. Not candidate-facing.** Evaluate the live 60-minute solution and walkthrough.

| Dimension | Points | Evidence |
| --- | ---: | --- |
| Business decomposition and invariants | 15 | Correct definitions for previously served versus newly disconnected, multi-core fallback, independent span IDs, access-site/account aggregations; separates snapshot and request validation. |
| Choice of analysis method | 22 | Reusable near-linear analysis instead of recomputing reachability; correctly represents undirected parallel spans, cycles, disconnected islands, and multiple cores; defends the correctness argument. |
| Functional correctness | 23 | Exact per-span impact triples and top lists; excludes disabled spans from top, includes zero-impact enabled spans, preserves deterministic ordering and output contracts. |
| Complexity and resource scalability | 15 | Preprocessing and O(1) or similar repeated single-span lookups; fast bounded top-k; no exhaustive per-outage traversal, no deep recursive overflow, credible discussion of 1.5 GB memory. |
| Difficult edge cases and input handling | 11 | Parallel edges, self-loops, redundant core routes, offline islands, zero-account access sites, ties, replay deduplication, invalid rows, unknown spans, booleans, and malformed queries. |
| Verification and debugging | 8 | Focused tests beyond starter baseline, shuffled rows, adversarial topologies, ideally randomized comparison to a small reference; runs checks. |
| Code quality | 4 | Understandable modular design, no cross-request mutation, stable JSON output, diagnostics on stderr, minimal dependencies. |
| Walkthrough and tradeoffs | 2 | Explains why correct, where scale bottlenecks arise, and when AI would or would not be used for exact outage counts. |
| **Total** | **100** | |

## Score ceilings

- A per-query or per-cable full-graph reachability scan, however clean, **cannot score above 55/100**. Happy-path brute force is insufficient at the specified scale.
- Failing to distinguish independent parallel physical spans or assuming one core caps at **60/100**.
- Returning counts for previously unserved locations caps at **65/100**.
- Implementing only `span` or only `top` caps at **68/100**. Returning only starter placeholders caps at **15/100**.
- No meaningful verification beyond green starter tests caps at **78/100**.

Score based on demonstrated correctness and evidence, not the amount of AI-generated code.
