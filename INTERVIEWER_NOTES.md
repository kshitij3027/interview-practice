# RecoveryWave — Interviewer Notes

**POST-PRACTICE ONLY — do not read before completing the exercise.**

## Intended underlying structure
The static hard-dependency relationships form a directed graph. For a failed service, affected services are reachable in the reverse-dependency direction. Recovery ordering is complicated by strongly connected regions: services inside a directed cycle cannot be linearly ordered under the stated rule and therefore must be treated as one restart unit. Collapsing those regions yields an acyclic component graph that can be scheduled into deterministic waves.

The candidate-facing problem intentionally avoids naming any of these techniques.

## Strong solution approach
A strong deterministic design typically does the following at startup:
1. Load services into an ID-indexed table.
2. Validate dependency endpoints once; count invalid rows.
3. Ignore soft dependencies for recovery propagation.
4. Deduplicate hard edges.
5. Build both dependency and reverse-dependency adjacency structures.
6. Identify mutually dependent components once on the static graph.
7. Build a condensed component graph and useful component metadata such as member IDs, minimum tier/member tie-break key, region membership, and reverse adjacency.

At query time:
1. Resolve known/unknown failed IDs and apply region eligibility.
2. Traverse reverse relationships from the failed component(s) to discover affected components, respecting region semantics.
3. Restrict scheduling to the affected component subgraph.
4. Compute prerequisite counts within that subgraph and emit eligible components in deterministic waves.
5. Expand each component to lexicographically sorted service IDs.

An alternative acceptable design may compute component structure only inside the affected subgraph per query if the candidate gives a convincing latency argument for typical incident size. That trades startup work for query cost and can still be defensible.

## Expected complexity
For full static preprocessing, a strong solution is roughly linear in static graph size at startup: O(V + E), with O(V + E) memory.

Typical incident planning should be proportional to the affected portion plus its relevant incident edges, e.g. O(Va + Ea) or O((Va + Ea) log Va) depending on the deterministic-ready structure. It should not rescan all ~1M dependency rows for every incident.

Materializing transitive closure is unacceptable at the stated scale.

## Why naive approaches fail
- Repeatedly scanning every dependency row until no new affected service is found becomes expensive and can approach quadratic behavior.
- A normal dependency-order pass that assumes acyclicity will stall or omit services when loops exist.
- Recursive traversal may overflow Python recursion depth on long production chains unless handled carefully.
- Precomputing reachability for every service can explode memory.
- Using sets/dicts without explicit ordering can violate deterministic output.
- Treating soft dependencies as hard over-expands incidents.
- Applying region filtering only at output time can let out-of-region nodes incorrectly propagate impact/order constraints.

## Subtle traps
1. **Direction:** `A depends_on B` means if B fails/restarts, A is affected; traversal for impact runs opposite the declaration direction.
2. **Cycle semantics:** `shipping <-> routing` and `legacy-sync <-> partner-feed` must each be restartable as one indivisible same-wave unit when affected.
3. **Self edge:** `search -> search` must not cause an infinite loop or special failure.
4. **Duplicates:** duplicate `checkout -> pricing` must not alter counts or readiness.
5. **Malformed endpoints:** `ghost -> identity` and `checkout -> missing-service` are ignored and counted as two invalid rows. The duplicate requirement says count rows, not unique invalid endpoint pairs.
6. **Soft edge:** notifications depends softly on orders and must not become affected solely because orders restart.
7. **Region:** an incident scoped to `us-west` cannot pull in another region through traversal or ordering.
8. **Multiple failed roots:** discovery must unify overlap without duplicates.
9. **Tie-breaking:** the candidate should explicitly implement deterministic ready selection; incidental iteration order is insufficient.

## Hidden evaluator-style checks
Use additional data to verify:
- a 50k-node linear chain without recursion failure;
- a dense 8-service cycle with incoming and outgoing branches;
- two separate loops connected by a one-way hard edge;
- duplicate hard edges repeated hundreds of times;
- soft-only branches that never propagate;
- two failed roots with heavily overlapping affected sets;
- region filtering that cuts across a dependency edge;
- unknown failed IDs mixed with valid IDs;
- malformed dependency rows with both unknown source and unknown target;
- shuffled input row order producing byte-equivalent semantic JSON output;
- a case where tier/service tie-breaking changes which simultaneously eligible component is selected first;
- repeated queries against the same loaded planner to ensure static preprocessing is reused.

## Alternative defensible designs
- Iterative component discovery on the incident-induced affected graph rather than globally at startup can be acceptable if preprocessing is otherwise reused and the candidate demonstrates plausible latency for typical 10–5,000 service incidents.
- A heuristic or LLM is not needed for the core problem because the semantics are exact. An LLM could be useful around malformed metadata interpretation or operator explanation in a broader product, but putting an LLM in the ordering loop adds nondeterminism without benefit.
- More aggressive caching of incident reachability sets may help repeated hot failures, but must be justified against memory limits and static-graph assumptions.

## Likely AI-agent failure modes
- One-shot implementation reaches for a plain topological sort and fails cycles.
- Agent misreads dependency direction.
- Agent rescans the full dependency list inside every incident.
- Agent produces nested DFS recursion that passes fixture tests but is unsafe on long chains.
- Agent ignores region semantics during traversal.
- Agent adds excessive frameworks or an LLM integration instead of solving the deterministic core.
- Agent writes only happy-path tests because candidate-visible tests are intentionally minimal.

## What the candidate should discover from the fixture
The data visibly contains duplicate rows, a self-link, two multi-service loops, soft edges, malformed endpoints, separate regions, and incidents targeting different shapes. A strong candidate should inspect these before coding and mention that the fixture is signaling correctness traps rather than being representative of production volume.

## Recommended 60-minute prioritization
- **0–8 min:** inspect README/data, restate dependency direction, identify scale and loop risks.
- **8–15 min:** choose static indexes and data model; explain complexity target.
- **15–38 min:** implement impact discovery and loop-safe ordering core.
- **38–50 min:** add deterministic ordering, region/unknown/malformed handling, CLI reuse.
- **50–58 min:** focused tests for a loop, propagation, ordering, unknown/region cases.
- **58–60 min:** run fixture, inspect output, summarize tradeoffs and known limitations.

## What to inspect during walkthrough
Ask the candidate to explain:
- why their edge direction is correct;
- what work happens once vs per incident;
- how a loop is represented and scheduled;
- worst-case startup, memory, and query complexity;
- how deterministic output is guaranteed;
- what happens on a 200k-node graph with 10k repeated queries;
- why an LLM is or is not appropriate for the core planning path.
