# Grading Rubric — 100 points

## 1. Problem decomposition and model — 14
- 13–14: Cleanly separates hierarchy applicability, temporal activity, precedence, validation, and reusable preprocessing; identifies skew/hot-scope risk.
- 10–12: Mostly sound decomposition with minor coupling.
- 6–9: Understands the happy path but misses an important dimension.
- 0–5: Treats the task as a flat scan/filter problem without a credible model.

## 2. Algorithm / data-structure choice — 22
- 20–22: Uses a production-credible indexing/search strategy for hierarchy + active-time lookup and can justify why the maintained state is sufficient.
- 15–19: Correct approach with some avoidable query-time work or weaker skew handling.
- 8–14: Fixture-correct but scans large per-scope histories or rebuilds substantial state per query.
- 0–7: Full promotion scan or similarly non-scalable approach with no credible production path.

## 3. Correctness under the contract — 20
Covers ancestor applicability, half-open windows, strict precedence ordering, unknown products, deterministic output, duplicate replay handling, and validation interactions.

## 4. Complexity / scalability reasoning — 14
Evaluates startup cost, per-query cost, memory, category depth, hot-root histories, and whether the approach remains credible at millions of products / 1.5M promotions.

## 5. Edge cases and adversarial behavior — 12
High-value areas include exact start/end boundaries, higher-priority ancestor versus direct-product rule, direct product versus deeper category at equal priority, exact-region versus wildcard ordering, equal-start lexical tie, timestamp offsets, deep ancestry, exact duplicate promotion replay, conflicting promotion IDs, cycles, and row-order independence.

## 6. Verification / testing — 8
Focused tests should target semantic boundaries and failure modes rather than only fixture snapshots.

## 7. Code quality — 5
Clear naming, reasonable boundaries, deterministic comparisons, and minimal accidental complexity.

## 8. Explanation and tradeoff defense — 5
Candidate can explain why the approach is correct, where it spends memory/time, what breaks under skew, and whether approximate/AI-assisted alternatives belong in the critical path.

## Overall calibration
- **90–100 Excellent:** correct, production-credible, well-verified, and clearly defended.
- **75–89 Strong:** solid solution with a few scale or edge-case gaps.
- **60–74 Partial:** useful progress but at least one major semantic or scalability weakness.
- **Below 60 Failing/incomplete:** brute-force/happy-path behavior, major precedence bugs, or little verification.

A solution that simply scans all promotions per query or ignores hierarchy/time-index scalability should not score above roughly **55–60**, even if it matches the checked-in fixture.
