# BundlePort — Evaluator Rubric (100 points)

**POST-PRACTICE ONLY.** Use only after the 60-minute candidate exercise.

| Area | Points | What earns credit |
|---|---:|---|
| Customer problem decomposition and semantic model | 12 | Distinguishes release identity, mandatory closure, one-version-per-name, device compatibility, symmetric conflicts, budget, query independence, and exact optimization objective. |
| Algorithmic strategy and state representation | 22 | Credible exact search/constraint propagation or a carefully justified optimizer, reversible state, exploring alternatives when cheapest local version fails, pruning without eliminating optimal plans, handling cycles consistently. |
| Functional correctness and global optimality | 23 | Correctly finds a feasible complete bundle when one exists, says unsatisfiable otherwise, honors all transitive requirements, conflicting constraints, two-way incompatibilities, and all objective/tie levels. |
| Scale, time and memory analysis | 16 | Indexed release and requirement lookup, shared catalog preprocessing, limited query-local state, meaningful complexity with exponential worst case, effectiveness/limits of pruning, evidence of viability at ordinary scale. |
| Traps and edge cases | 12 | Duplicate/conflicting roots, inactive and platform exclusions, shared dependencies counted once, cyclic requirements, boundary and contradictory ranges, exact budget equality, duplicate rows and malformed requests. |
| Verification and tests | 9 | Focused tests for a non-greedy counterexample, a feasible cycle, impossible cycle, competing tie, budget equality, malformed query continuing, and regression-safe baseline. |
| Code quality and explanation | 6 | Clear modular code, no hidden mutation between independent requests, deterministic output, readable diagnostics, explains failures and AI-generated code limitations. |
| **Total** | **100** | |

Scoring guidelines:

- A solution that merely takes the cheapest release per package and patches dependencies may receive **at most 55/100** even when the provided simple fixture passes; if it does not handle conflicts and cycles, score lower.
- A correct brute-force enumeration that ignores the published production constraints is capped at **60/100**. Explicitly acknowledge infeasible worst cases; enumerating the Cartesian product without branch pruning or indexing is not production-credible.
- A solution that intentionally returns an approximate result for arbitrary valid requests cannot receive full correctness points. An explainable heuristic can still earn decomposition, engineering, tests, and some scale credit.
- Credit partial implementations for robust parsing, sound validity checks, a coherent search state, and accurate complexity explanations. Do not conflate the green starter baseline with successful feature completion.
- The candidate should explain how AI was used and demonstrate independent checking of any generated solver logic.
