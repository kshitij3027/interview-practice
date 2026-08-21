# RecoveryWave — Grading Rubric (100 points)

## 1. Problem decomposition and data modeling — 15 points
- 13–15: Correctly distinguishes dependency direction, affected-service discovery, incident scoping, ordering semantics, malformed data, and repeated-query requirements. Builds reusable static indexes rather than mixing everything into per-query scanning.
- 9–12: Mostly correct model with one notable omission or inefficient boundary.
- 4–8: Happy-path understanding but dependency direction, region semantics, or loop behavior is shaky.
- 0–3: Fundamental misunderstanding of what must be restarted or in what order.

## 2. Correctness of affected-service discovery — 18 points
- Correctly includes failed services and all transitively affected dependents through hard dependencies.
- Ignores soft dependencies for propagation.
- Applies region filtering consistently.
- Handles duplicate rows without duplicate output.
- Reports unknown incident services without failing the whole incident.

Excellent work is correct on chains, branching fan-out, multiple failed roots, duplicate edges, region-filtered incidents, and mixed known/unknown failures.

## 3. Recovery-wave correctness — 22 points
- Produces dependency-safe restart ordering.
- Correctly handles self-links and multi-service dependency loops without hanging or dropping services.
- Groups services that cannot be ordered relative to one another into one wave.
- Ensures all inter-group hard dependencies point from earlier to later waves.
- Produces each affected service exactly once.

A solution that merely performs a normal topological pass and fails on loops cannot receive more than 10/22 here.

## 4. Determinism and tie-breaking — 8 points
- Services inside a wave are lexicographically ordered.
- Eligible work is selected deterministically using the stated `(tier, service_id)` rule.
- Output does not depend on CSV ordering, set iteration, hash randomization, or incidental dictionary insertion order.

## 5. Complexity and production scalability — 15 points
- 13–15: Static graph is parsed/indexed once; startup and query costs are explicitly reasoned about; approach is credible for ~200k vertices/~1M edges and repeated queries under 512 MB. Avoids full transitive closure and full edge rescans per incident.
- 9–12: Reasonable indexing and asymptotics, but some avoidable repeated work or vague memory analysis.
- 4–8: Works on fixture but query path repeatedly scans most/all static data or uses expensive global recomputation.
- 0–3: All-pairs, transitive-closure materialization, quadratic graph scans, or similarly non-credible design.

## 6. Edge cases and input robustness — 8 points
Covers malformed dependency endpoints, duplicate edges, self-dependencies, disconnected services, multiple failed roots, loops, empty affected sets after region filtering, and unknown incident IDs.

## 7. Verification and tests — 7 points
- Adds focused tests for difficult semantics rather than only the fixture happy path.
- Demonstrates at least one loop case, ordering case, propagation case, and robustness case.
- Uses tests/output inspection to catch implementation mistakes.

## 8. Code quality and implementation discipline — 4 points
Clear interfaces, sensible naming, bounded helper responsibilities, no unnecessary framework work, and no debug artifacts in normal output.

## 9. Walkthrough and tradeoff defense — 3 points
Candidate can explain dependency direction, preprocessing/query tradeoffs, complexity, loop semantics, and why the chosen deterministic/heuristic/LLM balance fits this problem.

---

## Score calibration
- **90–100:** Strong production-minded solution with correct loop semantics, deterministic output, credible repeated-query design, and strong verification.
- **75–89:** Correct core with minor edge-case, determinism, or scaling gaps.
- **60–74:** Substantial working solution but important correctness/scalability limitations.
- **40–59:** Happy path or brute-force approach that ignores key scale/loop requirements. A solution that only works on acyclic fixture subsets should remain in this band.
- **0–39:** Incomplete or fundamentally incorrect.

A superficially working happy-path implementation that ignores loops, scale, or repeated-query constraints should not score above roughly **55–60**.
