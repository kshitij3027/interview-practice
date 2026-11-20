# FreshClaim — evaluator grading rubric (100 points)

**POST-PRACTICE ONLY. Never copy into the candidate branch.** Score demonstrated working behavior and explained design, not use of one prescribed technology. Give full credit to exact deterministic, heuristic, LLM/hybrid or other strategies only when their measurable behavior meets the contract. A merely plausible answer without a reproducible guarantee does not earn the exactness points.

| Dimension | Points | Full-credit evidence |
| --- | ---: | --- |
| Customer decomposition and invariants | 12 | Distinguishes independently assessed baskets, batch eligibility intervals, consumable lot units, indivisible complete orders, and strict objective hierarchy; inspects data and clarifies assumptions before coding. |
| Algorithm and data representation | 18 | Identifies optimization and feasibility as distinct subproblems; chooses a correct scalable feasibility method and order-subset exploration/pruning or equivalent; justifies data structures, ties, and indexing. |
| Objective correctness | 22 | Exact maximum accepted count, then maximum units, then lexicographically smallest sorted accepted ID set. Valid full allocation exists; cannot double-spend stock. Handles both feasible/infeasible requests, empty sets, shared times, and non-trivial combinations. |
| Complexity and scale | 14 | Articulates batch validation/build cost, per-basket work and worst cases, pruning/indexing for skewed SKU partitions, memory bounds, and likely p95 limits. Does not claim an unsupported all-scale speed guarantee. |
| Edge and adversarial conditions | 12 | Checks ready-inclusive / expiry-exclusive times, multiple lots, expiring inventory, later arrivals, same-time competition, high stock skew, duplicate CSV retries, malformed values/IDs, catalog atomicity and request isolation. |
| Verification and testing | 10 | Writes focused tests beyond starter; uses small brute-force or independent oracle to compare results, tests counterexamples to obvious greedy order choice, runs provided commands, and explains what is not tested. |
| Implementation quality | 5 | Structured Python, isolated validation and engine, deterministic output, no hidden state leakage, readable error handling and no extra runtime deps. |
| Explanation, judgment and AI use | 7 | Walks through concrete allocation, proof sketch for chosen feasibility evaluator, priority criteria, complexity and alternatives; explains how AI code was checked and which tradeoffs remain. |
| **Total** | **100** | |

## Calibration and ceilings

- **0–25**: No functioning assessor or only restates requirements. Running the harness alone is not implementation progress.
- **26–45**: Correct on a few straightforward orders, but either chooses earliest/largest orders greedily without a global guarantee, or ignores lot time windows / capacity conservation.
- **46–55**: Has a reasonable partial solver and CLI, but fails meaningful objective, allocation, or scalability checks.
- **56–70**: Correct small cases with a clear optimization approach, but misses some adversarial, validation or scaling dimension.
- **71–85**: Reliable exact solver for representative cases, sound feasibility and tie strategy; testing or very hot-key performance still has gaps.
- **86–100**: Demonstrates complete contract, proof or robust oracle verification, explicit worst-case limitations, and a defensible scaling design.

**Hard ceiling: 55 points** if the candidate orders individual promises greedily, ignores alternative feasible subsets, or relies on total summed units without respecting pickup-time eligibility. **Hard ceiling: 60 points** for a brute-force lot-to-order allocation enumeration lacking both complexity analysis and a plausible plan for hot partitions. **Hard ceiling: 60 points** if output is heuristic or LLM-generated without verifying exact optimality and deterministic ties. A clean implementation of just the starter contract should not exceed 25.

No separate points are awarded for external integrations, framework choice, or using an LLM. Give credit for justified tradeoffs and concrete experimental evidence regardless of implementation technology.
