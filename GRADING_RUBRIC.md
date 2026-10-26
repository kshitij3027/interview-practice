# OpsDispatch evaluator grading rubric — 100 points

**POST-PRACTICE ONLY — do not expose to the candidate before the 60-minute exercise.**

Evaluate functional behavior and defended design, not the language or whether the candidate used deterministic/LLM/hybrid tools. A claimed optimal plan without a compelling correctness argument earns little credit. **A greedy nearest-first happy-path implementation ignoring global optimality or capacity coupling must not exceed 55/100**, even if it passes visible fixtures.

| Category | Points | What earns full credit |
|---|---:|---|
| Feasibility and output contract | 15 | Only listed eligible routes, at most one responder per incident, both responder and pod limits, no fabricated coverage, correct shape and totals, stable sorted output; coherent zero/unassignable handling. |
| Severity-optimal coverage | 25 | Proves and implements lexicographically maximal sev0, then sev1, then sev2 cover counts, allowing reassignment of earlier tentative selections where needed; no purely local urgency/nearest-first logic. |
| Global ETA optimality | 15 | Finds minimum total ETA among all plans with the same best severity counts, not merely locally cheapest edges; accounts for shared responders/pods and alternate routes. |
| Scale-aware architecture | 13 | Gives justified time/space complexity and credible handling of 15k/4k/350/250k sizes under constraints; identifies hot pods and when optimization becomes expensive. |
| Correctness edge cases | 12 | Tests scarce options, independent personal/pod capacities, zero caps, identical replays, ties, isolated incidents, equal/zero ETA, and row-order invariance. |
| Verification and diagnostics | 10 | Adds meaningful tests independent of fixture ordering, checks exact objective against small exhaustive oracle or mathematically sound cases, exercises CLI, and reports limitations faithfully. |
| Walkthrough and tradeoffs | 10 | Clearly explains objective, complexity, correctness invariant, how AI assistance was verified, and why deterministic/heuristic/LLM approach is or is not suited to an exact assignment contract. |
| **Total** | **100** | |

### Rating guidance

- **90–100 Excellent:** Correct global optimization and explainable complexity, reproducible results, strong adversarial tests and reliable CLI.
- **75–89 Acceptable:** Core objective/capacities correct, ETA optimality mostly sound, gaps confined to secondary validation, scale or tests.
- **55–74 Partial:** Global reasoning plausible but some ordering/ETA/capacity correctness gaps, or a correct slower reference implementation with credible scale strategy.
- **0–54 Failing:** Local greedy or one-shot output, breaks critical coverage or pod ceilings, guesses optimization without verification, or does not implement an operational planner.

### Hidden-evaluator-style checks

1. One sev0 has a unique responder; a second sev0 has that responder plus an alternate. Local minimum ETA must yield to completing both.
2. Two responders each have capacity >1 but share a pod limit of one: never dispatch two from that pod.
3. Tie in coverage counts with alternative routing paths that have different **total** ETAs; only the globally smallest ETA wins.
4. A sev0 has no eligible route; sev1/sev2 assignments must still be optimized, but never count the unrouteable sev0.
5. No responders or all zero caps: valid empty plan.
6. Identical route replays count once; conflicting pair replays fail at load time.
7. Same snapshot rows permuted dozens of ways must yield the same assignments, not just the same totals.
8. Repeated incident IDs with same data harmless; conflicting severity reuse invalid.
9. Equal-route ETAs and multiple equally optimal global plans: any deterministic selection allowed.
10. Large sparse and skewed synthetic inputs; no exponential subset enumeration or O(incidents × responders) cartesian expansion.
