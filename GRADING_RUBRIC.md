# WaterLine — evaluator scoring (100 points)

**Evaluator branch only. POST-PRACTICE ONLY.** Do not reveal to the candidate before completion.

| Dimension | Points | Evidence |
|---|---:|---|
| Customer understanding and decomposition | 12 | Separates baseline service from attributable impact; defines independent hypothetical closures, outputs, and error domains; inspects data before committing to an approach. |
| Algorithm / data structure decision | 20 | Selects a credible strategy for up to two absent controls across many independent requests; clearly addresses redundant routes, parallel physical links and multiple sources. Justifies deterministic vs heuristic vs LLM/hybrid in terms of exactness. |
| Functional correctness | 20 | Exact supplied-node membership before/after closures, all-sources semantics, correct three aggregates, no double counting, stable independent results and output contract. |
| Scalability / complexity | 16 | Explains preprocessing, worst-case time, batch/query behavior, memory, skew/hot controls; does not depend on a full O(V+E) walk per production query. |
| Edge cases / robustness | 12 | Covers two-link interactions, no-op closures, duplicate IDs, parallel pipes, self-loops, multiple sources, baseline islands, malformed inputs and atomic catalog errors. |
| Verification and testing | 10 | Adds high-information focused tests, checks exact expected outputs and invariants, uses measured or reasoned scale evidence, catches AI hallucinations. |
| Code quality / execution | 5 | Clean interfaces, runnable CLI, predictable errors, readable state management, no stdout noise or unintended dependencies. |
| Walkthrough and tradeoff defense | 5 | Explains data structure/invariants, alternatives, limitations, and why the chosen approach beats brute force for the actual workload. |
| **Total** | **100** | |

## Calibration and caps

- A solution that always returns zero, regardless of green starter tests: **at most 20**.
- A correctly validated brute-force scan per request: **at most 55**; if source/baseline logic is also wrong, score lower.
- A robust single-closure optimization that mishandles two-closure interaction: **at most 70**, usually lower depending on verification.
- An approximate model/heuristic without an exact correctness guarantee for required numeric outputs: **at most 55**. An LLM used for discovery, test design, or optional validated preprocessing is not penalized.
- Missing meaningful tests **or** an inability to explain performance invalidates a top-tier (90+) score. Do not reward incidental matching on tiny fixtures as proof of scale.
- Award partial credit for correct decomposition, proof of correctness, well-tested limited cases, and an explicit bound on unimplemented aspects.
