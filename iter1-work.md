# Iteration 1 — Detailed Implementation Plan (Phases 0–3)

Scope: everything up to and including a working, tested `RecoveryPlanner.plan()`.
CLI wiring (Phase 4), golden fixtures (Phase 5), and scale validation (Phase 6) are out of scope here.

Companion to `plan.md`. Where the two disagree, this file is the more current.

---

## 0. Ground rules

### 0.1 File layout

| File | Role | Status |
|---|---|---|
| `planner.py` | CSV/JSONL parsing, argparse CLI, back-compat `plan_recovery` | given; **do not disturb** parsing or CLI signatures |
| `recovery.py` | **new** — `ServiceTable`, `Csr`, `RecoveryPlanner` | all of iteration 1 lands here |
| `test_baseline.py` | given baseline parse tests | must stay green, unmodified |
| `test_planner.py` | **new** — everything below | grows through phases 1–3 |

`recovery.py` imports nothing from `planner.py` (avoids a cycle, since `planner.py` will import
`recovery.py`). The `Service` / `Dependency` dataclasses are only needed by the `from_loaded` path,
which accepts plain tuples instead — see §1.3.

### 0.2 Decision log (locked before coding)

| # | Decision | Rationale / risk |
|---|---|---|
| **D1** | `wave_policy="maximal"` is the default; `"single_component"` implemented and tested | The req-8/req-9 conflict from `plan.md` §0.1. Flip cost is one argument. |
| **D2** | Region filtering defines an induced graph — BFS does not traverse out-of-region nodes | Undecidable from fixture; synthetic test pins it (§2.5) |
| **D3** | `ignored_dependency_rows` counted once at build, echoed on every incident result | README says "top-level" but output is per-incident |
| **D4** | Endpoint validity is checked **before** the `kind` filter — a malformed `soft` row still counts as ignored | Req 11 says "rows whose endpoints are unknown", unqualified by kind. Cheap to flip; note in walkthrough. |
| **D5** | `kind` values other than `hard`/`soft` are treated as non-forcing (like `soft`) and **not** counted as ignored | Unspecified; conservative — only `hard` forces restarts |
| **D6** | `unknown_services` is sorted and de-duplicated; region-excluded services are **not** unknown | Determinism; "unknown" means absent from `services.csv` |
| **D7** | An incident naming a region absent from `services.csv` yields `waves: []`, `service_count: 0` | Falls out of D2 naturally; no special case |
| **D8** | Self-edges are retained; parallel edges in the condensation are **not** deduped | Both are absorbed by the general machinery — see §3.3, §3.4 |

### 0.3 The determinism argument (what we must be able to prove)

Req 9 forbids relying on CSV/dict iteration order. Service indices are assigned in `services.csv` order,
so index order *is* file order — we must show it never reaches the output:

1. **BFS** produces a `set`; traversal order cannot affect membership.
2. **Tarjan** discovery order affects component *numbering* but not component *membership*.
3. **Kahn** pops by `(tier, service_id)` heap key, never by component number.
4. Each component's key is `min((tier, service_id))` over its members. Components are disjoint and
   service IDs unique ⇒ **keys are globally unique ⇒ no tie-break is ever needed.**
5. Within a wave, output is sorted lexicographically (req 8).

Test `test_shuffled_input_rows_produce_identical_output` (§3.6) is the empirical check on this.

---

## 1. Phase 1 — Static index

### 1.1 `ServiceTable`

```python
class ServiceTable:
    ids: list[str]              # idx -> service_id, in services.csv order
    index: dict[str, int]       # service_id -> idx
    tier: array("i")            # idx -> tier
    region_of: array("i")       # idx -> region ordinal
    region_ids: dict[str, int]  # region name -> ordinal
```

Built by streaming `services.csv`; rows with an empty `service_id` are skipped (matching the given
`load_services`). A repeated `service_id` overwrites, also matching `load_services` (last wins) — keep
the two paths behaviourally identical so tests can cross-check them.

### 1.2 `Csr` — compressed sparse row adjacency

```python
class Csr:
    offsets: array("i")   # length V+1
    targets: array("i")   # length E
    def neighbours(self, u: int) -> memoryview:   # targets[offsets[u]:offsets[u+1]]
```

Two instances per planner:

- **`deps`** — `u -> v` for "u depends on v". Drives ordering (in-degree = in-plan hard deps).
- **`dependents`** — `v -> u`. Drives BFS propagation.

Budget check at production shape: `targets` 1M × 4 B = 4 MB each, `offsets` 200k × 4 B = 0.8 MB each,
`ids` ≈ 15 MB, `index` ≈ 18 MB. Total well inside 512 MB, and — critically — **peak equals steady
state**, because no intermediate edge list or dedupe set is ever allocated.

### 1.3 Build — one code path, two sources

Both constructors funnel into `_build`, which takes a *factory* (not an iterator) because the rows are
traversed twice:

```python
RowSource = Callable[[], Iterator[tuple[str, str, str]]]   # (service_id, depends_on, kind)

@classmethod
def from_paths(cls, services_path, dependencies_path) -> "RecoveryPlanner"
    # rows() re-opens and re-streams the CSV each call — cheap sequential I/O

@classmethod
def from_loaded(cls, services: dict[str, Any], dependencies: Sequence[Any]) -> "RecoveryPlanner"
    # rows() re-iterates the in-memory list; used by plan_recovery() and small tests
```

`from_loaded` accepts anything with `.service_id` / `.depends_on` / `.kind` and `.tier` / `.region`,
so `planner.Service` / `planner.Dependency` work without `recovery.py` importing them.

### 1.4 Build passes

**Pass A — services.** Populate `ServiceTable`.

**Pass B — degrees.** Stream rows; for each:

```
u = index.get(service_id); v = index.get(depends_on)
if u is None or v is None:  ignored_dependency_rows += 1;  continue   # D4: before kind check
if kind != "hard":          continue                                   # D5
deps_deg[u] += 1;  dependents_deg[v] += 1
```

Prefix-sum the degree arrays into `offsets`. Duplicates are counted here, so offsets are a **safe upper
bound** — exact sizing is not needed because Pass D compacts.

**Pass C — fill.** Re-stream with identical filtering (`ignored` is *not* re-counted — Pass C runs with
counting disabled). Scatter using a mutable `cursor = offsets[:-1].copy()`:

```
deps_targets[cursor_d[u]] = v; cursor_d[u] += 1
dependents_targets[cursor_r[v]] = u; cursor_r[v] += 1
```

**Pass D — sort + compact in place.** Per node: sort its slice, drop adjacent duplicates, write forward
with a global write cursor `w`. The invariant `w <= offsets[u]` always holds (compaction only shrinks),
so writing into the same array is safe. Truncate `targets` to `w` at the end and install new offsets.

```python
w = 0
for u in range(V):
    lo, hi = offsets[u], offsets[u + 1]
    new_offsets[u] = w
    prev = -1
    for t in sorted(targets[lo:hi]):      # temp list bounded by max degree
        if t != prev:
            targets[w] = t; w += 1; prev = t
new_offsets[V] = w
del targets[w:]
```

This collapses the duplicate `checkout,pricing,hard` with no auxiliary set, and leaves every adjacency
slice **sorted** — reused for cheap membership checks later.

### 1.5 Phase 1 tests (`test_planner.py`)

| Test | Asserts |
|---|---|
| `test_duplicate_edge_collapsed` | `checkout,pricing` appears once in `deps.neighbours(checkout)` |
| `test_soft_edges_absent_both_directions` | `orders`→`notifications` absent from `dependents`; `catalog`→`analytics` absent |
| `test_malformed_rows_counted_once` | fixture yields `ignored_dependency_rows == 2` (`ghost,identity` + `checkout,missing-service`) |
| `test_malformed_soft_row_counted` | D4 — a soft row with an unknown endpoint increments the counter |
| `test_unknown_kind_not_counted_not_forcing` | D5 — `a,b,weak` neither counted nor traversed |
| `test_csr_offsets_consistent_after_compaction` | `offsets[0]==0`, monotonic, `offsets[V]==len(targets)`, every slice sorted + strictly increasing |
| `test_csr_directions_are_transposes` | edge multiset of `deps` == reversed edge multiset of `dependents` |
| `test_from_paths_matches_from_loaded` | both constructors give identical CSRs on the fixture |
| `test_self_edge_retained` | `search` ∈ `deps.neighbours(search)` (D8) |

---

## 2. Phase 2 — Affected set

### 2.1 Signature

```python
def _affected(self, failed: Sequence[str], region: str | None)
        -> tuple[set[int], list[str]]:     # (affected indices, sorted unknown service ids)
```

### 2.2 Seeding

```
unknown = set()
seeds = []
region_ord = self.table.region_ids.get(region) if region is not None else None
if region is not None and region_ord is None:
    return set(), sorted(unknown_from(failed))     # D7: no service can match
for sid in failed:
    i = index.get(sid)
    if i is None:            unknown.add(sid)                    # D6
    elif in_region(i):       seeds.append(i)                     # else: silently excluded, not unknown
```

### 2.3 Traversal

Iterative stack, `visited` as a **`set[int]`, not a `bytearray(V)`** — per-query cost must be `O(V')`,
not `O(V)`. At 10k queries a V-sized allocation per query is 2×10⁹ byte-writes of pure overhead.

```python
visited = set(seeds)
stack = list(seeds)
while stack:
    v = stack.pop()
    for u in self.dependents.neighbours(v):       # u depends on v ⇒ u must restart too
        if u not in visited and in_region(u):     # D2: do not traverse through excluded nodes
            visited.add(u); stack.append(u)
```

Explicitly iterative: a 200k-deep chain would exceed the 1000-frame recursion limit. Duplicate seeds
and re-reachable nodes are absorbed by `visited`; cycles terminate because membership is monotone.

`in_region(i)` is `region_ord is None or region_of[i] == region_ord` — a single predicate, so flipping
D2 to the output-filter reading means changing this one call site.

### 2.4 Phase 2 tests

| Test | Asserts |
|---|---|
| `test_affected_identity` | `{identity, profile, checkout, fraud, orders, payments, analytics}` — 7 nodes |
| `test_soft_dependent_excluded` | `notifications` ∉ affected for `inc-identity` |
| `test_region_scoped_incident` | `inc-shipping-west` ⊆ us-west services only |
| `test_unknown_services_reported` | `inc-mixed` → `unknown == ["does-not-exist"]`, planning continues |
| `test_duplicate_seeds_idempotent` | `["identity","identity"]` == `["identity"]` |
| `test_cycle_terminates` | `legacy-sync` seed returns `{legacy-sync, partner-feed}` |
| `test_empty_failed_services` | empty set, no exception |
| `test_all_unknown_incident` | empty set, all IDs reported unknown |
| `test_unknown_region` | D7 — empty set |

### 2.5 The region-semantics test (pins D2)

Synthetic graph, built via `from_loaded` rather than the fixture (the fixture has no cross-region path):

```
services: east-a (us-east), west-b (us-west), east-c (us-east)
deps:     east-a -> west-b (hard),  west-b -> east-c (hard)
incident: failed=[east-c], region="us-east"
```

- **D2 (induced graph, chosen):** `west-b` is excluded, so propagation stops ⇒ `{east-c}`.
- **Alternative (output filter):** propagation reaches `east-a` through `west-b` ⇒ `{east-c, east-a}`.

The test asserts the D2 result and carries a comment naming the alternative, so the assumption is
documented at the point where it is enforced.

---

## 3. Phase 3 — Wave ordering

### 3.1 Localisation (why per-query cost stays `O(V' + E')`)

Before any graph work, remap the affected set to dense local indices `0..n-1`:

```python
nodes = sorted(affected)                     # stable, and makes local order index-order
local = {g: i for i, g in enumerate(nodes)}
adj = [[] for _ in range(n)]                 # induced "depends on" edges, local
for i, g in enumerate(nodes):
    for t in self.deps.neighbours(g):
        j = local.get(t)
        if j is not None:                    # induced subgraph: both endpoints affected
            adj[i].append(j)
```

Every subsequent array is size `n`, never `V`. This is what makes p95 track incident size (10–5,000)
rather than fleet size. Edges to unaffected nodes are dropped here — which is precisely why `checkout`
is orderable despite depending on the unaffected `pricing`.

### 3.2 Iterative Tarjan SCC

Recursive Tarjan is disqualified by the recursion limit. The explicit-stack form:

```python
idx = [-1] * n; low = [0] * n; comp = [-1] * n
on_stack = bytearray(n); sstack = []; sccs = []; counter = 0

for s in range(n):
    if idx[s] != -1: continue
    work = [(s, 0)]
    while work:
        v, pi = work[-1]
        if pi == 0:
            idx[v] = low[v] = counter; counter += 1
            sstack.append(v); on_stack[v] = 1
        descended = False
        for k in range(pi, len(adj[v])):
            w = adj[v][k]
            if idx[w] == -1:
                work[-1] = (v, k + 1); work.append((w, 0)); descended = True; break
            elif on_stack[w] and idx[w] < low[v]:
                low[v] = idx[w]
        if descended: continue
        work.pop()
        if work and low[v] < low[work[-1][0]]:
            low[work[-1][0]] = low[v]
        if low[v] == idx[v]:
            members = []
            while True:
                w = sstack.pop(); on_stack[w] = 0; comp[w] = len(sccs); members.append(w)
                if w == v: break
            sccs.append(members)
```

**Self-loops need no special case** (D8): for `w == v`, `idx[w] != -1` and `on_stack[w]` is set, so the
update is `low[v] = min(low[v], idx[v])` — a no-op. `search` becomes a singleton SCC, exactly right.

### 3.3 Condensation

```python
key[c]      = min((tier[nodes[m]], ids[nodes[m]]) for m in sccs[c])   # globally unique (§0.3)
dag[cv]    -> cu      for every induced edge u->v with comp[u] != comp[v]
indegree[cu] += 1     # cu depends on cv ⇒ cv restarts first
```

Note the **direction flip**: an induced edge is "u depends on v", the DAG edge is "v enables u".

Parallel DAG edges are kept, not deduped (D8): two induced edges collapsing to the same component pair
increment `indegree` twice and decrement it twice. Consistent by construction, and cheaper than a
dedupe set.

### 3.4 Layered Kahn with the policy seam

```python
heap = [(*key[c], c) for c in range(len(sccs)) if indegree[c] == 0]
heapq.heapify(heap)
waves = []
while heap:
    batch_size = len(heap) if policy == "maximal" else 1
    batch = [heapq.heappop(heap)[-1] for _ in range(batch_size)]   # pop ALL first...
    for c in batch:                                                # ...then relax
        for d in dag[c]:
            indegree[d] -= 1
            if indegree[d] == 0:
                heapq.heappush(heap, (*key[d], d))
    waves.append(sorted(ids[nodes[m]] for c in batch for m in sccs[c]))   # req 8
assert sum(len(w) for w in waves) == n      # condensation is a DAG; failure means a build bug
```

**The pop-then-relax split is load-bearing.** Interleaving pops with pushes would let a component that
became eligible *during* this wave be popped *into* this wave, breaking req 7.

Under `maximal` the heap order cannot change wave membership (all eligible components are drained), so
tier is unobservable — the known cost of D1. Under `single_component` the heap key is the entire
selection rule, which is how req 9 is demonstrated.

### 3.5 Result assembly

```python
{"incident_id": ..., "waves": waves, "service_count": n,
 "unknown_services": unknown, "ignored_dependency_rows": self.ignored_dependency_rows}
```

`n == 0` ⇒ `waves: []`, `service_count: 0`.

### 3.6 Phase 3 tests

| Test | Asserts |
|---|---|
| `test_dependency_precedes_dependent` | for every induced hard edge `u->v` with both in-plan and in different SCCs, `wave_of(v) < wave_of(u)` — checked over all four fixture incidents, not one hand-picked case |
| `test_scc_members_share_a_wave` | `legacy-sync` / `partner-feed` same wave; `shipping` / `routing` same wave |
| `test_self_loop_service_is_placed` | `search` appears exactly once when reachable |
| `test_wave_contents_sorted` | every wave equals its own `sorted()` |
| `test_service_count_matches_waves` | `service_count == sum(len(w))`, and no service appears twice |
| `test_shuffled_input_rows_produce_identical_output` | shuffle `dependencies` rows *and* `services` rows with a seeded RNG across N permutations; output byte-identical (the §0.3 check) |
| `test_maximal_policy_ignores_tier` | diamond graph, components eligible together; mutating tiers leaves output unchanged, and they land in **one** wave |
| `test_single_component_policy_follows_tier` | same graph: waves ordered by ascending `(tier, service_id)`, **and** mutating one tier reorders the output |
| `test_policies_agree_on_membership` | both policies emit the same service set with the same partial order — they differ only in wave granularity |

The last three are the review's "make tier observable somewhere" requirement, and deliberately pin the
two D1 readings against each other rather than leaving the distinction implicit.

---

## 4. Build order and checkpoints

1. `ServiceTable` + `Csr` skeleton, `from_loaded` only → §1.5 tests minus `from_paths`. **Checkpoint: `python3 -m unittest -v` green, `test_baseline.py` untouched.**
2. Add `from_paths` streaming + Pass D compaction → full §1.5.
3. `_affected` + region predicate → §2.4, §2.5.
4. Tarjan + condensation + Kahn + `plan()` → §3.6.
5. `plan_recovery()` back-compat wrapper (`from_loaded(...).plan(incident)`) so the given signature keeps working. Full CLI reuse of a single planner instance is Phase 4.

**Definition of done for iteration 1:** `RecoveryPlanner.from_paths(...).plan(incident)` returns a
correct result dict for all four fixture incidents, every test above passes, and `test_baseline.py` is
unmodified and green.

## 5. Known risks carried into iteration 2

- **D1 is a spec defect, not a preference.** If the reference implementation uses `single_component`,
  the four golden fixtures in Phase 5 all mismatch. Ask before Phase 5; the flip itself is one argument.
- **D2 is undecidable from the fixture.** Test pins it; a wrong guess is invisible until a cross-region
  incident appears.
- **`array("i")`** is platform-dependent (4 bytes everywhere in practice, but `itemsize` is not
  guaranteed). Assert `itemsize >= 4` at import; switch to `"l"` if it ever fails.
- Pass D's `sorted(targets[lo:hi])` allocates a temp list per node — bounded by max degree. A
  pathological hub (one service with 500k dependents) makes that temp large but not fatal; note it and
  move on unless Phase 6 measurements say otherwise.
