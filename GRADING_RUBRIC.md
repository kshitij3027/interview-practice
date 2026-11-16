# SourceMark — 100-Point Grading Rubric

**POST-PRACTICE ONLY — EVALUATOR MATERIAL. Do not show this file to the candidate during the timed exercise.**

Grade actual behavior, reasoning and verified results, not confident claims from a coding assistant.

| Dimension | Points | Evidence |
| --- | ---: | --- |
| Customer framing and decomposition | 14 | Understands source-set semantics, positives and negatives, validation vs infeasibility, optimization priority, and actual fixtures. |
| Algorithm/data-structure choice and optimality | 22 | Identifies bounded combinatorial coverage, sound preprocessing/search, lex tie and distinct optimum ambiguity; justifies why smaller solutions cannot exist. |
| Exact functional/contract correctness | 19 | Globally minimum source count, correct sorted winner, ambiguity only at minimum, no-match, empty set, site and JSONL output. |
| Complexity and production scalability | 15 | Addresses 2M edges, 200K lots, skew, repeated queries, memory, indexing, worst-case combinatorics, and realistic benchmarks. |
| Edge cases and failure semantics | 12 | Empty positive mix, negative eliminations, duplicates, identical participation profiles, cap zero, contradictions, invalid JSON types, unknown/cross-site references. |
| Verification/testing | 9 | Writes focused hard tests, preferably cross-checks small randomized cases against independent exhaustive oracle, runs all starter commands and inspects real outputs. |
| Code quality | 4 | Maintainable structure, clear failure paths, preserves CLI and robust input validation. |
| Walkthrough and tradeoffs | 5 | Explains AI-generated code, defends tradeoffs, complexity and known limits. |
| **Total** | **100** | |

**Scoring caps:** A brute-force design enumerating every lot pair/triple at production scale cannot score higher than **55/100**, even if it passes every tiny fixture. A happy-path heuristic that ignores negative mixes or minimum-size optimality is generally below 50. A clearly bounded, correctly tested partial exact method may outrank an unverified supposedly complete one. Keeping the starter placeholder unchanged scores at most 15. Neither AI nor deterministic approaches are mandated.
