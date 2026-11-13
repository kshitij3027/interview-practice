# POST-PRACTICE ONLY — WaterLine interviewer notes

**Never place this document, the rubric, or evaluator checks on the candidate branch or in its history.**

## Underlying structure (revealed after the interview)

This is exact connectivity-under-two-independent-edge-deletions with multiple designated source vertices and component aggregates. Queries are **independent**, so a traversal for every scenario is too costly. The baseline is the union of components containing at least one source; a query's loss is the baseline served aggregate minus the aggregate still served after its closures. Multiple pipes with identical endpoints remain distinct edges. Contraction into an undirected multigraph is sound only if pipe identifiers remain independent.

## Strong solution designs

1. **General offline batch method (recommended):** Treat each request as one index on a fictitious timeline. Each pipe is present at every index except the 0, 1 or 2 indices at which that request closes it. Collect absent-query indices per pipe, then insert all disjoint active-index intervals into a segment tree over request indices. DFS that tree with a **rollback disjoint-set union** (union by size, no path compression). Each root stores `source_count`/`has_source`, `meters`, `demand`, `critical`. Maintain global *unsupplied* counts. Before a union, subtract the unsupplied contributions of both roots; after the union, add the result if source-free. Log enough previous root and global state to revert at the end of a segment node. At a leaf, the three unsupplied totals are computed for exactly the open-pipe graph; subtract the same baseline unsupplied totals to get attributable impact. Precompute the baseline by ordinary connectivity on the full snapshot. Invalid request lines are isolated in the CLI; store the valid requests in physical-order slots, run the batch offline, then interleave invalid outputs without reordering. A duplicate pipe name in one request is one closure.

   With `n` nodes, `m` pipes, `q` valid requests, and at most `k=2` closures/request, total interval insertions are `O(m + kq log q)` (more conservative `O((m+kq)log q)`); each rollback union/find costs `O(log n)` worst case, giving `O((m+kq log q)log n)` union work, plus `O(m+n+kq log q)` storage if storing interval jobs, rollback history, and graph data. An optimized implementation must account for Python object overhead and skew; streaming/compact arrays or a compiled implementation may be advisable to meet the production time target. Initial baseline computation is `O(n+m)`.

2. **Hybrid specializing common scenarios:** Precompute connected-component and bridge information to answer zero/one-closure cases quickly, while batching two-closure scenarios using the offline method. This can be much faster if most reviews close only one pipe. It must still handle pairs that isolate a component even though neither control individually does. Another credible approach computes a two-edge-failure connectivity oracle or handles a small hot set of closure pairs with cached exact results, but must demonstrate bounds and correctness, not vague caching promises.

3. **Simple correctness oracle:** For tiny cases, remove the specified IDs from a multigraph, traverse from all sources, compare the reached nodes to a separately computed baseline, and sum only nodes lost. This is ideal for randomized property tests and validation; not the production strategy.

## Why naive approaches fail

- One BFS/DFS for each query costs `O(q(n+m))` — roughly 75k walks of 750k graph entities. A simple tree-only bridge test ignores pairs of individually noncritical pipes that collectively separate supply.
- Removing one endpoint pair rather than one pipe ID incorrectly removes parallel physical pipes. Disconnected legacy islands are already unsupplied and must not count in any repair's attributable loss.
- Treating the first source as the only supply invents outages. Summing every path or per-source meter count double-counts customer nodes.
- Standard DSU alone cannot delete an edge; path compression makes rollback difficult. Versioned events/stateful sequential closures violate query independence.
- Globally caching all previously evaluated request outputs does not solve adversarially diverse closure pairs or worst-case scaling.

## Hidden checks and subtle traps

- No closures yields zero; a self-loop cut changes nothing; one parallel link cut changes nothing but cutting both may sever a component.
- `PIPE-11` isolates J-08/J-09/J-10 in supplied fixtures: 505 meters, 280 lps, 6 critical. `PIPE-12` alone impacts zero; `PIPE-12` plus `PIPE-13` impacts 245 meters, 145 lps, 3 critical.
- `PIPE-01` plus `PIPE-07` leaves all non-source, previously served junctions unsupplied: 2040 meters, 1090 lps, 10 critical.
- `PIPE-14` isolates 45 meters, 35 lps, 1 critical. Closing `PIPE-14` twice is identical to once.
- `OLD-1`/`OLD-2` already have no source; their 150 meters, 75 lps, 1 critical must never be added to attributable impact.
- Closing two individually harmless controls can produce real loss; closing an edge inside a cycle may not. Cycles, disconnected components, mixed supplied/unsupplied components, zero-meter nodes, source-only components, shared source reachability, duplicate catalog rows, conflicting duplicates, strange CSV order, JSONL invalid isolation and repeated request IDs all matter.
- Add property-based small randomized multigraphs (including parallel edges and self loops), and compare every one-/two-closure answer against a slow independent oracle. Test exact field names, integer precision, stderr/stdout, and catalog atomicity.

## Likely AI-agent failure modes

A naive generated solution often returns zero because the starter smoke test passes; optimizes for one closure with Tarjan bridges but misses pair interactions; strips multigraph edges into a set of endpoint pairs; counts all disconnected nodes instead of newly disconnected ones; mutates one graph across independent scenarios; recomputes graph reachability per line; uses non-rollback path compression; incorrectly handles root aggregate updates on rollback; or trusts random Python hash ordering instead of explicit deterministic semantics. Ask the candidate to substantiate the cost of their approach, not merely state it is 'optimized'.

## Data inspection discoveries

The fixtures contain two reservoirs, a looped central grid, a redundant cross-connection, a downstream pocket, two distinct pipes sharing endpoints, an irrelevant self-loop, and an already disconnected old sector. There are intentional identical retry rows and bad JSONL requests. Their presence is evidence that a simple tree/path picture will not do.

## Suggested 60-minute prioritization and walkthrough

- Minutes 0–8: read README and inspect nodes/pipes/requests; state baseline-versus-post-closure invariant and exact output/error semantics.
- Minutes 8–18: build a tiny independent oracle and adversarial cases; choose a performant strategy with proof sketches.
- Minutes 18–45: implement offline or justified hybrid core, beginning with no-/single-/two-closure correctness; avoid needless UI or tooling setup.
- Minutes 45–54: run targeted tests and compare to oracle, especially the parallel pair, two-source isolation, baseline islands, and duplicates.
- Minutes 54–60: explain asymptotic/runtime/memory tradeoffs and how to improve unfinished portions.

During walkthrough inspect: representation of independently controlled physical pipes; preservation of query isolation and original output order; source-aware component aggregates; rollback correctness; whether a pair of non-bridge closures is handled; test design; and any AI-generated code that was accepted without checking its invariants. Deterministic exact approaches fit naturally, but validated alternatives are gradable on observable guarantees rather than a predetermined tech stack.
