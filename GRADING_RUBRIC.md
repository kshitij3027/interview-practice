# TraceCode — POST-PRACTICE ONLY — 100-Point Grading Rubric

This document is reserved for assessment after the interview. Credit demonstrated, repeatable correctness and defensible engineering choices, not just convincing generated code or explanations.

| Dimension | Points | Observable evidence |
| --- | ---: | --- |
| Problem decomposition and invariants | **10** | Recognizes fixed-width payload + check digit, inclusive model ranges, per-position OCR cost, exact minimum, tie order, ambiguous optimum, and catalog/query error isolation. |
| Algorithm/data-structure selection | **20** | Chooses a principled bounded optimization/search design rather than decimal enumeration; explains its state/invariants, deduplicated authorized ranges, tie selection and optimal candidate counting. |
| Exact behavior and functional correctness | **25** | Range validity (6), checksum including final digit cost (5), globally minimal penalty (5), lexical optimum (5), and ambiguity of distinct minimum-cost serials (4). |
| Complexity, scalability and operational tradeoffs | **20** | Time complexity (6), hot-model/precomputation approach (6), memory costs (4), and worst-case all-unreadable labels / distribution skew (4). |
| Boundary and adversarial correctness | **10** | Leading zeros (2), endpoints and overlap (2), disjoint model scope/no solution (2), precise cap behavior (2), strict inputs and catalog atomicity (2). |
| Tests and verification | **10** | Adds independently justified cases for optimality, overlap, ambiguity, checksum, malformed records and a scale probe; runs available commands and interprets failures. |
| Code quality and walkthrough defense | **5** | Well-separated responsibilities, reproducible output, maintainable code, and can explain how and why AI-generated changes work. |
| **TOTAL** | **100** | |

## Critical caps

- **55/100 maximum** for solutions that enumerate every authorized payload, all decimal values, or all combinations of OCR choices, even if they pass the tiny fixture. They fail the primary production-scale requirement.
- **60/100 maximum** for an efficient-looking implementation that handles only one authorized interval, loses disjoint bands, uses a greedy nonoptimal solution, or double-counts serials authorized by overlapping intervals.
- **55/100 maximum** for unverified model/heuristic guesses, regardless of subjective plausibility. Exact output guarantees cannot be assumed.
- **50/100 maximum** if the solution omits the printed check digit or selects cheapest digits independently without checking validity.
- **35/100 maximum** when no correct successful scan can be demonstrated.
- An unstable tie-break or false ambiguity materially reduces exact correctness points; passing starter tests alone is not evidence of the missing feature.

## Suggested performance bands

90–100: complete exact semantics, realistic hot-model performance strategy, adversarial tests, excellent complexity defense.
75–89: exact or nearly exact core, clear engineering limits and representative tests.
60–74: most ordinary scans work but hidden corner cases or substantial scale limitations remain.
40–59: functional partial demo, superficial testing or unacceptable enumeration.
0–39: little demonstrated customer capability.

Use a hand-checked counterexample, an all-unreadable scan and an overlapping-range test to distinguish superficially successful from correct solutions.
