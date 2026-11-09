# POST-PRACTICE ONLY — VaultScope Interviewer Notes

**Do not disclose before the candidate finishes.** This is an evaluator guide, not code to be copied into the candidate branch.

## Underlying structure

This is an effective-access query on a **time-filtered directed membership graph**. Each live membership points from its member (user or group) to the containing group; group-to-group edges may cycle. Version rows must first be reduced by ID to their highest revision, with duplicate-conflict validation occurring across **all** revisions (including superseded records). Policies are versioned similarly. The requested explanatory witness is the minimal-hop active reachability path, with deterministic lexicographic group-sequence tie breaking. Denial takes precedence over allow regardless of witness path length.

## Strong solution directions and complexity

A credible baseline first validates and normalizes snapshots in O(N) expected dictionary time and space, then builds adjacency lists keyed by `(member_type,member_id)` and policies keyed by `(resource,action)` and possibly `(subject_type,subject_id)`. For a query at time t, traverse active outgoing membership edges, preserving the best `(hop_count,group_tuple)` for each reachable group. A breadth-first exploration with sorted adjacency or priority ordering can produce shortest/lexical paths; an explicit priority queue keyed by `(hops,path_tuple)` is simpler to reason about but stores more path data. Direct user policies are considered at zero hops. Collect active policies targeting the user or reachable groups, pick effect `deny` if present else `allow`, then minimize `(path_length,policy_id,path_tuple)`. Return the full path for group policies.

Snapshot validation is O(N+E+P) expected. A straightforward per-query traversal is O(V_t+E_t+P_candidate) plus sorting or priority-queue overhead, O(V_t) reachability memory plus explanation path storage. For small fixtures this is fine but not enough for 400k production queries. Strong scale discussion covers filtering policies by resource/action early, interval checks, caching repeated `(user,time)` safely only when active-edge sets are unchanged, precomputed equivalence intervals or offline processing sorted by relevant change boundaries, and practical memory profiling. Avoid blanket transitive-closure materialization (`O(G^2)` worst case) and treating strongly connected components as permanently connected when edges expire. Precomputation might be viable for highly stable static slices, but the interviewer should ask how timestamps and revocations invalidate it. An LLM may help interpret unexpected data, but should not substitute for a correctness-proof or hallucinate membership paths.

## Why naive approaches fail

Direct-only lookups ignore nested teams. Treating group membership as an undirected relation grants access backward from parent to child. A DFS without a visited/best-path map loops on cycles. A global visited set created before testing path length may freeze a longer witness and produce incorrect tie-breaking; likewise, the first policy found is not necessarily authoritative. Ignoring the latest revision resurrects deleted policies. Sorting by policy ID before deny dominance can grant access incorrectly. Applying policy time but not membership time (or vice versa) yields fabricated access. Recomputing all graph paths for every resource query is expensive. Cache keys consisting only of user ID (or user+day) are unsound for arbitrary millisecond boundaries.

## Subtle traps / hidden checks

1. `alice` has a direct allow on `handbook`, while nested `reviewers` becomes a deny exactly at t=300: deny wins, with nonempty group path. At t=700 the denial expires.
2. `ops -> staff -> reviewers -> ops` forms a real active cycle, with an additional shorter `ops -> reviewers` edge. Choose shortest rather than enumerating cycles.
3. `bob` has a revised membership `m16` ending at t=90 rather than t=120; t=90 must exclude that membership.
4. `carol` has a revised direct deny on `quarterly` active only `[200,250)`; at t=250 the denial must disappear but group-based allow may remain.
5. `p08` is deleted at higher revision; it must not grant any `roadmap` edit. `p09` direct allow can still apply to alice, except where `p10` active denial wins.
6. `m11` is deleted and must not give `faye` finance access. A later `delete` without an earlier upsert should also be tolerated if introduced in a hidden fixture.
7. Two equal-length paths to the same policy group should pick lexicographically smaller **sequence of full group IDs**, not whichever row appeared first.
8. A group policy for `export` never provides `view`; action is exact.
9. Inactive edges cannot be used as a bridge even when the endpoints are active independently. Time `until` is exclusive, `from` inclusive.
10. Valid duplicate query IDs each receive their own line. Invalid `at_ms:true`, zero-length intervals, contradictory same `(ID,revision)`, cross-tenant snapshot relationships, and malformed JSON require correct scope of failure.
11. Direct user-policy witness path is empty even if the user also belongs to several groups.
12. All catalog revision rows must be structurally and referentially validated, including superseded upserts. Deleting an ID with absent previous version is allowed.

## Alternative defensible designs

A per-user group expansion may be cached at fixed non-overlapping time spans determined by incident membership boundaries; invalidating a cache solely on a group policy revision is unnecessary if group reachability is cached independently, but effective-decision cache must account for policies as well. For offline sorted queries, active edges can be processed by time with a dynamic graph, though deletion/recomputation of connectivity with directed paths is difficult. A bounded batch algorithm grouping queries by tenant/user/timestamp region and reusing traversal may be useful. For extreme dense graphs, cap analysis with honest complexity rather than claiming constant-time reachability. Exact algorithms remain preferable to heuristic/LLM decisions given the strict contract; hybrids for data triage are defensible if every final decision is verified.

## AI-agent failure modes

Common errors: equating group->group membership direction with parent->child; checking only one policy; applying a direct allow after discovering a deny; using recursive traversal without guarding cycles; forgetting that `type(True) is int` is false for request times; trusting fixture outputs returned by the unfinished starter; hardcoding fixture labels; emitting `via` as one group instead of the full chain; caching stale paths across times; hidden tests inadvertently copied into candidate history; and skipping the requested run commands.

## What the candidate should discover, and when

The fixture contains actual cycles and competing direct and inherited rules, plus non-monotonic revision changes, timestamp boundary opportunities, and two tenants. Recommended 60-minute flow: 0–8 minutes inspect schema, parser and cases; 8–17 minutes articulate semantics, indexes and graph/path approach; 17–40 minutes implement vertical end-to-end decisions and proof path; 40–51 minutes adversarial tests including deny, cycles, tie, revocation, time; 51–60 minutes measure/describe complexity, possible caching, run CLI and summarize known limitations.

## Walkthrough inspection points

Ask candidate to demonstrate one user/resource/action/time where inherited deny overrides direct allow, show which membership edges justify `via`, prove tie-breaking independent of CSV order, show handling of a cycle, inspect one deleted policy and revised membership, and describe what changes when queries reuse a user across close timestamps. Confirm stdout has one JSON object per physical request line and loader rejects invalid catalogs atomically. Explain any scale claims, especially memory growth when paths are materialized and time filters are dynamic.
