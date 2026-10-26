# POST-PRACTICE ONLY — AidLink Grading Rubric (100 points)

**Use only after the candidate completes the timed exercise.** The candidate-facing starter does not contain this document.

| Area | Points | Strong performance |
| --- | ---: | --- |
| Business interpretation / decomposition | 12 | Models separate depot stock, lane capacity, clinic critical/routine demand, and the hierarchy of global objectives. Validates inputs and request isolation. |
| Algorithm and data-structure choice | 20 | Uses a globally valid allocation/optimization method, explains rerouting, distinguishes priority maximization from cost minimization, and handles sparse lanes and parallel edges. |
| Functional correctness | 26 | Produces feasible shipments, exact per-clinic served amounts, global critical optimum, then routine optimum, then minimum shipping cost. Handles shortages/overrides without cross-request state leakage. |
| Complexity / production scale | 16 | Avoids one-unit-at-a-time loops and exhaustive allocation search; bounds graph size, augmentation behavior, memory, and repeated-scenario costs, with realistic benchmark discussion. |
| Robustness and adversarial cases | 12 | Handles zero stock/demand, disconnected/disabled lanes, distinct parallel lanes, cost/priority conflicts, duplicate catalog replay, tie determinism, invalid per-line requests, and integer precision. |
| Verification / tests | 8 | Independent test cases show priority dominance, rearrangement versus cheap greedy choice, cost-optimality at fixed priorities, failed scenarios, and repeatability. |
| Code quality | 4 | Clear boundaries, manageable implementation, meaningful names and no output pollution. |
| Walkthrough and tradeoff defense | 2 | Can explain why the returned plan is globally optimal, where AI-generated approaches might fail, and next reliability steps. |
| **Total** | **100** | |

## Calibration and caps

- 90–100: robust, scalable approach with convincing tests and explanation.
- 75–89: strong core with bounded edge-case or scaling gaps.
- 60–74: meaningful partial work; critical holes remain.
- Below 60: non-global optimization or incomplete solver.
- **A cheapest-first, per-clinic greedy, or brute-force happy path that ignores scale or adversarial allocation must never score above 55–60 points**, even if it matches the supplied fixture.
- A solver that violates the first or second priority has a functional correctness ceiling of 11/26; one that does not minimize cost at fixed service has at most 18/26.
- A solver that can emit infeasible shipments cannot receive more than 12/26 functional correctness points.
- Do not require one specific implementation technique. Valid exact alternative algorithms are acceptable if the candidate proves correctness and defends complexity.

## Suggested interviewer observation

Evaluate how the candidate discovers the optimization model, tests counterexamples, checks numerical types, and explains residual constraints. Distinguish evidence-backed reasoning from simply reading AI-generated code aloud.
