# CryoRelay — POST-PRACTICE ONLY Grading Rubric (100 points)

**Evaluator branch only. Never place this file or excerpts on a candidate branch.** Judge observable guarantees, sound reasoning, and responsible use of AI, not allegiance to a particular library or model.

| Criterion | Points | Strong evidence |
| --- | ---: | --- |
| Problem decomposition and data discovery | 12 | Inspects fixture and parser; distinguishes pickup vs transfer, feasible vs optimal, snapshot vs query failure; states invariants. |
| Approach and algorithm/data representation | 20 | Frames timed service reachability and objective ordering; justifies indexed, bounded exploration, state distinctions and path reconstruction; handles multiple labels when appropriate. |
| Functional correctness | 22 | Finds exact earliest feasible arrival, then fewest services and lex smallest service-ID sequence; correct output formats; all transfer constraints, capacity and zero-hop behavior. |
| Performance and memory reasoning | 14 | Supports preprocessing/repeated queries; provides explicit asymptotic costs, hot-hub skew consideration, bounded-leg analysis, and realistic memory tradeoffs. |
| Edge cases and adversarial reasoning | 12 | Tests strict boundaries, warm-hub maximum dwell, late arrivals that dominate earlier ones for feasibility, equal-time routes, loops, zero slots, cold capability and duplicates. |
| Verification strategy | 9 | Adds targeted independent tests, distinguishes smoke tests from correctness tests, checks full CLI, and probes invalid inputs and scaling. |
| Code clarity and operational reliability | 5 | Legible separation of concerns, no unexpected stdout, safe immutable query semantics and maintained validation behavior. |
| Walkthrough and AI tradeoff defense | 6 | Explains why chosen design works, discusses heuristic/LLM/deterministic alternatives and failure modes, owns AI-generated code. |
| **Total** | **100** | |

Scoring guidance: an efficient, exact non-LLM solution can earn full credit. A documented LLM/hybrid method earns full credit **only if exact validation, reproducibility and performance** meet the same contract. A shallow greedy or repeated full-catalog scan that ignores production-scale goals **must not score above 55**, even if it passes happy-path examples. Ignoring cold-dwell or transfer feasibility is a hard cap of **45**. Returning valid but nonoptimal arrival paths is capped at **60**. No attempt beyond the starter placeholder scores at most **10**. Correct but slow small-fixture solutions may earn partial credit for decomposition and verified logic. Don't award points for unspecified integrations or arbitrary aesthetic choices.
