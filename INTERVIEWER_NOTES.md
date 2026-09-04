# POST-PRACTICE ONLY — Interviewer Notes

Do not read this file before completing the 60-minute exercise.

## Intended underlying problem structure

Once an outage is fixed, each impacted shipment can use a finite set of feasible `(lane_id, slot_start)` resources, and every such resource has capacity one. The core is a weighted assignment problem over a sparse bipartite feasibility structure.

A strong exact solution typically models impacted shipments on one side and currently available compatible lane-slots on the other. Feasible shipment/resource pairs become edges. The optimization must preserve three objectives lexicographically: maximize assigned priority, then assigned count, then minimize displacement. This can be solved with a min-cost flow / weighted matching formulation, staged exact solves, or another exact assignment method with equivalent guarantees.

The candidate should discover the model from the customer constraints rather than being told to use matching or flow.

## Strong solution approach

Preprocess the static baseline once:

- index lanes by site and capability;
- index baseline occupancy by `(lane_id, slot_start)`;
- index bookings by lane/time so an outage can locate impacted shipments without scanning all daily bookings;
- retain immutable baseline state so outage requests remain independent.

For one outage:

1. Identify impacted bookings whose current lane is unavailable at their current slot.
2. Build fixed occupancy from unaffected bookings; all impacted original slots are considered vacated before assigning any impacted shipment.
3. Generate feasible resources only within each impacted shipment's time window, compatible site/capability lanes, lane operating window, and outage availability.
4. Optimize globally over shipment-to-resource edges.
5. Materialize sorted assignments/unassigned IDs and recompute summary totals from the chosen plan.

For a cost-based formulation, objective scaling must be mathematically safe. One common pattern makes the reward for one unit of shipment priority dominate the maximum possible contribution of count and displacement across the entire outage, and makes one assigned shipment dominate any possible displacement difference. Another defensible approach performs sequential exact optimizations while constraining previous objective optima. The interviewer should not require a specific encoding if the candidate can prove the precedence is correct.

## Complexity

Let `I` be impacted shipments, `R` candidate lane-slot resources, and `E` feasible shipment/resource pairs after pruning. Baseline preprocessing should be near linear in lanes/bookings. Per-outage candidate generation should depend on the outage-local data and feasible windows, not all 900k daily bookings.

For a standard successive-shortest-path min-cost flow implementation, the exact runtime depends on the solver; a common sparse implementation is roughly proportional to the amount of assigned flow times shortest-path work over `V = O(I + R)` and `E` edges. This is credible for typical 20–400 shipment outages when candidate generation is sparse. Severe 8k-shipment outages require discussion of solver choice, decomposition, specialized matching implementations, or bounded fallback/approximation strategies.

The key scale insight is that enumerating the cross-product of all site lanes × all day slots × all shipments is unnecessary. Candidate edges should be generated from narrow time windows and capability indexes.

## Why naive approaches fail

- **Priority-sorted first-fit:** a flexible high-priority shipment can consume the only slot available to another high-priority/narrow shipment, reducing total retained priority.
- **Earliest-slot greedy:** can satisfy the same number/priority but produce unnecessary displacement.
- **Independent best slot per shipment:** double-books shared resources.
- **Backtracking over combinations:** fixture-sized success does not survive hundreds or thousands of impacted shipments.
- **Rescanning every booking per outage:** ignores the repeated-query production shape.
- **Using a single unproven weighted score:** may accidentally allow a lower-priority plan to win because displacement/count coefficients are too large.

## Subtle traps / hidden checks

1. `cold` is not satisfied by a `cold-chain`-only lane. The fixture deliberately contains both tokens.
2. An outage uses `[start, end)` slot-start semantics; a slot starting exactly at `end` is available.
3. `earliest_start` and `latest_start` are both inclusive.
4. A lane's `open_until` is exclusive; the 15-minute appointment must fit inside the lane's operating window.
5. Remove every impacted original booking from occupancy before generating assignments. Two impacted shipments must not block each other at old slots.
6. Unaffected bookings are immutable blockers even if moving one would improve the result.
7. Hidden contention case: one flexible shipment and one narrow shipment compete for a scarce slot; locally best/first-fit placement is globally inferior.
8. Hidden priority-vs-count case: one priority-10 shipment conflicts with two priority-4 shipments. Priority total wins even though fewer shipments are scheduled.
9. Hidden count-vs-displacement case: when priority ties, a plan scheduling more shipments wins regardless of displacement.
10. Hidden displacement case: only after priority and count tie should total absolute time movement choose the winner.
11. Input row shuffles must not change quality or nondeterministically flip output across runs.
12. `out-004` in the fixture has no impacted shipment and should produce an empty plan.
13. Processing `out-001` must not alter the baseline used for `out-002`.
14. Duplicate IDs, unknown lanes, wrong-site bookings/outages, double-booked baseline slots, unsupported baseline capabilities, timezone-less timestamps, and misaligned windows should fail validation.
15. Broad `general` capability can create many candidates; discuss pruning and site/time indexing rather than blindly expanding every slot in the day.

## What should be discovered from the supplied data

- JFK-05 supports `cold-chain`, not `cold`; substring capability matching is incorrect.
- Some outage-affected lanes remain usable immediately before/after the outage, so moving to a different time on the same lane may be valid.
- Nearby alternate lanes are already occupied at several attractive times, so candidate generation must respect fixed baseline occupancy.
- The multiple outage records are independent scenarios, not a cumulative event stream.
- There is an explicit zero-impact outage case.

## Alternative defensible designs

- Exact min-cost maximum-flow on the sparse shipment/resource network.
- Exact weighted bipartite matching with dummy unassigned resources and a rigorously encoded lexicographic objective.
- A trusted local optimization library if the candidate chooses to add one and can explain the model, portability, and complexity.
- For the severe-outage production tail, decomposition by disconnected feasibility components can reduce solver size without changing the optimum.
- A heuristic can be defensible only if the candidate clearly labels it approximate, measures optimality loss, and explains why the customer would accept that tradeoff. It should not be described as exactly satisfying the stated objectives.

An LLM is not naturally useful in the exact critical assignment path. It could help explain dispatcher constraints or generate diagnostics, but it should not decide resource assignments unless correctness is independently enforced.

## Likely AI-agent failure modes

- One-shot agent writes a priority-sorted greedy allocator because it looks plausible on the fixture.
- Agent uses `if required in capabilities_string`, causing `cold` to match `cold-chain`.
- Agent forgets to remove impacted old bookings from occupancy.
- Agent mutates a shared occupancy map and leaks the first outage's plan into later outage requests.
- Agent treats `latest_start` or outage `end` as the wrong boundary type.
- Agent implements a flow solver but uses shortest-path logic incorrectly with negative residual edges.
- Agent compresses the three objectives into arbitrary constants without proving dominance.
- Agent scans all bookings for every outage and claims production readiness because the fixture is small.
- Agent tests only that assignments are legal, not that the objective values are globally optimal.

## Recommended 60-minute prioritization

1. Nail impacted/fixed occupancy and candidate-generation semantics.
2. Build one adversarial contention test that disproves greedy local placement.
3. Implement a globally optimizing core for priority and count.
4. Add displacement as the tertiary objective without weakening the first two.
5. Materialize deterministic output and empty/no-impact cases.
6. Add boundary tests and explain scale; CLI polish last.

If time runs short, a correct sparse model with priority/count optimality and a clear plan for displacement is more valuable than a polished CLI wrapped around a greedy allocator.

## Walkthrough inspection points

After the hour, ask the candidate to show:

- the exact code path that makes impacted old slots free;
- one counterexample their solution handles that greedy first-fit does not;
- how objective precedence is guaranteed rather than assumed;
- the candidate count/edge count they would expect for a typical outage;
- what state is preprocessed once versus rebuilt per outage;
- a test for row-order determinism or tie handling;
- behavior for the zero-impact outage;
- what they would change for an 8,000-shipment severe outage.
