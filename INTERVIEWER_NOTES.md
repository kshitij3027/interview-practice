# BundlePort — Interviewer Notes
POST-PRACTICE ONLY

## Intended underlying problem
Select one version for every required package, satisfying all transitive version ranges, platform restrictions and explicit exclusions, while minimizing the sum of distinct downloads under a request budget. This is a weighted constraint-optimization problem with combinatorial worst-case search. Cyclic requirements are legal when the selected releases agree; no installation ordering is requested.

## Strong approaches
Pre-index the immutable catalog by package name and version, parent release requirements, and both endpoints of exclusions. Per request, maintain chosen versions and the conjunction of required ranges for each package. When a release is selected, add its requirements, propagate constraints to a fixed point, and reject inconsistent domains. A consistent cyclic dependency must stabilize. Explore alternative versions when a choice fails. Track total cost only for distinct selected releases. A credible exact implementation may prioritize the narrowest available domain, preserve undoable local state, compare fully feasible candidate bundles under every objective, and prune only with valid cost bounds.

Catalog indexing is approximately linear in release, requirement, and exclusion counts, plus version sorting. Query search is exponential in the number of interacting choices in the worst case; propagation, lower bounds and decomposition can dramatically reduce ordinary workload. A latency guarantee over all adversarial inputs is not realistic. A heuristic may be defended if it identifies which exact guarantees it sacrifices.

## Naive solutions that fail
- Picking individually cheapest or latest versions cannot optimize complete bundle cost and can introduce later incompatibilities.
- Marking a package visited on first encounter loses constraints introduced by other parents.
- Rejecting any dependency cycle loses valid mutually compatible release sets.
- Counting a shared dependency's bytes per incoming edge overstates cost.
- Comparing version strings misorders multi-digit components.
- Treating exclusions as directional misses the reverse selection order.
- A budget check before the mandatory closure is complete can accept incomplete bundles.
- A first-feasible return ignores cheaper complete solutions and deterministic ties.

## Subtle cases and representative data
The agent release catalog contains an inactive high-numbered release. The linux agent variants imply different codec and transport requirements. Analytics version 2 conflicts with crypto version 2; the reversed conflict row is the same relationship. A transport and parser may share codec version 2. Probe and compat form satisfiable cycles in compatible pairs. Multiple root ranges may narrow a valid selection or make it impossible. Requirements and release rows have duplicate delivery replays. A malformed JSON line and boolean budget precede a valid request; processing must continue. A budget equal to the computed total is permitted.

## Evaluator-only checks
Test a case where a more expensive direct root choice produces a cheaper global bundle. Test two independent parents requiring one shared package, conflicting transitive ranges, and a cycle that is feasible versus a cycle that is inconsistent. Test explicit conflict symmetry, platform exclusivity, inactive releases, range upper-bound exclusivity, equality at the cost cap, numeric version comparisons, and all ranking tie-break levels. Permute catalog rows and repeat request IDs. Compare a result against a small exhaustive oracle for randomly generated tiny catalogs. Test malformed requests followed by valid requests and conflicting release replays during catalog validation. Probe deep narrow dependency paths and branching-heavy cases separately.

## Alternative defensible designs
Explicit constraints can be delegated to a suitable optimization engine if an external dependency is allowed in a hypothetical production system. An approximate best-first search may be useful when hard deadlines matter, but its output must be labeled approximate and cannot claim guaranteed minimum cost. Specialized fast paths for simple acyclic catalogs and independent components are valid if they preserve the global ranking.

## Likely AI-generated implementation mistakes
Agent-written recursive code commonly omits backtracking rollback, caches a state by package name without its active constraints, prunes using an inadmissible sum that double-counts shared packages, raises errors for legal cycles, uses string comparison for versions, or tests only the fixture's simplest request. Check if generated code has independently verified cost accounting and closure semantics.

## Suggested 60-minute review
First 8 minutes: formulate invariants and inspect data. Minutes 8–20: build lookup indexes and query state. Minutes 20–40: implement consistent selection, propagation and alternative choices. Minutes 40–52: verify conflicts, cycles, budget boundaries, and a greedy counterexample. Minutes 52–60: test and defend worst-case behavior. In the walkthrough, ask the candidate to trace a second parent tightening a range, a conflict discovered in reverse order, how a cycle terminates, what state is restored after backtracking, and why an optimization bound is sound.
