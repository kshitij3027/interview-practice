# Iteration 1 — Detailed Implementation Plan (Phases 0–3)

Scope: everything up to and including a working, tested `RecoveryPlanner.plan()`.
CLI wiring (Phase 4), golden fixtures (Phase 5), and scale validation (Phase 6) are out of scope here.

Companion to `plan.md`. Where the two disagree, this file is the more current.

**Rev 2 — changes from review.** D1 default flipped to one-SCC-per-wave; D2 no longer blocks
traversal; complexity restated honestly (§0.4); "peak = steady state" retracted (§1.2); duplicate
`service_id` now overwrites its slot (§1.1); `from_loaded` input contract made explicit (§1.3).

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
`recovery.py`). It never references the `Service` / `Dependency` classes by name — see the duck-typed
protocols in §1.3.

### 0.2 Decision log

| # | Decision | Rationale / risk |
|---|---|---|
| **D1** | `wave_policy="single_component"` is the **default**: one SCC per wave, chosen by min `(tier, service_id)`. `"maximal"` implemented behind the same seam. | §0.5. Chosen because it is the only reading under which no requirement is vestigial. |
| **D2** | Propagation traverses the **full** hard graph; region retention is applied to the *result*, not to traversal | §0.6. "Must not appear" constrains output, not reachability. |
| **D3** | `ignored_dependency_rows` counted once at build, echoed on every incident result | README says "top-level" but output is per-incident |
| **D4** | Endpoint validity checked **before** the `kind` filter — a malformed `soft` row still counts as ignored | Req 11 says "rows whose endpoints are unknown", unqualified by kind |
| **D5** | `kind` values other than `hard`/`soft` are non-forcing (treated like `soft`) and **not** counted as ignored | Unspecified; conservative — only `hard` forces restarts |
| **D6** | `unknown_services` sorted and de-duplicated; region-excluded services are **not** unknown | Determinism; "unknown" means absent from `services.csv` |
| **D7** | An incident naming a region absent from `services.csv` yields `waves: []`, `service_count: 0` | Falls out of D2: everything is filtered at retention |
| **D8** | Self-edges retained; parallel condensation edges **not** deduped | Both absorbed by the general machinery (§3.2, §3.3) |
| **D9** | Out-of-region **failed seeds still seed propagation**, then get filtered like any other node | Direct consequence of D2; the alternative silently re-introduces the traversal block |
| **D10** | Duplicate `service_id` rows **overwrite the existing slot** (id, tier, region), never append a vertex | Appending leaves an unreachable ghost vertex that `from_loaded` cannot reproduce (§1.1) |

### 0.3 The determinism argument (what we must be able to prove)

Req 9 forbids relying on CSV/dict iteration order. Service indices are assigned in `services.csv`
order, so index order *is* file order — we must show it never reaches the output:

1. **BFS** produces a `set`; traversal order cannot affect membership.
2. **Tarjan** discovery order affects component *numbering* but not component *membership*.
3. **Kahn** pops by `(tier, service_id)` heap key, never by component number.
4. Each component's key is `min((tier, service_id))` over its members. Components are disjoint and
   service IDs unique ⇒ **keys are globally unique ⇒ no tie-break is ever needed.**
5. Within a wave, output is sorted lexicographically (req 8).

Test `test_shuffled_input_rows_produce_identical_output` (§3.6) is the empirical check.

### 0.4 Cost model (corrected)

The `O(V' + E')` claim in rev 1 was wrong in two independent ways. Accurate per-query bound, with
`R` = nodes reached by propagation, `V'` = retained in-region nodes, `C` = SCC count:

```
O( Σ revdeg(v) for v in R       # propagation reads the full reverse degree of every reached node,
                                #   including edges to nodes that retention later discards
 + Σ depdeg(u) for u in V'      # localisation reads the full forward degree of every retained node,
                                #   including edges leaving the affected set
 + V' log V'                    # sorted(affected) + per-wave sorting
 + C log C )                    # heap operations
```

**The degree terms are not bounded by result size.** A 10-service result that touches one
500k-dependent hub costs 500k edge reads. This is the real threat to the 100 ms p95 target, and it is
why Phase 6's generator must include a pathological hub rather than uniform fan-out.

Startup is `O(V + E log Δ)` (Δ = max degree) — the `log Δ` from the per-node sort in Pass D.

### 0.5 D1 in full: why one SCC per wave

| Reading | `inc-identity` | Which requirement goes dead |
|---|---|---|
| **A — maximal layer** | `[identity] [checkout,fraud,profile] [orders] [analytics,payments]` | req 9 — tier is unobservable anywhere in the spec |
| **B — one SCC per wave** *(chosen)* | `[identity] [checkout] [fraud] [orders] [payments] [profile] [analytics]` | req 8 still applies, but only to multi-member SCCs |

Three signals favour B:

1. **Req 6** says unorderable services share a wave *"because of their dependency relationships"*.
   Under B that clause is exactly SCC membership. Under A, `checkout`/`fraud`/`profile` share a wave
   while having no dependency relationship with each other — a case req 6 does not describe.
2. **Req 9's** "multiple valid waves could be emitted at the same point" needs waves to be *selected*.
   Under A the partition is forced; nothing is chosen.
3. Under A, **tier appears in no other requirement**, so no observable behaviour depends on it.

The deciding principle: prefer the reading under which no requirement is vestigial.

Under B, tier is observable **on the fixture itself** — `profile` (tier 2) is eligible from wave 2 but
emitted at wave 6, behind three tier-1 services. That is the req-9 compliance demonstration, and it
does not need a synthetic graph.

### 0.6 D2 in full: region selects output, not reachability

Req 3 ("must not appear") constrains the result; req 2 ("include all services transitively affected")
constrains membership. Rev 1 derived a *traversal* rule from an *output* rule — an excluded service is
still restarted in reality, and still transmits the need to restart to its dependents.

On `east-a → west-b → east-c`, `failed=[east-c]`, `region=us-east`:

- **D2 (chosen):** traverse fully, retain in-region ⇒ `{east-c, east-a}`, `west-b` filtered.
- **Rev 1 (wrong):** stop at `west-b` ⇒ `{east-c}`, silently losing an affected service.

Two consequences to implement deliberately:

- **Retention happens before SCC computation, not after.** An SCC straddling a region boundary is
  split by retention, and its retained members may then be orderable relative to one another. So Tarjan
  runs on the *retained* induced subgraph (§3.1).
- **D9:** out-of-region seeds still seed propagation. Filtering them at seed time would re-create the
  traversal block through the back door.

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

Rows with an empty `service_id` are skipped (matching the given `load_services`).

**Duplicate `service_id` (D10).** `load_services` is last-wins on a dict, so `from_paths` must be
last-wins on the *same vertex*:

```python
i = index.get(sid)
if i is None:
    i = len(ids); index[sid] = i; ids.append(sid); tier.append(...); region_of.append(...)
else:
    tier[i] = ...; region_of[i] = ...          # overwrite in place — do NOT append a second vertex
```

Appending would leave the old index as an unreachable ghost vertex: `V` would differ between the two
constructors, CSR arrays would be sized differently, and `test_from_paths_matches_from_loaded` would
fail — because `from_loaded` receives an already-deduplicated dict and cannot reproduce a ghost. The
README declares IDs unique, so this is not a valid-input bug, but the compatibility claim is only true
with the overwrite.

### 1.2 `Csr` — compressed sparse row adjacency

```python
class Csr:
    offsets: array("i")   # length V+1
    targets: array("i")   # length E
    def neighbours(self, u: int) -> memoryview:   # targets[offsets[u]:offsets[u+1]]
```

- **`deps`** — `u -> v` for "u depends on v". Drives ordering (in-degree = in-plan hard deps).
- **`dependents`** — `v -> u`. Drives BFS propagation.

**Steady state** at production shape: `targets` 1M × 4 B = 4 MB each, `offsets` 200k × 4 B = 0.8 MB
each, `ids` ≈ 15 MB, `index` ≈ 18 MB.

**Peak is higher than steady state** — rev 1 claimed otherwise, wrongly. Construction additionally
holds degree arrays (2×V), fill cursors (2×V), and rebuilt offsets (2×V) ≈ 6 × 200k × 4 B ≈ 5 MB, plus
one `sorted()` temp bounded by Δ. Comfortable inside 512 MB, but Phase 6 **measures construction peak
RSS separately** rather than trusting this arithmetic. Cheap mitigation: reuse the degree arrays
in place as the offsets arrays after prefix-summing.

`array("i")` itemsize is not formally guaranteed ≥ 4 bytes; assert it at import and fall back to `"l"`.

### 1.3 Build — one code path, two sources (contract made explicit)

Rev 1 contradicted itself here. Three distinct contracts:

```python
# INTERNAL: what the build consumes. Plain tuples, no attributes.
RowSource = Callable[[], Iterator[tuple[str, str, str]]]      # () -> iter of (service_id, depends_on, kind)
SvcSource = Callable[[], Iterator[tuple[str, int, str]]]      # () -> iter of (service_id, tier, region)

# PUBLIC: from_paths streams CSV and adapts to the internal tuple protocol.
@classmethod
def from_paths(cls, services_path, dependencies_path) -> "RecoveryPlanner"

# PUBLIC: from_loaded takes duck-typed objects and adapts them to the same tuples.
#   services:     Mapping[str, S]  where S has .tier (int) and .region (str)
#   dependencies: Iterable[D]      where D has .service_id, .depends_on, .kind (all str)
# planner.Service / planner.Dependency satisfy these without recovery.py importing them.
@classmethod
def from_loaded(cls, services, dependencies) -> "RecoveryPlanner"
```

A *factory* rather than an iterator, because rows are traversed twice: `from_paths` re-opens the CSV
(cheap sequential I/O), `from_loaded` re-iterates the in-memory sequence. Hence `dependencies` must be
re-iterable — a `Sequence`, not a generator. Assert that.

### 1.4 Build passes

**Pass A — services.** Populate `ServiceTable` with the D10 overwrite rule.

**Pass B — degrees.** Stream rows:

```
u = index.get(service_id); v = index.get(depends_on)
if u is None or v is None:  ignored_dependency_rows += 1;  continue   # D4: before kind check
if kind != "hard":          continue                                   # D5
deps_deg[u] += 1;  dependents_deg[v] += 1
```

Prefix-sum into `offsets`. Duplicates are counted here, so offsets are a **safe upper bound** — exact
sizing is unnecessary because Pass D compacts.

**Pass C — fill.** Re-stream with identical filtering, counting disabled. Scatter via
`cursor = offsets[:-1]` copies.

**Pass D — sort + compact in place.** The invariant `w <= offsets[u]` holds throughout (compaction
only shrinks), so writing into the same array is safe:

```python
w = 0
for u in range(V):
    lo, hi = offsets[u], offsets[u + 1]
    new_offsets[u] = w
    prev = -1
    for t in sorted(targets[lo:hi]):      # temp bounded by max degree Δ
        if t != prev:
            targets[w] = t; w += 1; prev = t
new_offsets[V] = w
del targets[w:]
```

Collapses the duplicate `checkout,pricing,hard` with no auxiliary set, and leaves every slice sorted.

### 1.5 Phase 1 tests

| Test | Asserts |
|---|---|
| `test_duplicate_edge_collapsed` | `checkout,pricing` appears once in `deps.neighbours(checkout)` |
| `test_soft_edges_absent_both_directions` | `orders`→`notifications` and `catalog`→`analytics` absent |
| `test_malformed_rows_counted_once` | fixture yields `ignored_dependency_rows == 2` |
| `test_malformed_soft_row_counted` | D4 — soft row with unknown endpoint increments the counter |
| `test_unknown_kind_not_counted_not_forcing` | D5 — `a,b,weak` neither counted nor traversed |
| `test_csr_offsets_consistent_after_compaction` | `offsets[0]==0`, monotonic, `offsets[V]==len(targets)`, slices strictly increasing |
| `test_csr_directions_are_transposes` | edge multiset of `deps` == reversed multiset of `dependents` |
| `test_from_paths_matches_from_loaded` | identical `ids`, `tier`, `region_of`, and both CSRs on the fixture |
| `test_duplicate_service_id_overwrites_slot` | D10 — two rows for `a` ⇒ `V` unchanged, tier is the later value, no ghost vertex |
| `test_self_edge_retained` | `search` ∈ `deps.neighbours(search)` (D8) |

---

## 2. Phase 2 — Affected set

### 2.1 Signature

```python
def _affected(self, failed: Sequence[str], region: str | None)
        -> tuple[set[int], list[str]]:     # (retained indices, sorted unknown service ids)
```

### 2.2 Seeding (D9)

```
unknown = set(); seeds = []
for sid in failed:
    i = index.get(sid)
    if i is None: unknown.add(sid)          # D6
    else:         seeds.append(i)           # region NOT applied here — D9
```

No early return for an unknown region: retention (§2.4) discards everything and D7 falls out with no
special case.

### 2.3 Traversal — full graph, no region predicate

```python
visited = set(seeds)
stack = list(seeds)
while stack:
    v = stack.pop()
    for u in self.dependents.neighbours(v):       # u depends on v ⇒ u must restart too
        if u not in visited:
            visited.add(u); stack.append(u)
```

`visited` is a **`set[int]`, not `bytearray(V)`** — per-query cost must not carry an `O(V)` term at 10k
queries. Explicitly iterative: a 200k-deep chain exceeds the 1000-frame recursion limit. Cycles
terminate because membership is monotone.

### 2.4 Retention

```python
if region is None:
    return visited, sorted(unknown)
ord_ = self.table.region_ids.get(region)
if ord_ is None:
    return set(), sorted(unknown)                          # D7
return {i for i in visited if self.table.region_of[i] == ord_}, sorted(unknown)
```

One predicate, one call site: flipping D2 back to the traversal-blocking reading means moving this test
into §2.3's loop and applying it at seed time. Keep them adjacent in the source and cross-reference.

### 2.5 Phase 2 tests

| Test | Asserts |
|---|---|
| `test_affected_identity` | `{identity, profile, checkout, fraud, orders, payments, analytics}` — 7 nodes |
| `test_soft_dependent_excluded` | `notifications` ∉ affected for `inc-identity` |
| `test_region_scoped_incident` | `inc-shipping-west` ⊆ us-west services |
| `test_unknown_services_reported` | `inc-mixed` → `["does-not-exist"]`, planning continues |
| `test_duplicate_seeds_idempotent` | `["identity","identity"]` == `["identity"]` |
| `test_cycle_terminates` | `legacy-sync` ⇒ `{legacy-sync, partner-feed}` |
| `test_empty_failed_services` | empty set, no exception |
| `test_all_unknown_incident` | empty set, all IDs reported unknown |
| `test_unknown_region` | D7 — empty set |
| `test_out_of_region_seed_still_propagates` | D9 — seed in us-west, region us-east ⇒ its in-region dependents appear, seed does not |

### 2.6 The region-semantics test (pins D2)

Synthetic, via `from_loaded` — the fixture has no cross-region path:

```
services: east-a (us-east), west-b (us-west), east-c (us-east)
deps:     east-a -> west-b (hard),  west-b -> east-c (hard)
incident: failed=[east-c], region="us-east"
```

- **D2 (chosen):** `{east-c, east-a}` — `west-b` filtered from output but still transmits.
- **Alternative (traversal block):** `{east-c}`.

The test asserts D2 and carries a comment naming the alternative, so the assumption is documented where
it is enforced.

---

## 3. Phase 3 — Wave ordering

### 3.1 Localisation (on the *retained* set — see §0.6)

```python
nodes = sorted(retained)                     # deterministic local order
local = {g: i for i, g in enumerate(nodes)}
adj = [[] for _ in range(n)]                 # induced "depends on" edges, local
for i, g in enumerate(nodes):
    for t in self.deps.neighbours(g):
        j = local.get(t)
        if j is not None:                    # both endpoints retained
            adj[i].append(j)
```

Every subsequent array is size `n`, never `V`. Note the honest cost (§0.4): this loop reads the *full*
forward degree of each retained node, including the edges it then discards — `checkout`'s edges to the
unaffected `pricing` and `promotions` are read and dropped here, which is exactly what makes `checkout`
orderable despite depending on them.

Because retention already happened, an SCC straddling a region boundary is correctly split.

### 3.2 Iterative Tarjan SCC

Recursive Tarjan is disqualified by the recursion limit.

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
update reduces to `low[v] = min(low[v], idx[v])` — a no-op, and `search` becomes a singleton SCC.

### 3.3 Condensation

```python
key[c]      = min((tier[nodes[m]], ids[nodes[m]]) for m in sccs[c])   # globally unique (§0.3)
dag[cv]    -> cu      for every induced edge u->v with comp[u] != comp[v]
indegree[cu] += 1     # cu depends on cv ⇒ cv restarts first
```

Note the **direction flip**: an induced edge is "u depends on v"; the DAG edge is "v enables u".
Parallel DAG edges are kept (D8) — incremented twice, decremented twice, consistent by construction and
cheaper than a dedupe set.

### 3.4 Kahn with the policy seam (default: one SCC per wave)

```python
heap = [(*key[c], c) for c in range(len(sccs)) if indegree[c] == 0]
heapq.heapify(heap)
waves = []
while heap:
    batch_size = 1 if policy == "single_component" else len(heap)   # D1: single_component default
    batch = [heapq.heappop(heap)[-1] for _ in range(batch_size)]    # pop ALL first...
    for c in batch:                                                 # ...then relax
        for d in dag[c]:
            indegree[d] -= 1
            if indegree[d] == 0:
                heapq.heappush(heap, (*key[d], d))
    waves.append(sorted(ids[nodes[m]] for c in batch for m in sccs[c]))   # req 8
assert sum(len(w) for w in waves) == n      # condensation is a DAG; failure means a build bug
```

**The pop-then-relax split is load-bearing under `maximal`**: interleaving pops with pushes would let a
component that became eligible *during* the wave be popped *into* it, breaking req 7. Under
`single_component` the split is a no-op but costs nothing.

Under `single_component` the heap key *is* the selection rule, which is how req 9 is demonstrated.

### 3.5 Result assembly

```python
{"incident_id": ..., "waves": waves, "service_count": n,
 "unknown_services": unknown, "ignored_dependency_rows": self.ignored_dependency_rows}
```

`n == 0` ⇒ `waves: []`, `service_count: 0`.

### 3.6 Phase 3 tests

| Test | Asserts |
|---|---|
| `test_dependency_precedes_dependent` | for every induced hard edge `u->v`, both retained, different SCCs ⇒ `wave_of(v) < wave_of(u)`; checked across all four fixture incidents |
| `test_scc_members_share_a_wave` | `legacy-sync`/`partner-feed` and `shipping`/`routing` each share a wave |
| `test_self_loop_service_is_placed` | `search` appears exactly once when reachable |
| `test_wave_contents_sorted` | every wave equals its own `sorted()` |
| `test_service_count_matches_waves` | `service_count == sum(len(w))`, no service twice |
| `test_shuffled_input_rows_produce_identical_output` | seeded-RNG shuffles of both CSVs ⇒ byte-identical output (§0.3) |
| `test_tier_changes_wave_order` | **req 9 compliance** — on the fixture, `profile` (tier 2) lands at wave 6 behind three tier-1 services; raising its tier to 0 moves it to wave 2 |
| `test_maximal_policy_ignores_tier` | same graph under `maximal`: mutating tiers changes nothing, and co-eligible components land in one wave |
| `test_policies_agree_on_membership` | both policies emit the same service set respecting the same partial order — they differ only in wave granularity |
| `test_split_scc_across_regions` | an SCC straddling a boundary is split by retention and its retained members are ordered normally (§0.6) |

`test_tier_changes_wave_order` is the review's "changing tiers must affect output somewhere"
requirement, and under D1 it is satisfiable **on the real fixture** rather than a synthetic graph.

---

## 4. Build order and checkpoints

1. `ServiceTable` + `Csr`, `from_loaded` only → §1.5 minus `from_paths`. **Checkpoint: `python3 -m unittest -v` green, `test_baseline.py` untouched.**
2. Add `from_paths` streaming + Pass D compaction → full §1.5, including D10.
3. `_affected` + retention → §2.5, §2.6.
4. Tarjan + condensation + Kahn + `plan()` → §3.6.
5. `plan_recovery()` back-compat wrapper (`from_loaded(...).plan(incident)`).

**Definition of done:** `RecoveryPlanner.from_paths(...).plan(incident)` returns a correct result dict
for all four fixture incidents, every test above passes, `test_baseline.py` unmodified and green.

## 5. Known risks carried into iteration 2

- **D1 remains the highest-stakes call.** If the reference implementation uses maximal layering,
  `inc-identity` changes; the other three fixture incidents happen to emit identical waves under
  both policies. The seam makes the flip one argument wide; ask before Phase 5.
- **D2 is still undecidable from the fixture** — §2.6 pins it, but a wrong guess stays invisible until
  a real cross-region incident appears.
- **Hub degree, not result size, governs latency** (§0.4). Phase 6's generator must include a
  pathological hub or it will measure the wrong thing and report a falsely comfortable p95.
- **Construction peak RSS is unverified arithmetic** (§1.2). Measure it; do not cite it.
- Pass D's `sorted(targets[lo:hi])` allocates a temp bounded by Δ — fine for realistic fan-out, worth
  re-checking against the hub case.
