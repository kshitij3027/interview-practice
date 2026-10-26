# POST-PRACTICE ONLY — AidLink Interviewer Notes

**Do not expose these notes, evaluator cases, or their contents to a candidate before the 60-minute exercise.**

## Intended underlying problem structure

This is a capacitated transportation optimization with a **lexicographic global objective**. Each depot has supply; each directed depot→clinic lane has its own capacity and nonnegative linear per-unit cost; each clinic receives up to critical plus routine demand. Critical units across *all* clinics outrank all routine units; within that optimum, routine service outranks cost. Merely sorting clinics by urgency, sorting lanes by cost, or filling one clinic at a time can fail because an initially used lane may have to be rerouted through another depot to open capacity for a constrained clinic.

A strong implementation can formulate a directed residual network with source→depot arcs (stock), depot→clinic arcs (lane capacity/cost), clinic→priority sink arcs (critical/routine capacities plus suitable priority reward), and a sink. It can optimize lexicographic objectives by staged constrained optimization or by rigorously bounded integer reward scaling. Rewards must dominate **all possible** downstream changes in delivery count and cost, not merely the largest single edge cost. In a reward encoding, the algorithm must continue augmenting while overall benefit is positive, then reconstruct **net** flow on original shipment lanes (not attempted augmentations). Reverse residual arcs are essential.

All quantities/costs fit exact integers but can exceed 32-bit range in sums and scaled objectives. One feasible class is successive shortest augmenting paths with residual arcs and potentials / an appropriate negative-edge initialization; other valid min-cost/max-flow or linear-programming formulations are acceptable. Each augment should use its bottleneck capacity rather than iterate per physical cylinder. Handle negative reverse costs correctly. Verify flow conservation, capacities, critical-first accounting, and minimum cost at fixed served totals.

## Complexity and scale

Let V≈depots+clinics+priority nodes and E≈lanes+depots+clinics. A shortest-augmenting-path implementation with efficient priority queues may cost roughly O(K·E·log V) after suitable potential initialization, where K is the number of augmentations, **not** the number of shipped units. This bound varies with initialization and implementation. K can still be large in adversarial dense/re-routing cases; Python 2-second p95 needs benchmarking and may motivate cost-scaling, topology reuse, decomposition by disconnected region, caching repeated scenarios, or an optimized solver. Avoid promising worst-case SLA by assertion alone. Memory should be O(V+E) per scenario for a sparse residual network, excluding request and cached structures. A raw exhaustive allocation enumeration is exponential; naive per-unit enumeration scales with numeric capacities up to 10^6.

## Where naive approaches fail

1. Cheapest-lane-first can exhaust the only depot that serves a remote clinic, even when an alternate depot could serve the nearer clinic.
2. Filling one clinic's critical needs in file order need not maximize total critical service; constrained connections require coordinated reallocations.
3. Serving routine demand before globally maximizing critical is invalid even if it substantially reduces transport cost.
4. Minimizing shipping cost alone can choose to ship nothing (zero cost) unless the higher-level service objectives are enforced.
5. Maximizing overall shipped units can sacrifice critical units for more routine deliveries, violating priority one.
6. Greedy nearest-feasible deliveries may maximize served totals but fail the **minimum cost among those** requirement.
7. One-step augmentations without reverse residual arcs do not permit required rerouting.
8. Reusing altered stock or clinic demand between separate what-if requests introduces invisible cross-query leakage.
9. Combining capacities of parallel lanes while using only one cost or ID corrupts results and hides valid alternatives.
10. Floating-point money, unbounded reward constants, or parsing booleans as ints break exact behavior.

## Hidden checks / adversarial examples

- **Rerouting:** Depot A has 1 unit and can serve X or Y, depot B has 1 and can only serve X; both clinics have one critical need. Correct service is 2 critical, requiring A→Y and B→X, independent of cheap A→X.
- **Urgency over economics:** A single depot has one unit and reaches clinic U (1 critical, cost 100) or clinic R (1 routine, cost 0). Send to U.
- **Routine only after critical optimum:** Several allocations serve equal critical totals; routine capacity varies. Choose greatest routine total before looking at cost.
- **Cost after service:** Two feasible allocations serve equal critical and routine totals, but one costs 17 cents and the other 18. Select 17.
- **Parallel lanes:** Same depot/clinic endpoints with caps 1 and 2, different prices. Respect each independently; report distinct sorted lane IDs.
- **Disabled bridge:** Removing one unique lane makes some demand unreachable even though stock remains ample elsewhere.
- **Overstock / no demand:** No invented shipments; all unused capacity stays unused.
- **Insufficient stock:** Total sent never exceeds depot stock; urgent total served may be below total urgent need.
- **Conflicting replay:** Same lane ID with differing cost must reject catalog before any planned results; identical duplicate rows must count once.
- **Invalid line recovery:** `[]`, bad JSON, negative, `true` instead of an integer, missing `routine`, unknown ID, and an otherwise valid line after all of them.
- **Input-order determinism:** Shuffle input CSV row order and scenario order, preserving valid business meaning; each scenario's shipment vector and cost should remain stable. Duplicate request IDs are independent.
- **Large capacity:** A lane with capacity 1,000,000 and a matching single need must not perform one million one-unit iterations.
- **Zero-cost cycle / reallocation:** A correct residual implementation must terminate and not misreport negative flow on an original lane.

## Fixture discoveries the candidate should articulate

- `L-03` and depot `D-RIDGE` are exact replay rows, not extra supply/capacity.
- `L-05` and `L-10` provide independent routes to the same clinic with different limits/costs.
- `D-EMPTY` has no stock in the base case, so `C-ISLAND` is not reachable with its initial demand despite an approved lane.
- Several clinics share constrained depots and alternatives; a globally optimized plan must consider the entire snapshot.
- The `closure-east`, `extra-stock`, `fully-idle`, and override requests change **only** their own snapshots. Some physical request lines are intentionally invalid.

## Alternative defensible designs

- Multi-stage maximum-flow calculations followed by minimum-cost allocation that preserves exact previously optimized totals.
- A properly specified integer linear program or proven equivalent network-optimization method if environment/setup allows; candidate starter itself needs no external services.
- Cached topology with rebuilt capacities/costs per independent scenario. A heuristic/LLM may aid modeling or testing but cannot replace exact optimization evidence under this contract.

Do not penalize a candidate for choosing a different exact formulation. Do penalize a plausible but unproven greedy approach that passes only simple fixture rows.

## Likely AI-assistant failure modes

Generating a per-clinic greedy loop from the customer prose; using min-cost-flow without priority protection; reusing a buggy generic solver with incorrect reverse-edge indices; treating all lanes between identical endpoints as one; arithmetic reward constants too small; continuing augmentation after its net benefit becomes nonpositive; computing `routine_served` by totals instead of per-clinic need; exposing internal nodes as shipments; forgetting deterministic sorting; and writing tests that mirror the implementation rather than independent counterexamples.

## Suggested 60-minute prioritization

- 0–10 minutes: read fixture and contract, identify global lexicographic objectives and validation boundaries.
- 10–20: choose exact model; decide representation and objective ordering; construct a two-depot counterexample.
- 20–43: implement core planner incrementally, including residual rerouting and shipment reconstruction.
- 43–54: verify with tiny independent cases (including three priority tiers, costs, parallel arcs and disabled lanes); run starter scripts.
- 54–60: explain proof outline, complexity, worst-case performance, and implementation limits.

## Walkthrough inspection points

Ask: Why do lower-tier units never displace a higher-tier feasible unit? Can a previous shipment be reversed when a better allocation is discovered? How does lane-level capacity survive multiple lanes with identical endpoints? How are scenario overrides kept isolated? How are the returned critical/routine totals derived at each clinic? What happens with negative residual costs, zero-cost links, or very large unit counts? How would the candidate benchmark and instrument the target SLA? Verify the candidate can defend these decisions without memorizing generated code.
