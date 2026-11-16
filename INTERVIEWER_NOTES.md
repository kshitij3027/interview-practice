# POST-PRACTICE ONLY — ChronoCheck Interviewer Notes

**EVALUATOR-ONLY. DO NOT VIEW OR DISTRIBUTE BEFORE THE 60-MINUTE PRACTICE.**

## Intended underlying problem structure

The latest *active* measurements form a signed-potential constraint graph. Each directed statement (a,b,d) requires potential[b] − potential[a] = d, where potential represents a clock reading relative to an arbitrary reference. A connected component is either consistent (all exact differences uniquely determined) or inconsistent (no assignment satisfies all equations). No absolute time reference exists. Request status depends on component relation and inconsistency, not on existence of a direct measurement.

## Strong solution approaches

**A. Weighted disjoint-set with relative potentials** is memory efficient. Maintain parent, size, weight and bad flags. Invariant: weight[x] = potential[x] − potential[parent[x]]. A weighted find returns (root, wx), where wx = potential[x] − potential[root], compressing paths while correctly accumulating differences. For constraint potential[b]−potential[a]=d, find (ra,wa) and (rb,wb). If ra==rb, check wb−wa==d; a mismatch marks that root bad. Otherwise, attach root rb under ra with weight[rb] = d + wa − wb and merge bad flags. If union-by-size attaches root ra under rb instead, weight[ra] = wb − wa − d. Distinct roots answer unresolved; same bad root answers conflict; otherwise delta_us = wb − wa. Initialize even unmeasured isolated clocks. Validate tenant membership before building relationships.

**B. One-time adjacency traversal with potentials** is an equally strong alternative. Create signed edges both ways from current upserts. Traverse each connected component once, assigning a root potential of zero and propagating offsets. If an already visited endpoint contradicts a new implied offset, mark the component bad. Store component ID, potential, and component bad flag for every clock. All query answers use O(1) lookup. This version can be simpler in a 60-minute interview but consumes O(E) adjacency memory, especially when the graph is dense.

**Expected complexity:** with V clocks, R revision rows, E latest active measurements, and Q requests, reconciling revisions costs O(R) expected time and O(R) storage when retaining each distinct ID/revision for conflict validation. The DSU solution uses O((V+E+Q) α(V)) time and O(V) graph state after reconciliation; graph traversal uses O(V+E+Q) time and O(V+E) graph state. Python dict/string/tuple overhead on 1.5m clocks and 4m revision rows should be discussed: compact integer indices, streaming reconciliation, careful retention of duplicate-revision evidence, and memory pressure from dense graphs are relevant.

## Why naive approaches fail

A direct lookup misses multi-hop relationships; a full BFS per request cannot handle 800k hot queries. Reading the last physical CSV row as latest revision is wrong. Treating updates as streaming active constraints without removing superseded ones leaves stale contradictions or links. Removing one arbitrary edge from an impossible cycle silently fabricates an answer. Taking an average of offset reports is incompatible with an exact constraint contract. A universal clock origin cannot be inferred: connected consistent groups only identify *relative* offsets.

## Subtle traps and hidden checks

1. Sign orientation: b−a = −4 implies a−b = +4; some generated union formulas reverse this.
2. Inconsistent triangles, repeated parallel claims under different measurement IDs, zero self-loops, and nonzero self-loops.
3. Contradictory groups make *every pair within them*, including x→x, a conflict. Two separate inconsistent groups are still unresolved relative to one another.
4. A retraction at higher revision eliminates earlier upserts even if its CSV row appears first. A still newer upsert can restore the measurement.
5. Identical replay of (ID,revision) is harmless; conflicting replay is fatal even when a larger revision exists. Bad superseded upserts are fatal too.
6. An isolated clock queried against itself returns +0, but versus another isolated clock is unresolved.
7. Graph or DSU preprocessing must not mix tenant boundaries or let contradiction flags from one component contaminate others.
8. Signed integer arithmetic must tolerate long chains where total implied difference exceeds one measurement's allowed bound and can exceed 64-bit.
9. Duplicate request IDs are independent; malformed JSON lines are isolated. Well-formed query naming a clock in another tenant returns unknown_clock without leaking tenant details.
10. Case sensitivity, duplicate clock declarations, canonical CSV numbers (-0 invalid), CSV row permutation, blank input lines, bool request IDs, and output order.

**Hidden verification idea:** Make small generated graphs with known assigned potentials, add consistent redundant constraints, then inject one contradictory edge. Compare candidate output against a separate traversal oracle. Randomly shuffle CSV rows and query IDs. Make a bad group connect to a previously good group and verify flags propagate. Keep these checks evaluator-only, never on the candidate history.

## What the candidate should discover from fixtures

Acme: measurement m_B has unordered revisions 2,1,3; revision 3 restores -20. m_C is later retracted and should not contribute. Main Acme group is consistent, while a separate solo_1 device has a nonzero self-report and is inconsistent. Globex: the active g1→g2 (8), g2→g3 (7), and g1→g3 (20) form a contradiction; g4 is in that same connected group through m_J. m_T is retracted and should not contribute. Umbra: one consistent 999-microsecond relation. Duplicated clock declarations, one identical measurement retry, repeated request IDs, invalid requests and a cross-tenant reference are intentional.

**Expected fixture outcomes:** q1 Acme edge_1→edge_3 is ok +130; q2 Acme edge_5→edge_1 is ok −230. q3 and q4 Globex are conflict. q5 solo_1→solo_1 is conflict. q6 solo_1→edge_1 is unresolved. q7 Umbra u_a→u_b is ok +999. q8 and q10 are invalid unknown_clock; q13 Umbra reverse is ok −999. The boolean request ID and malformed JSON are invalid invalid_query.

## Alternative defensible designs

A compact indexed array traversal may use less Python memory than a dict-heavy weighted DSU with pointers. A general algebraic constraint solver per component is potentially correct but requires scaling justification. LLM or heuristic triage may assist with parsing explanations and human investigation, but cannot directly replace exact mathematical outputs without independent verification. A storage-backed precomputed snapshot can be justified if performance and cost are measured; do not award points simply for using another service.

## Likely AI-agent failure modes

Wrong union sign when swapping roots, incomplete path-compression weight updates, treating every same-clock query as zero, using all revisions instead of only current active revisions, ignoring retract, treating duplicate request IDs as idempotency keys, applying a global conflict flag rather than per-component, and writing tests that mirror the same bug. Ask the candidate for one independently hand-calculated contradiction and sign reversal.

## Recommended 60-minute prioritization

0–8 minutes: inspect fixtures, note corrections, signs, tenants and contradictions. 8–15: articulate the invariant and choose weighted connectivity or a one-time traversal. 15–35: implement preparation and three status types, test chains and reversal. 35–47: handle contradictions, self-loops, bad versus disconnected groups and retractions. 47–55: validate unusual inputs and ordering; estimate memory/latency. 55–60: explain complexity, AI usage and failure modes. Credit a well-scoped correct partial solution over a falsely claimed complete system.

## Walkthrough inspection

Have the candidate compute a reversed offset manually, show how a nonzero self-loop affects its whole connected group, explain how a higher-revision retract changes the active snapshot, and state both preprocessing and typical query complexity. Probe what happens when two groups are joined after one is already inconsistent, why a graph's chosen reference time does not affect answers, and which AI-generated code they reviewed most closely.
