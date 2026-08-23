# RecoveryWave — Phased Implementation Plan

Target: implement recovery planning in `planner.py` so each incident in `fixtures/incidents.jsonl`
produces one deterministic JSON result, with a startup/query split that stays credible at
~200k services / ~1M dependency rows / 10k queries per process.

*Rev 3 after review: wave policy defaults to one-SCC-per-wave (§0.1); region filtering no longer
blocks traversal (§0.2); complexity and memory claims corrected (§0.4).*

---

## Core model (the one idea the whole solution rests on)

Dependency rows are stored **forward** — `checkout,pricing,hard` means *checkout depends on pricing*.
Recovery propagates **backward**: restarting `pricing` forces `checkout` to restart. So the primary
index is a **reverse adjacency map over `hard` edges only**: `depends_on -> {dependents}`.

That gives a clean two-phase shape: parse and index the static graph once at startup, then serve each
incident by touching only the part of the graph the incident reaches. No transitive closure, no
all-pairs work, no rescan of the 1M rows per query (README requirement 12).

---

## Phase 0 — Decisions to lock before coding

### 0.1 Wave emission: one SCC per wave

Requirement 9 says "when multiple valid waves could be emitted at the same point, choose by the
smallest `(tier, service_id)`". Two readings were on the table:

| Reading | `inc-identity` waves | Cost |
|---|---|---|
| **A — maximal layer** (all eligible per wave) | `[identity] [checkout,fraud,profile] [orders] [analytics,payments]` | tier is unobservable; req 9 vestigial |
| **B — one SCC per wave**, chosen by min `(tier, service_id)` | `[identity] [checkout] [fraud] [orders] [payments] [profile] [analytics]` | req 8 only bites on multi-member SCCs |

**Decision: B is the default.** The deciding test is *which reading leaves no requirement dead* — and
that is B:

- Req 6 says unorderable services share a wave *"because of their dependency relationships"*. Under B
  that clause is precisely SCC membership. Under A, `checkout`/`fraud`/`profile` share a wave while
  having no dependency relationship with one another, which req 6 does not describe.
- Req 9's "multiple valid waves ... at the same point" only has a referent if waves are *selected*.
  Under A the partition is forced and nothing is chosen.
- Under A, tier appears in no other requirement, so nothing in the spec can observe it.

A is kept behind a `wave_policy` seam (same `(tier, service_id)` heap drives both) so the choice is one
argument wide if the interviewer confirms maximal layering.

Under B, tier is observable **on the fixture itself**: `profile` (tier 2) is eligible from wave 2 but
emitted at wave 6, behind three tier-1 services. That is the req-9 compliance demonstration.

### 0.2 Region filtering selects output, it does not block traversal

Req 3 says an out-of-region service "must not appear"; req 2 says include everything transitively
affected through hard edges. *Must not appear* is a constraint on the result, not on reachability — an
excluded service still transmits the need to restart. So: **propagate over the full hard graph, then
retain only in-region services** for output and ordering.

On `east-a → west-b → east-c` with `failed=[east-c]`, `region=us-east`, this yields `{east-c, east-a}`
with `west-b` filtered out. (The earlier plan blocked traversal at `west-b` and wrongly dropped
`east-a`.) The fixture cannot distinguish the readings — `inc-shipping-west` is entirely us-west —
so this is pinned by a synthetic test.

Consequence to state in the walkthrough: filtering after condensation means an SCC straddling a region
boundary is *split*, and its retained members may become orderable relative to one another. SCCs are
therefore computed on the retained subgraph, not before filtering.

### 0.3 Smaller calls

- **`ignored_dependency_rows`** counted once at index build, echoed on every incident result.
- Endpoint validity is checked **before** the `kind` filter, so a malformed `soft` row still counts.
- **`unknown_services`**: incident IDs absent from `services.csv`, sorted, de-duplicated, always
  present. Region-excluded services are *not* "unknown".
- Out-of-region **failed seeds still seed propagation** (they are filtered from output like any other
  node) — the direct consequence of §0.2.

### 0.4 Honest cost claims

Earlier drafts claimed `O(V' + E')` per query and "peak memory equals steady state". Both were wrong.

**Per query**, with `R` = nodes reached by propagation, `V'` = retained in-region nodes, `C` = SCC count:

```
O( Σ revdeg(v) for v in R      # propagation scans full reverse degree, incl. edges later filtered
 + Σ depdeg(u) for u in V'     # localisation scans full forward degree, incl. edges leaving the set
 + V' log V' + C log C )       # sorting and heap
```

The degree terms are bounded by the *fleet-wide* degree of touched nodes, not by result size — a
10-service result that brushes one 500k-dependent hub is expensive. This is the main threat to the
100 ms p95 target and is what Phase 6 must actually measure.

**Startup** is `O(V + E log Δ)` (Δ = max degree), from the per-node sort in the dedupe pass.

**Memory peak** = steady state + transient build arrays (degree counters, fill cursors, rebuilt
offsets) ≈ 6 × V ints ≈ 5 MB at V=200k, plus one sort temp bounded by Δ. Small, but *measured*, not
asserted — Phase 6 records construction peak RSS separately from steady state.

---

## Phase 1 — Static index (memory-first)

`RecoveryPlanner.from_paths(services_csv, dependencies_csv)` is the production constructor;
`from_loaded(...)` serves small inputs and the back-compat `plan_recovery` wrapper. Both funnel into
one build. `load_services` / `load_dependencies` in `planner.py` stay untouched — `test_baseline.py`
pins them.

**Never materialise 1M `Dependency` objects or a 1M-element dedupe set.** Four passes:
services → degree count → fill → sort-and-compact in place. Result is CSR (`array("i")` offsets +
targets) in both directions over interned integer IDs: ~4 MB per 1M edges per direction versus
hundreds of MB for dict-of-tuples-of-strings.

Duplicate `service_id` rows **overwrite the existing slot** rather than appending a new vertex — an
append would leave an unreachable ghost vertex that `from_loaded` (which receives an already-deduped
dict) could never reproduce.

## Phase 2 — Affected set

Iterative reverse BFS over the full hard graph from the known failed services, `visited` as a `set` so
per-query cost tracks the incident rather than the fleet. Region retention is applied *after*
traversal (§0.2), as a single predicate so the interpretation has one flip site.

## Phase 3 — Wave ordering

On the induced subgraph of the **retained** set: iterative Tarjan SCC (recursion limit rules out the
recursive form), then layered Kahn over the condensation driven by a heap keyed on each component's
minimum `(tier, service_id)`. Emission follows `wave_policy` (§0.1). Component keys are globally
unique — components are disjoint and service IDs unique — so no tie-break is ever needed and no
iteration order can reach the output.

Self-edges and parallel condensation edges need no special case; the general machinery absorbs both.

## Phase 4 — Output + CLI

Per incident: `{incident_id, waves, service_count, unknown_services, ignored_dependency_rows}`.
`main()` builds the planner **once** and streams incidents through it. Diagnostics → stderr.

## Phase 5 — Adversarial + golden tests

Per-phase tests plus: the cross-region test pinning §0.2; the tier tests pinning §0.1 (mutating a tier
must reorder output under B, and must *not* under A); and golden outputs for all four fixtures.
`inc-identity` under B is `[[identity],[checkout],[fraud],[orders],[payments],[profile],[analytics]]`,
`service_count = 7` (`notifications` excluded — soft edge only).

## Phase 6 — Scale validation

Synthetic ~200k services / ~1M edges with realistic fan-out **including at least one pathological hub**,
since §0.4 identifies hub degree as the real latency risk. Measure construction wall time, construction
peak RSS, steady-state RSS, and p95 over ~1k incidents sized 10–5,000. Targets: p95 < 100 ms
post-startup, < 512 MB.

Levers if measurements disagree: skip Tarjan when the retained subgraph is acyclic and fall back only
on the residue; reuse preallocated scratch across queries; cache by `(frozenset(seeds), region)`.

---

## Notes for the walkthrough

- **Ordering & loop semantics:** SCC condensation satisfies both "cycles must still produce a finite
  plan" and "unorderable services share a wave" — they are the same statement.
- **The req-8/req-9 tension** and how it was resolved (§0.1) is the most interesting thing to raise:
  the choice was made by asking which reading leaves no requirement vestigial, not by preference.
- **Region semantics** (§0.2) is the other judgement call — and the one where "must not appear" is
  easily over-read into "does not propagate".
- **Cost:** per-query cost tracks *degrees touched*, not result size (§0.4). That is the honest
  scaling story and the thing to measure rather than assert.
- **LLM component:** not used. Exactly specified, fully verifiable, deterministic output under a 100 ms
  budget — a model call adds nondeterminism and latency with no headroom for either. The honest place
  for a heuristic is *ranking* waves for operators (blast radius, tier-weighted risk), a different and
  softer question than this spec asks.
