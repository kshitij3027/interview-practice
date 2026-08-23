# Phase 6 — Scale Validation: Detailed Plan

Scope: test the production-shape claims in `README.md` — ~200k services, ~1M dependency rows, 10k
incidents per process, **p95 < 100 ms for typical incidents**, **< 512 MB**.

Companion to `plan.md` §Phase 6, `iter1-work.md` §0.4, `iter2-work.md`. Decisions are `F1`–`F9`.

**Rev 2 after review.** The gate no longer exempts labelled classes (§1.1) — which changes the
expected outcome (§4); workload selection no longer conditions on measured output (§2.2); the lever
ordering is withdrawn pending phase timers (§5); memory methodology corrected (§3.3).

---

## 0. Reconnaissance findings

Before writing this plan I ran a throwaway probe in a scratchpad (not in the repo): a 200k-service /
996k-row dataset measured against the real planner. **These are preliminary indicators, not results** —
one machine, one generator, one seed, no warmup discipline, `tracemalloc` absent. They exist to aim the
plan. The harness below replaces them.

| Measurement | Probe value |
|---|---|
| Build (200k services, 996k rows) | 2.85 s |
| RSS high-water after build | 63 MB |
| RSS high-water after a 199k-service incident | **219 MB** |
| Dedupe / ignored | 996k rows → 969,862 unique hard edges; 1,000 ignored |
| p95 latency, results in 10–5,000 | 5.03 ms |
| p95 latency, unstratified random seeds | 350 ms |
| **Region-scoped hub, 1% region** | **74.5 ms for a 1,994-service result** |

### 0.1 Stratification changes the question — but must not be used to duck it

Unstratified random seeds gave p95 = 350 ms. That number is not about the planner: the p95 *result* was
104,229 services, twenty times outside the README's stated 10–5,000. Restricted to that band, p95 was
5.03 ms.

| result size | p50 | p95 | n |
|---|---:|---:|---:|
| < 10 | 0.01 ms | 2.17 ms | 178 |
| 10–99 | 0.07 ms | 1.13 ms | 159 |
| 100–999 | 0.57 ms | 3.15 ms | 125 |
| 1k–5k | 3.82 ms | 8.08 ms | 51 |
| 5k–50k | 32.08 ms | 100.81 ms | 47 |
| > 50k | 374.18 ms | 780.79 ms | 40 |

Sub-millisecond figures are at timer resolution; the 47- and 51-sample tails are unstable estimates
(§3.2). Treat this table as shape, not measurement.

**F1 — the primary gate covers EVERY sampled incident whose result lands in 10–5,000, regardless of
how the incident was generated.** Class labels (`hub`, `region_scoped`, `cyclic`) are diagnostic
slices reported alongside; they are **never** grounds for exemption from the gate.

Rev 1 of this document got this wrong in a way that would have manufactured a pass: it defined
"typical" by result size, then exempted `region_scoped_hub` as an "outlier class" — even though that
class produces results *inside* the band. Excluding the expensive in-band case from a gate defined by
result size is circular. If a narrower workload definition is ever wanted, it must come from an
external statement about production traffic, not from post-hoc classification of what turned out slow.

### 0.2 The case that flaw would have hidden

Measured directly, with a synthesised 1% region:

```
hub, region=tiny :  74.5 ms   service_count=1994   waves=1994
  _affected      :  69.6 ms   (full closure over ~199k nodes, then retain 1,994)
  _waves         :   3.5 ms
```

A **1,994-service result — squarely in-band — costs 74.5 ms**, against ordinary 1k–5k incidents at
p95 8.08 ms. Roughly 15× the cost for a comparable result size, because retention (D2/D9) happens
after full propagation: the traversal pays for all ~199k reached nodes.

This is architecturally forced, not a bug, and `iter1-work.md` §0.4 predicted it. What is new is the
magnitude: it converts the comfortable 20× headroom into **1.3×** for the worst in-band case.

Note also the bottleneck *inverts* by class: here `_affected` is 69.6 of 74.5 ms, whereas on the
large-result incident `_waves` dominated. There is no single hotspot to optimise (§5).

### 0.3 Two hypotheses tested and eliminated

Rev 1 asserted that localisation scaffolding dominates `_waves`, inferring it by subtracting Tarjan's
cumulative time. That inference does not isolate anything — `_waves` also does condensation, key
computation, heap scheduling, wave materialisation, and per-wave sorting.

One sub-hypothesis is now measured and **false**. Under `single_component` a large acyclic result emits
one wave per SCC, so the hub incident produces 179,161 waves; `maximal` produces 101. If wave
materialisation and heap traffic dominated, the two should differ enormously:

```
policy=single_component :  854 ms   waves=179,161
policy=maximal          :  796 ms   waves=     101
```

~7%. Wave/heap output is **not** the dominant cost, and D1 has effectively no latency dimension — worth
knowing, since D1 was chosen on semantics and it is useful that performance does not argue against it.

**F2 — no lever is selected until explicit phase timers exist** (§5). Rev 1's ordering was inference
dressed as measurement.

### 0.4 Memory: comfortable, but state it precisely

63 MB is the build/steady-state high-water; **219 MB is the peak observed**, after a 199k-service
incident. Under a gate that reads "peak RSS, any class < 512 MB", 219 MB is the figure that must be
quoted — rev 1 quoted 63 MB, which is the wrong number for its own acceptance rule.

So: ~150 MB of transient per-query structures for the largest incident, against a 512 MB budget. That
is comfortable on this probe. It is not yet "solved" — it is one unreproduced measurement on one graph,
and query RSS tripled the build figure.

---

## 1. Deliverables

| File | Role |
|---|---|
| `scripts/gen_scale_fixture.py` | Deterministic generator; writes `services.csv` / `dependencies.csv` |
| `scripts/bench_scale.py` | Harness: build, measure, gate, report |

**F3 — neither runs under `python3 -m unittest`.** The suite is 39 tests in 0.42 s; a multi-second
benchmark does not belong in it. `scripts/check.sh` is untouched.

**F4 — generated CSVs are never committed** (~30 MB, and the repo has no `.gitignore`). Default `--out`
is a temp dir outside the repo.

---

## 2. Generator and workload (`gen_scale_fixture.py`)

Seeded RNG, fixed default seed, config echoed into the report so any result is traceable to its inputs.

### 2.1 Structure

Fleet-shaped graph at ~200k / ~1M carrying the fixture's adversarial features at scale: duplicate rows,
soft rows, malformed rows with unknown endpoints, self-edges, many small cycles, at least one large
SCC, multi-region spread, at least one high-reverse-degree hub, and — required by §0.2 — **at least one
deliberately small region (~1%)**, since that is what makes the expensive in-band case reachable.

### 2.2 Workload definition — declared, never selected on results

**F5 — the incident workload is defined structurally, before any timing, and every sampled incident is
kept and reported.**

Rev 1 proposed sampling seeds, running them, and keeping those whose closure landed in 10–5,000. That
conditions the population on the planner's own output and biases toward cheap, low-degree subgraphs —
precisely the failure `plan.md` §0.4 warns about, since two incidents with 2,000 results can differ by
an order of magnitude in traversal cost. It would also have discarded the §0.2 case as "not typical".

Instead, the workload is drawn from declared structural strata — seed degree band, region size band
(none / large / small), position (near-hub, mid-graph, leaf, inside-SCC), seed count — with fixed
counts per stratum. Nothing is filtered afterwards.

**F6 — per-incident diagnostics are recorded for every incident**, not just latency:

`incident_id, stratum, seed_count, region, result_size, reached_nodes, reverse_edges_scanned,
retained_edges, scc_count, wave_count, latency_ms`

`reached_nodes` and `reverse_edges_scanned` are what make the §0.2 case legible — they show cost
tracking degrees touched rather than result size, and turn "this one is slow" into "this one scanned
969k edges to retain 1,994 nodes". Both require light instrumentation (counters returned from
`_affected`) — acceptable in the harness, and must be **off** in the timed path or measured separately
so counting does not distort the timing it explains.

---

## 3. Measurement methodology (`bench_scale.py`)

### 3.1 Runs

**F7 — three separate processes, because the instruments interfere:**

| Run | Purpose | Instruments |
|---|---|---|
| **A — timing** | Latency gate | `perf_counter` only. No `tracemalloc` |
| **B — memory** | RSS gate | `ru_maxrss` sampled after build, after each stratum, after the 10k run |
| **C — diagnostics** | Explanation | `tracemalloc`, phase timers, per-incident counters (§2.2) |

Run A produces the numbers that gate; run C explains them. `tracemalloc` adds both memory and latency
overhead, so a figure from C is never quoted as a production number.

### 3.2 Statistics

- **F8 — quantile convention: nearest-rank on the sorted sample**, stated in the report. Rev 1's "a p95
  over 47 samples is not a p95" was wrong — it *is* a p95 estimate, just an unstable one with poor tail
  resolution. Correct requirement: **minimum 200 samples per gated stratum**, and every reported
  quantile carries its `n`. Below 200, report the raw sorted tail instead of a quantile.
- Report p50, p95, p99, max per stratum, plus the gate verdict over the pooled in-band population.
- Discard the first N incidents as warmup and state N. The rationale is **allocator state, CPU
  frequency scaling, and branch/cache warmth** — not import cost, since imports and the planner build
  complete before any timed `plan()` call.
- Fixed seed for incident selection; identical incidents every run.
- Report header records machine, OS, Python version, `array("i").itemsize` (the code branches on it),
  and the generator config.

### 3.3 Memory specifics

- **F9 — normalise `ru_maxrss` units explicitly**: bytes on macOS, KiB on Linux. Detect via
  `sys.platform` and record the raw value and the unit in the report. (The probe assumed macOS bytes.)
- Do **not** claim a precise "per-query transient" from a build-only vs build-plus-query process
  difference. Allocator retention and execution history make that a bound, not a measurement. Report it
  as "RSS high-water rose from X to Y across the query phase".
- Do **not** assume the largest result is the highest-memory case. Sample RSS after **every** stratum;
  memory tracks reached nodes, retained edges, SCC structure, and wave count independently.
- **The full 10k-query run gets its own RSS verdict**, since the high-water can climb across a
  heterogeneous mix even when no single query is large.

### 3.4 Acceptance

| Gate | Criterion |
|---|---|
| **Latency** | p95 < 100 ms over **all** incidents whose result is 10–5,000, pooled across strata (F1) |
| **Memory** | Peak RSS < 512 MB at every sample point, including after the 10k run |
| Build time | **Reported, not gated.** README permits startup preprocessing |
| Throughput (10k queries) | **Reported, not gated.** The README states a process volume, not a completion deadline; converting wall time into a pass/fail invents a requirement |
| Out-of-band results (< 10, > 5,000) | Reported, characterised, ungated |

---

## 4. Expected outcome

On probe numbers, ordinary in-band incidents sit ~12–20× inside budget, but the **worst in-band case
(§0.2) is 74.5 ms against 100 ms — about 1.3× margin**. Rev 1's conclusion ("~5 ms p95, 20× headroom,
optimise nothing") was an artifact of the exemption this revision removes.

So the honest expected finding is: **passes, with one thin-margin class.** That margin is fragile in
ways the harness should probe rather than assume — a larger hub, more edges, a slower machine, or a
smaller region all push the §0.2 case toward the limit, and it is dominated by `_affected`, which
scales with fleet-wide reverse degree rather than anything the incident controls.

Two consequences:

1. The harness must **sweep** the §0.2 case (hub fan-in × region size) rather than measure one point,
   so the report shows where the 100 ms crossing actually is.
2. If the crossing sits near plausible production shapes, optimisation moves from contingency to
   required — and §5 says the target is `_affected`, not the localisation work rev 1 nominated.

---

## 5. Levers — withdrawn pending measurement (F2)

Rev 1 ranked levers from a cProfile subtraction that isolated nothing. Two things are now known, and
neither supports that ranking: wave/heap output is ~7% (§0.3), and the bottleneck inverts by class —
`_affected` dominates the region-scoped case (69.6/74.5 ms) while `_waves` dominates large results.

**Prerequisite:** explicit phase timers around localisation, SCC, condensation, key computation, heap
scheduling, and wave materialisation, reported per stratum in run C. Only then rank levers.

Candidates, unranked: cheaper induced-subgraph construction (flat CSR mirroring Phase 1); skipping
localisation below a measured crossover; skipping Tarjan when the induced subgraph is acyclic; scratch
buffer reuse; caching by `(frozenset(seeds), region)` — the last only if the workload actually repeats
incidents, which nothing in the README claims.

For the §0.2 case specifically, the only structural lever is to stop paying full traversal for a
region-scoped query — e.g. region-partitioned adjacency. That is a **semantics-affecting** change
(D2/D9 decide that propagation must cross regions), so it is a design question for the interviewer,
not a local optimisation.

---

## 6. Threats to validity

- **Generator realism is the weakest link.** The result rests on a synthetic blast-radius distribution
  matching a production one nobody has shown us. §2.1 is a documented assumption — and rev 1's probe
  shows how far a plausible generator can skew the answer.
- **The workload strata are also an assumption.** F5 removes selection-on-output bias but replaces it
  with a declared prior about what incidents look like. State it explicitly in the write-up.
- **One machine, one Python, one seed.** No cross-platform claim; `itemsize` recorded.
- **Instrumented counters (F6) perturb what they measure** — hence the run split in F7.
- **Timer resolution** bounds the sub-millisecond strata; report those as "below resolution".
- The §0.2 measurement used a **synthesised** region (rewriting `region_of` in place), not a generated
  one. The harness must reproduce it from generated data before the number is trusted.

---

## 7. Build order

1. `gen_scale_fixture.py` including the small region (§2.1). **Checkpoint: print the structural strata
   and their result-size histogram — do not filter on it, just look at it.**
2. `bench_scale.py` run B (build + memory) — cheapest, and settles the 512 MB question.
3. Run A: stratified latency with the F1 pooled gate. Confirm both the ordinary in-band p95 and the
   §0.2 case.
4. The §0.2 sweep (hub fan-in × region size) to locate the 100 ms crossing.
5. Run C: phase timers and per-incident counters; only now consider §5.
6. Write results into the walkthrough, including the §0.1 story — *"the naive benchmark said 350 ms and
   was measuring the wrong thing; the corrected one found a 74 ms case the first framing would have
   excluded"* is a better answer to "how did you verify this?" than any single number.

**Definition of done:** one command regenerates inputs and reproduces the report; the pooled in-band
latency gate and every RSS sample carry explicit verdicts; the §0.2 crossing is located; out-of-band
classes are characterised; the 39-test suite and `scripts/check.sh` are unaffected.
