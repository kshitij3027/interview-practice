# BatchPath — Grading Rubric (POST-PRACTICE ONLY)

**100 points total.** Grade observed behavior and design defense, not only the compact fixtures.

| Dimension | Points | Expectations |
| --- | ---: | --- |
| Problem decomposition and specification | 12 | Explains concurrent prerequisite semantics, release times, exact finish times, cycle reachability and deterministic tie rules; identifies global vs per-query errors. |
| Catalog revision modeling and integrity | 13 | Highest-revision upserts/retractions, harmless identical replays, conflicting same-revision copies, strict superseded-record validation, tenant consistency, duplicate endpoints. |
| Algorithm/data-structure choice and scale | 20 | Efficient reusable per-dataset analysis for 200k datasets and 600k link rows; avoids recursion limits, exponential enumeration and per-query catalog traversal; defends time and space bounds. |
| Exact readiness and deadline calculations | 18 | Start constrained by local earliest and all active prerequisite finish times plus lag; processing duration added once; independent parallel branches; equality with deadline; exact integers. |
| Cycle detection and blocking propagation | 12 | Distinguishes upstream/reachable cycles, self-cycles and downstream dependents from disconnected healthy datasets. |
| Deterministic controlling chain | 9 | Exact predecessor tie-breaking, including ties against own earliest start, root-to-target order, no repeated nodes. |
| Request/CLI robustness | 7 | Typed JSON numbers and IDs, correct unknown-dataset errors, physical-line isolation, atomic catalog failure, deterministic output without stdout diagnostics. |
| Tests and verification | 5 | Covers revisions, branching, ties, reachable versus isolated cycles, malformed input and a scale/depth case; executes starter checks. |
| Maintainability and explanation | 4 | Clear implementation, ability to explain correctness, complexity, alternatives and limitations. |
| **Total** | **100** | |

**Caps:** A happy-path or brute-force implementation that recalculates the graph for every query and cannot meet production constraints scores at most **58/100**, regardless of its small-fixture accuracy. Ignoring reachable cycles or revision precedence caps a solution at 55. An otherwise partial or non-functional implementation cannot exceed 45. Apply caps after category scoring, and award partial points for demonstrated correctness.

Suggested bands: 85–100 excellent, 70–84 strong with gaps, 55–69 partially complete, below 55 insufficient.
