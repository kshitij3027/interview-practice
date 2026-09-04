# Grading Rubric — 100 points

The exercise is graded as a problem-solving interview, not just a fixture-passing coding task. A happy-path implementation that greedily places shipments or brute-forces combinations without a credible scale argument should not score above roughly **55–60 points**.

## 1. Problem decomposition and modeling — 15 points

- **13–15 Excellent:** Correctly separates fixed versus impacted bookings, identifies lane-slot capacity as the scarce resource, represents shipment feasibility cleanly, and preserves the three plan objectives in their required order.
- **10–12 Acceptable:** Sound model with one minor ambiguity or inefficient boundary.
- **5–9 Partial:** Gets local feasibility mostly right but misses global competition or mixes parsing/planning concerns heavily.
- **0–4 Failing:** Treats each shipment independently or misunderstands what may move.

## 2. Algorithm / data-structure choice — 20 points

- **18–20 Excellent:** Chooses and implements an approach that can optimize globally over competing shipment-to-slot choices, with a defensible method for the lexicographic objectives and deterministic ties.
- **14–17 Acceptable:** Correct exact approach with some avoidable overhead, or a well-justified approximation with explicit limitations.
- **7–13 Partial:** Greedy or search approach works on easy cases but has known counterexamples or explosive behavior.
- **0–6 Failing:** Brute-force combinations, first-fit placement, or an approach that cannot satisfy the stated objectives.

## 3. Correctness under constraints — 22 points

Assess exact behavior for impacted detection, fixed occupancy, site/capability/window eligibility, one-shipment/one-slot capacity, outage boundaries, the priority → count → displacement objective order, independent requests, summaries, and deterministic output.

- **20–22 Excellent:** Correct across nearly all hidden checks.
- **15–19 Acceptable:** Core optimum is correct with a small number of boundary defects.
- **8–14 Partial:** Substantial working logic but one major correctness dimension is wrong.
- **0–7 Failing:** Produces illegal assignments or systematically suboptimal plans.

## 4. Complexity and production scalability — 15 points

- **13–15 Excellent:** Preprocesses static baseline/indexes once; scopes work to affected site/lane/time ranges; generates only plausible candidate resources; clearly explains complexity in terms of impacted shipments and feasible assignment edges rather than total daily bookings.
- **9–12 Acceptable:** Reasonable per-outage scaling with one potentially expensive step acknowledged.
- **4–8 Partial:** Repeatedly scans all bookings/lanes or materializes much more state than necessary.
- **0–3 Failing:** Exponential search presented as production-ready or no scale reasoning.

## 5. Edge cases and adversarial behavior — 12 points

High-value evaluator themes include:

- exact `cold` versus `cold-chain` capability membership;
- earliest/latest inclusive boundaries and lane-close exclusivity;
- freeing all impacted original slots before replanning;
- not moving unaffected bookings;
- a high-priority narrow-window shipment competing with lower-priority flexible shipments;
- priority objective dominating scheduled-count objective;
- scheduled-count objective dominating displacement;
- multiple optimal plans requiring deterministic behavior;
- an outage with zero impacted shipments;
- repeated independent outage requests against unchanged baseline state;
- shuffled lane/booking input rows;
- malformed/duplicate baseline data.

## 6. Verification and testing — 8 points

- **7–8 Excellent:** Adds focused tests that prove at least one global-contention counterexample plus several boundary/validation cases; verifies objective totals rather than only individual placements.
- **5–6 Acceptable:** Meaningful tests beyond the supplied baseline.
- **2–4 Partial:** Mostly happy-path tests.
- **0–1 Failing:** Little or no verification.

## 7. Code quality — 4 points

Clear naming, sensible separation of indexing/candidate generation/optimization/materialization, deterministic iteration where needed, and no gratuitous framework or infrastructure rewrite.

## 8. Walkthrough and tradeoff defense — 4 points

Candidate can explain why local greedy decisions fail, how the chosen approach preserves objective precedence, expected time/memory behavior, pathological cases, and whether an LLM/heuristic belongs in the critical planner.

## Overall calibration

- **90–100:** Excellent; robust, production-aware, and clearly defended.
- **75–89:** Strong/acceptable; correct core with limited gaps.
- **60–74:** Partial; useful implementation but meaningful optimality, scaling, or edge-case weaknesses remain.
- **Below 60:** Incomplete, locally greedy/brute-force, or materially incorrect under the stated constraints.
