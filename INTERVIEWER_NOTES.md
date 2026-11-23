# BatchPath — Interviewer Notes (POST-PRACTICE ONLY)

**Never show this document to the candidate before practice.** The problem-solving strategy should be discovered from the business specification.

## Intended underlying problem structure

This is a directed dependency graph with node durations and release-time lower bounds and edge handoff delays. Each active prerequisite u -> v enforces start(v) >= finish(u) + lag. If all requirements in the ancestor closure are acyclic, earliest finish is a longest-path dynamic program over a dependency ordering, with local earliest time as an additional lower bound. Since run_min is strictly positive, any directed cycle creates impossible circular prerequisites; all of its downstream dependents are also blocked. A cycle in a disconnected or unrelated component is irrelevant to healthy targets.

## Strong exact approach

First read and validate the entire catalog. Index dataset IDs and tenants. Track every (link_id, revision) to reject inconsistent replays while permitting identical duplicates. The logical link's highest numeric revision is authoritative; validate all earlier upserts as well. Preserve distinct active links even when endpoints coincide (they may have different lag). Check tenant ownership for all endpoint references.

Construct outgoing edges and an incoming requirement count for each dataset. Initialize every node's own lower bound earliest_min and its runtime. Process nodes whose incoming requirements are all satisfied. Each finished prerequisite can advance a downstream node's feasible start to max(current, finished_time + lag), and update the designated predecessor at equal times using the case-sensitive lexicographically smallest prerequisite ID. If a dependency's completion + lag equals earliest_min, the dependency MUST win over the node's own release-time baseline. When all incoming requirements have been processed, that node's earliest finish is fixed, and its outgoing edges can be processed. A queue-based topological elimination is a natural design.

At termination, every processed node is schedulable. Every node not processed belongs to a directed cycle or is downstream of one: any remaining node has at least one incoming edge from the remaining set, so tracing backwards in a finite set eventually enters a cycle. This eliminates the need for an explicit recursive cycle search when computing readiness. For a valid target, consult its precomputed status and ready time; reconstruct the controlling chain by following the stored predecessor choices backward and reversing, stopping at a node whose own earliest_min dominates every requirement. Unknown tenant/dataset is a per-line invalid response.

Expected time for snapshot preparation is O(V + E + R), expected dictionary operations, where V = datasets, E = active links, R = revision rows. Additional query work is O(1) except O(length of emitted chain), which is unavoidable. Memory O(V + E + R) unless revisions are safely compacted. Avoid storing whole path strings for every node, as that can be quadratic on chains.

Alternative defensible approaches: strongly connected components with downstream blocked propagation, then dynamic programming on the resulting schedulable subgraph; iterative post-order dependency analysis with correct tri-state cycle handling and memoization. A hybrid or AI-assisted system is acceptable only with a deterministic exact core and scale-conscious verification.

## Why naive approaches fail

- Adding all upstream runtimes counts concurrent tasks sequentially and inflates earliest completion.
- Following the first, fastest, or arbitrarily ordered prerequisite misses another slower requirement.
- Using physical CSV order to select revisions applies stale corrections or revives withdrawn edges.
- Collapsing links by (source, target) loses multiple valid requirements with different lags.
- Rejecting the whole tenant when any cycle exists is overbroad; checking only cycles containing the target overlooks upstream cycles.
- Recursive traversal risks failure on deep production chains; per-query whole-graph traversal scales as O(Q*(V+E)).
- Forgetting intermediate node earliest_min or comparing deadline to start rather than finish violates the contract.
- Naive tie-breaking by link ID or input order does not satisfy predecessor-ID tie rules, especially when a requirement ties the local earliest_min.

## Fixtures and meaningful discoveries

- A5 originally links SIDE to MART with a costly lag but revision 2 retracts it; it must not delay MART.
- A6 revises SIDE-to-MART into RAW_B-to-MART at revision 2. The lower revision appears later and must not win.
- A1 is delivered twice identically and is a single logical requirement, not a conflict.
- LOOP_A and LOOP_B cycle; DOWNSTREAM is blocked because it requires LOOP_B. MART, FRESH, TIED and the BLUE tenant's DASH are not blocked.
- MART depends on CLEAN, while CLEAN depends on two independent sources. The scheduling result is governed by the latest requirement, not the sum of all source runtimes.
- TIED includes a local release-time lower bound and multiple incoming requirements; verify tie precedence against the own release time.

## Hidden checks for an evaluator to construct independently

1. A 150,000-node chain and repeated lookups: no recursion failure or repeated full scan; outputting an actual large chain may take proportional time.
2. Wide diamond dependencies with equal completion candidates. Confirm tie by direct prerequisite ID, not the edge or revision ID or ingestion order.
3. Exact external-versus-local tie: where incoming finish+lag = earliest_min, select external predecessor.
4. Two separately identified links with identical endpoints but different lags, and withdrawal of one. Do not collapse both into one.
5. A self-loop, a multi-node cycle, acyclic upstream feeders, a long downstream tail and a disconnected healthy component: only the cycle and dependent tail are blocked.
6. Invalid superseded upsert with unknown endpoint; still reject whole catalog. Conflicting same-revision copies, tenant changes across a link ID, invalid numeric notation and malformed CSV must also fail globally.
7. Same valid target requested with many deadlines including exact equality, and duplicated request IDs; identical readiness and independent responses.
8. Empty/invalid JSONL lines, wrong field types (boolean, float and string), Unicode identifiers, unknown tenant and cross-tenant dataset. Validate error precedence and continue after bad lines.
9. Randomly permuted revision rows and repeated identical rows give deterministic results.
10. Dataset whose local earliest start is later than all prerequisites, zero lags, and times accumulating past 32-bit bounds.

## Likely AI-agent failure modes

Single-pass over input file as if it were ordered; naive DFS that never marks downstream cycle dependence; path strings copied for each node; boolean accepted as integer; wrong orientation of a dependency edge; tie updating with only greater-than comparison and losing equal contribution; output path reversed; ignoring tenant containment; confidence in generated tests that never exercise assess; overengineering an app instead of solving the single algorithmic capability.

## Prioritization during 60 minutes

Minutes 0–8: inspect contract/fixtures, identify the exact readiness and cycle semantics.
Minutes 8–26: choose the graph representation and compute order, implement earliest-time propagation and blocked classification.
Minutes 26–39: deterministic predecessor chain and request output.
Minutes 39–52: tests covering revisions, unrelated/upstream cycles, ties, malformed inputs and CLI.
Minutes 52–60: run a deep-chain or wide-fan-in stress case and explain complexity/tradeoffs.

## Walkthrough inspection points

Ask the candidate to show that readiness cannot be finalized until all active incoming requirements have been considered; why a node left unprocessed after elimination cannot finish; how duplicates and retractions are reconciled; what happens when local earliest equals an upstream contribution; why equal predecessor selections are stable across CSV order; how the solution handles 100,000 repeated queries; and why memory and call-stack use remain bounded. Review actual code and tests rather than AI-generated assertions.
