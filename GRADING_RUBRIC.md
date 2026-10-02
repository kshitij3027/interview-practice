# Grading Rubric — POST-PRACTICE ONLY

Total: **100 points**

## 1. Problem decomposition — 15
Exact eligibility, radius, ranking, rounding, validation, deterministic output, and separation of snapshot versus query errors.

## 2. Search and data-structure choice — 20
Reusable exact search state; safe pruning; avoids a full snapshot scan per query; accounts for small result limits.

## 3. Functional correctness — 20
Correct status, slot, size, capability, radius, exact-distance, ordering, limit, and output behavior.

## 4. Complexity, scalability, and memory — 15
Defensible preprocessing, memory, query, and worst-case costs for the stated production scale.

## 5. Edge cases — 10
Date line, poles, exact radius, identical coordinates, ordinal sizes, exact capability tokens, inactive/zero-slot decoys, unrounded-distance ranking, and deterministic ties.

## 6. Verification and tests — 10
Focused tests for risky semantics and useful cross-checking against a simple exact reference on small data.

## 7. Code quality — 5
Clear, cohesive, deterministic code without needless dependencies.

## 8. Explanation and tradeoff defense — 5
Explains preprocessing, exactness, performance, worst cases, and alternatives.

A happy-path implementation that scans every locker for every query and ignores the stated scale should generally not score above **55–60**, even if the fixture output is correct. A 90+ solution needs exact semantics, defensible pruning, bounded top-result work, strong geographic tests, and a credible memory/latency story.
