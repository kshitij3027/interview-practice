# Grading Rubric — 100 points

## 1. Problem decomposition and model — 16 points
- 14–16: Cleanly separates catalog validation/normalization, reusable indexing, request validation, pattern matching, precedence, and capture recovery. Explicitly identifies why priority-first winner selection complicates a purely specificity-first lookup.
- 10–13: Mostly sound decomposition with minor coupling or missed invariants.
- 5–9: Understands matching but treats the system largely as an unstructured scan.
- 0–4: Misreads the routing contract or precedence.

## 2. Algorithm / data-structure choice — 22 points
- 19–22: Uses production-credible reusable indexes for host/method/path dimensions, avoids per-query catalog scans, handles overlapping literal/parameter/wildcard alternatives deliberately, and can justify pruning or candidate enumeration.
- 14–18: Good indexing but one hot-path dimension still risks large scans.
- 8–13: Some indexing, but fixture-driven or weak under hot hosts.
- 0–7: Linear scan / regex over all routes per request or equivalent brute force.

## 3. Correctness under the routing contract — 20 points
Covers host suffix semantics, method matching, `*`/`**`, zero-length `**`, captures, exact winner precedence, priority before specificity, deterministic route-id tie break, and invalid-request isolation.

## 4. Complexity and scalability reasoning — 12 points
Candidate should discuss startup cost, memory, common-case lookup, pathological overlap, hot-host behavior, and why the design can approach the stated latency target. Merely claiming O(path length) without accounting for overlapping branches is not full credit.

## 5. Edge cases and adversarial behavior — 12 points
High-value checks include case-insensitive hosts, terminal-dot normalization, bare-host non-match for suffix wildcards, root path, `**` matching zero/many segments, parameter versus `*` specificity, high-priority broad route, duplicate/conflicting IDs, repeated params, and input-order independence.

## 6. Verification and testing — 8 points
Focused tests should target precedence interactions and pathological matching rather than only fixture happy paths.

## 7. Code quality — 5 points
Readable boundaries, deterministic behavior, disciplined error handling, and no unnecessary query-time allocation/copying.

## 8. Explanation / tradeoff defense — 5 points
Can explain the chosen structures, correctness argument, worst case, alternatives, and why AI/heuristics do or do not belong in the critical lookup path.

## Calibration
- **90–100:** Excellent: exact, well-indexed, robust under adversarial overlap, with credible complexity reasoning.
- **75–89:** Strong: correct on most semantics and reasonably scalable, with some pathological/performance gaps.
- **60–74:** Partial: useful implementation, but important scale or edge-case limitations remain.
- **Below 60:** Brute-force, precedence-broken, or substantially incomplete.

A happy-path implementation that scans every route attached to a host, relies on route-file order, or ignores overlap/scale should not exceed **55–60 points**, even if it matches the checked-in fixture.
