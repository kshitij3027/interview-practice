# OpsDispatch — interviewer notes

**POST-PRACTICE ONLY. Never copy this file, its contents, or the grading rubric into a candidate branch or its ancestry.**

## Intended underlying structure

This is **capacitated, priority-weighted bipartite assignment with a shared intermediate pod quota**, reducible to a min-cost circulation / min-cost flow network. Incidents are at most once, responders have individual slot limits, and pod groups cap aggregate assignments. A simple feasible network is source -> pod (pod limit) -> responder (responder capacity) -> incident (one unit per allowed route, edge ETA-based cost) -> sink (one unit incident limit). The candidate must discover that the min ETA / max coverage objective is a **global** property, not per-incident greedy.

Alternative node directions are valid if all limits stay intact. Introduce severity rewards on incident coverage to implement a lexicographic objective, or perform multiple constrained optimization stages. A workable reward scheme with N = number of incidents and E = maximum ETA <= 240 is B = N*E + 1, W2 = B, W1 = (N+1)*W2, W0 = (N+1)*W1. Giving a covered sev0/sev1/sev2 unit a negative cost -W0/-W1/-W2 and each selected route its nonnegative ETA makes reducing total cost prioritize sev0 counts, then sev1, then sev2, then ETA. Stop augmenting once no negative-cost source/sink augmentation remains; do not force every feasible incident to be assigned if it would worsen the true objective (with these weights, any available incident will still have negative net marginal cost unless it sacrifices too many higher-priority placements). Be careful to maintain valid residual rerouting paths and reverse edges.

IMPORTANT: The reward inequalities need a rigorous check: the maximum lower-tier reward plus ETA swing for an arbitrary pair of plans must not outrank a one-unit higher-tier gain. A safe scheme uses U = N*E+1, W2=U, W1=(N+1)*U, W0=(N+1)*W1; these work since at most N assignments occur and total ETA spans at most N*E. If using successive-shortest-augmenting paths with large negative costs, apply Bellman-Ford/SPFA or correctly initialized potentials, then Dijkstra on reduced costs; native Dijkstra on negative edges is invalid. Output tie must be deterministic via stable indexing and edge exploration or another explicit policy. Equal-optimum assignments are all valid, but each implementation's results must not vary with input row order.

## Time and space complexity

Let P be pods, R responders, I incidents, A route options, F the number of assignments. Flow network has O(P+R+I) vertices and O(P+R+I+A) arcs (including reverse arcs). A straightforward augmenting-path implementation can take O(F * (A + P + R + I) log(P+R+I)) under suitable shortest-path data structures, which may struggle at production volumes. Stronger designs use cost scaling, batching, component partitioning and justified solver/library choices; the candidate should characterize the actual bottleneck and memory amplification (Python adjacency/object overhead). A correct small-instance baseline plus a defensible production strategy is better than asserting nonexistent performance.

## Why naive approaches fail

- Greedy shortest ETA for sev0 can block another sev0 whose only option is the first one's chosen responder.
- Greedy sev0 then sev1 without rerouting can be suboptimal at either tier when earlier assignments occupy scarce pods.
- Greedy individual capacity is not enough because two responders can share a pod with a lower ceiling.
- Minimizing total ETA *before* maximizing priority counts can drop a critical ticket to save travel.
- Ranking severity by an unbounded arbitrary score fails lexicographic dominance at high N.
- Solving each incident independently creates quota violations, double assignment, or globally inferior choices.

## Expected discovery from fixtures

P0-A can be assigned to N-1 quickly, but P0-B is eligible only for N-1. To cover all three critical incidents the planner may need to use alternate responders even with longer routes. E-1 and E-2 share EAST's pod cap of one, so their nominal personal capacities cannot be treated independently. Z-1 appears as a zero-ETA option but SHADOW's pod cap is zero. One duplicated P0-A,N-1,1 route is harmless. Several incidents have options that compete for NORTH/SOUTH, and some have no capacity available after critical dispatches.

## Checks and interviewer walkthrough

Run baseline tests first. Validate a full plan by recomputing assignments and checking every route, incident uniqueness, responder loads, pod loads, severity counts and summed ETA from scratch. For small random fixture instances, compare priority coverage tuple and total ETA against exhaustive enumeration (not the specific assignment, because equal-optimal assignments are legal). Verify row permutations do not change output. Try all zero-capacity cases, isolated incidents, responders only in zero-cap pods, and routes with tie ETAs. Use a synthetic skew where almost every incident has edges to the same pod. Ask why their algorithm can change an earlier assignment if that enables a more valuable one.

Expected 60-minute prioritization: ~10 minutes inspect/define invariants, ~10 formulate optimization and representation, ~25 implement core algorithm with clean data contract, ~10 adversarial tests and counterexample checks, ~5 explain scale and limits. Strong candidates use AI for scaffolding/proof exploration but actively challenge surprising results with a small exact oracle.

## Alternative defensible designs

A general-purpose exact optimization library may be appropriate for production if dependencies are acceptable; this starter intentionally needs none. Deterministic combinatorial algorithms are favored for exact, small-integer feasibility/optimality; an LLM may help translate constraints or generate tests but cannot provide a proof that every produced plan globally maximizes the stated objective. Heuristics can be part of an explicitly labeled fallback if time-bound constraints make exact solve impossible, but an unqualified claim of meeting this exact contract is not acceptable.
