# POST-PRACTICE ONLY — Interviewer Notes

## Intended underlying problem structure

This is a resource-constrained path-planning problem on a directed adapter catalog. The request has three hard resources: latency, quality loss, and adapter count. Cost is the primary optimization objective, followed by quality loss, latency, hop count, and adapter-ID sequence.

The critical insight is that **one best label per schema is not sufficient**. A cheaper partial chain can consume too much latency or quality budget to complete, while a more expensive partial chain to the same schema can remain feasible and ultimately win. A strong exact solution therefore keeps multiple non-dominated partial states/labels per schema (and usually hop count), prunes states that cannot improve another along all relevant dimensions, and uses an ordered work queue to explore promising labels first.

## Strong solution approaches

A strong implementation can:

1. preprocess deterministic outgoing adjacency once, already filtered only for structurally valid catalog rows;
2. per request, normalize the disabled set and filter edges by region/disabled status during expansion;
3. represent a label with current schema, cumulative latency/loss/cost, hops, predecessor/path identity, and enough information for deterministic tie resolution;
4. reject expansions that exceed any hard budget;
5. maintain a Pareto frontier for each appropriate state bucket, pruning a new label only when an existing label is no worse in every resource/objective dimension needed for future feasibility and final ranking;
6. use a priority queue ordered by cumulative cost and the later objective dimensions, with deterministic tie behavior;
7. track the best feasible target result and stop only when queue ordering plus non-negative costs makes further improvement impossible.

Because all metrics are non-negative, dominance pruning is safe when defined carefully. Keeping hop count in the dominance relation/state is important because remaining hop budget differs. A candidate can instead use dynamic programming by hop count plus Pareto frontiers, or another exact label-setting/label-correcting method.

## Complexity

Static preprocessing is approximately O(E log d) if each adjacency list is sorted, where E is the number of adapters and d is local out-degree. Query complexity is output/frontier-sensitive rather than simply O(E log V): roughly proportional to the number of non-dominated labels generated plus eligible outgoing expansions. Worst-case Pareto-frontier size can be exponential for adversarial multi-resource instances; a strong candidate should acknowledge that exact resource-constrained shortest path variants do not have a universally tiny frontier.

For the stated production profile, small `max_adapters` plus bounded real-world budgets and aggressive safe dominance pruning make this credible. Stronger production variants could add lower-bound heuristics, reverse precomputed optimistic bounds, budget quantization (if approximation allowed), cache keys for repeated requests, or operational caps with explicit fallback behavior.

## Why naive approaches fail

- **Cheapest-first Dijkstra with one distance per schema:** unsafe because the cheapest partial state may consume more latency/loss than a costlier state and block completion.
- **BFS / fewest adapters:** optimizes the wrong objective and ignores weighted constraints.
- **Pick cheapest outgoing adapter greedily:** local decisions do not compose globally.
- **Enumerate every simple chain up to max hops:** branching makes this exponential and production-implausible.
- **Search unconstrained cheapest path then reject if over budget:** can miss a more expensive but feasible route.
- **Visited-schema set:** invalid for the same reason as one-label Dijkstra; revisiting a schema with a different resource profile may be necessary.

## Subtle traps / hidden checks

- Two different paths reach the same intermediate schema: one is cheaper but nearly exhausts latency; only the other can reach the target within budget.
- A corresponding case where quality loss, rather than latency, is the resource that makes the cheaper prefix unusable.
- Total exactly equal to `max_latency_ms` or `max_quality_loss_ppm` must be accepted.
- `max_adapters = 0` with different source/target is unreachable; same source/target is a valid zero chain.
- Zero-cost and zero-loss cycles must terminate; equality/dominance handling cannot allow infinite duplicate labels.
- Global (`*`) and exact-region adapters coexist.
- Disabled IDs contain duplicates and unknown values.
- Exact duplicate adapter records are harmless; conflicting records with the same ID are dataset corruption.
- Several feasible target paths tie through cost/loss/latency/hops; lexicographically smaller adapter-ID sequence wins.
- Shuffling `adapters.csv` rows must not change output.
- A deprecated schema remains legal unless the requirements say otherwise.

## Visible fixture observations worth discovering

The fixture includes cycles between `bridge-a` and `bridge-b`, a very cheap but high-loss legacy path, region-specific US/EU alternatives, a duplicate catalog replay, a zero-hop request, an impossible tight-budget request, and disabled adapter duplicates. The candidate should inspect these rather than treat the fixture as a flat list.

## Alternative defensible designs

- Exact dynamic programming by hop count with Pareto frontiers.
- A* / best-first constrained search with admissible reverse lower bounds for cost/latency/loss.
- Integer programming or generic optimization solver can be correct for small batches, but dependency/setup and p95 latency must be defended.
- Approximate budget bucketing or beam search can be production-useful only if the candidate clearly states that it sacrifices the exact observable contract.
- LLM-based reasoning may help explain adapter metadata but should not be trusted as the exact optimizer for this numeric catalog unless wrapped by deterministic verification.

## Likely AI-agent failure modes

- One-shot generation of ordinary Dijkstra with `(cost, node)` and one `best[node]` value.
- Treating budgets only when the target is reached instead of pruning/representing them during search.
- Using a `visited` set that removes valid alternative labels.
- Reconstructing a path from mutable per-node parents even when several labels per node exist.
- Ignoring deterministic final tie-breaking.
- Adding third-party graph libraries unnecessarily.
- Writing tests that mirror only visible requests and never create the adversarial same-intermediate tradeoff case.

## Recommended prioritization for 60 minutes

1. Model request eligibility and cumulative constraints precisely.
2. Build an exact minimal planner with correct state representation and safe pruning.
3. Add targeted adversarial tests for competing labels and boundaries.
4. Wire CLI output and deterministic path reconstruction.
5. Discuss scalability/frontier growth and optional optimizations if time remains.

## Walkthrough inspection points

After the hour, ask the candidate to explain:

- what makes two partial states at the same schema meaningfully different;
- the exact rule used to discard one state as dominated;
- why that rule is safe with remaining hop/latency/quality budgets;
- how cycles terminate;
- how final tie-breaking stays deterministic;
- the worst-case and typical-case frontier size;
- what their tests prove that the visible fixture alone does not.
