# ClaimSignal — Evaluator Grading Rubric (100 points)

**POST-PRACTICE ONLY. Do not share with the candidate during the exercise.**

| Dimension | Points | Expected evidence |
| --- | ---: | --- |
| Problem decomposition and contract interpretation | 12 | Precisely distinguishes catalog validation, independent request handling, occurrence eligibility, non-overlap, the cardinality limit, and whole-set optimization. Calls out the difference between local and global ranking. |
| Matching strategy / algorithm and data structures | 20 | Appropriate reusable multi-phrase search representation; correct occurrence enumeration with boundaries and channels; coherent globally optimal cardinality-constrained selection approach; no unjustified exponential enumeration. |
| Functional correctness | 20 | Correct eligible findings, inclusive/exclusive span arithmetic, scores, `max_findings`, globally optimal complete-set selection, original text extraction, stable ordered JSONL output, and no cross-case state. |
| Complexity, scale and memory | 17 | Explicit complexity for catalog build, note scan, hits, sorting, selection and ties; useful preprocessing shared across cases; sensible handling of dense matching and 1 GB constraint; realistically discusses p95 and worst-case workloads. |
| Edge cases and invariants | 12 | Exact replays vs conflicts, duplicate phrase across rules, different channels, inactive rules, punctuation/whole-word boundaries, repeated/overlapping hits, adjacent spans, deterministic all-level ties, empty notes and invalid independent requests. |
| Verification and debugging discipline | 8 | Existing tests green, additional targeted examples for non-greedy and tie cases, randomized/brute reference comparisons for small inputs where feasible, malformed-input continuation, and a clear reproducible run. |
| Code quality | 5 | Coherent separation of indexing/matching/selection/API, readable naming, predictable errors, minimal dependencies and localized changes preserving baseline behaviors. |
| Explanation and tradeoff defense | 6 | Can explain why greedy/exhaustive/local selection fails, defend chosen asymptotics, state limitations and AI-generated-code risks, and prioritize improvements under time. |
| **Total** | **100** | |

## Score ceilings

- A correct-looking happy-path brute-force phrase scan or subset enumeration **may not exceed 55/100** even if its fixture output is correct. This requires evidence of a credible scale-aware redesign to exceed the ceiling.
- A greedy occurrence selector that loses the required global optimum **may not exceed 50/100**, regardless of clean presentation.
- A solution that only validates inputs and does not attempt case resolution **may not exceed 25/100**.
- A small-input-correct solution with no credible catalog indexing or bounded-cardinality complexity analysis **may not exceed 60/100**.
- A naive one-shot generated implementation with no tests beyond baseline normally scores below 65, even when it passes visible examples.
- Scores are further constrained by major observable contract violations, not merely by how many lines were implemented.

## Scoring bands

90–100: exact end-to-end, scalable design, robust verification, clear tradeoff defense. 75–89: strong near-complete solution with small omissions or measured scaling caveats. 60–74: reasonable strategy, partial correctness or edge gaps. 40–59: happy-path, greedy, non-scaling, or major correctness omissions. Below 40: cannot reliably process independent requests or apply basic semantics.
