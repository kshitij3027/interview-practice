# RecoveryWave — One-Hour AI-Assisted Problem-Solving Interview

## Customer context
A B2B platform operates a large fleet of internal services. During an incident, one or more services may be restarted or replaced. Services declare hard runtime dependencies on other services. If a dependency is restarted, every service that transitively depends on it must also be restarted before traffic is considered safe again.

The operations team currently builds recovery plans by hand. This works for small incidents, but production has roughly **200,000 services**, **1,000,000 dependency records**, and thousands of incident queries per day.

You are given a representative dataset and asked to build a recovery planner that could plausibly be adapted for production.

## Supplied data
`fixtures/services.csv` contains:
- `service_id` — unique service identifier
- `tier` — integer operational tier; lower numbers are more critical
- `region` — service region

`fixtures/dependencies.csv` contains directed dependency declarations:
- `service_id`
- `depends_on`
- `kind` — `hard` or `soft`

A row `checkout,pricing,hard` means checkout cannot safely operate until pricing is available.

`fixtures/incidents.jsonl` contains incident requests. Each line is a JSON object with:
- `incident_id`
- `failed_services` — one or more services that must be restarted
- optional `region` — if present, only services in that region may appear in the plan

The fixture intentionally contains duplicates, a cycle, soft dependencies, and services that are not involved in every incident.

## Goal
Implement `plan_recovery(...)` in `planner.py` and wire the CLI so that each incident produces one JSON result.

For each incident, identify every service that must be restarted because it is failed itself or transitively relies on a failed service through **hard** dependencies. Then partition those services into ordered restart waves.

A service may appear in a wave only when every hard dependency that is also part of the recovery plan is either:
1. in an earlier wave, or
2. in the same wave because those services cannot be safely ordered relative to one another.

The output must be deterministic.

## Observable requirements
For each incident, output:

```json
{
  "incident_id": "inc-001",
  "waves": [["svc-a"], ["svc-b", "svc-c"]],
  "service_count": 3
}
```

The following rules apply:

1. Include the initially failed services if they exist and are eligible for the incident.
2. Include all services transitively affected through `hard` dependencies only. `soft` dependencies never force another restart.
3. A service outside an incident's requested region must not appear when `region` is supplied. Region filtering applies to both failed services and affected dependents.
4. Duplicate dependency rows must not duplicate work or output.
5. Input may contain self-dependencies and multi-service dependency loops. The planner must still return a valid finite plan.
6. Services that cannot be ordered relative to one another because of their dependency relationships must be placed in the same wave.
7. Waves must respect dependency ordering for the affected subgraph: dependencies restart before their dependents.
8. Within each wave, order service IDs lexicographically.
9. When multiple valid waves could be emitted at the same point, choose deterministically by the smallest tuple `(tier, service_id)` among services becoming eligible; do not rely on CSV/dictionary iteration order.
10. Unknown service IDs in an incident must be reported under `unknown_services` and ignored for planning rather than crashing the whole run.
11. Malformed dependency rows whose endpoints are unknown must be ignored and counted once in a top-level `ignored_dependency_rows` metric.
12. The process should parse and preprocess the static service/dependency data once, then handle many incident queries without rebuilding all static indexes for every request.

## Production constraints
Design for this production shape even though the fixture is small:

- ~200k services
- ~1M dependency rows
- up to 10k incident queries against the same static graph per process
- typical incident result: 10–5,000 affected services
- memory budget: 512 MB
- target p95 planning latency after startup: under 100 ms for typical incidents

A solution that performs all-pairs analysis, materializes full transitive closure, or rescans all dependency rows for every incident is not considered production-credible.

You may preprocess the static dataset at startup. Be prepared to explain the startup/query-time tradeoff you chose.

## Expected deliverable
Implement a working Python solution in this repository. You may modify `planner.py`, add focused tests, and add small helper modules if useful.

Your walkthrough should explain:
- how you model the customer problem;
- why your approach satisfies ordering and loop semantics;
- expected startup and per-query complexity;
- how the approach behaves at production scale;
- what you would change if latency or memory measurements disagreed with your assumptions;
- whether an LLM or heuristic component would add value here, and why you did or did not use one.

## In scope
- Python standard library or lightweight local dependencies if you choose to add them.
- Preprocessing/indexing.
- Deterministic or hybrid solutions.
- Focused unit/integration tests.

## Out of scope
- Distributed execution.
- Persistent databases.
- Live service discovery.
- Network calls.
- A web UI.

## Run / verify
Baseline checks:

```bash
python3 -m unittest -v
python3 planner.py --help
```

After implementing the feature:

```bash
python3 planner.py \
  --services fixtures/services.csv \
  --dependencies fixtures/dependencies.csv \
  --incidents fixtures/incidents.jsonl
```

Write one JSON object per incident to stdout. Diagnostic logging, if any, should go to stderr.

## 60-minute interview instruction
You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or other AI tools as you would on the job. Start by inspecting the fixtures and constraints before committing to an implementation. The interviewer cares about the problem decomposition, correctness, scaling argument, verification strategy, and your ability to explain the resulting code—not about memorizing a particular technique.

Do not spend the hour polishing CLI ergonomics. Prioritize a correct, scalable core and enough tests to demonstrate that you understand the difficult cases.

## Implementation walkthrough

`RecoveryPlanner` interns service IDs as integers and builds forward and reverse compressed sparse row
(CSR) indexes once. An incident walks the reverse index from its failed services to find the transitive
blast radius. Region filtering is deliberately applied after propagation, so an out-of-region service
can still carry impact to an eligible dependent. The retained graph is reduced to strongly connected
components with iterative Tarjan; each component is one indivisible restart unit. A deterministic
heap-based topological traversal then emits dependencies before dependents, using `(tier, service_id)`
as its eligibility key.

Startup is `O(V + E + sum(d log d))` time because each adjacency slice is sorted and deduplicated, and
`O(V + E)` memory. For a query, reverse traversal is `O(R + E_R)`, where `R` is the reached set before
region retention. SCC construction and ordering are linear in the retained induced graph aside from
deterministic sorting and heap operations. No transitive closure or per-query scan of all static rows is
materialized.

This is a deterministic graph problem; an LLM or heuristic would add nondeterminism without improving
the correctness or asymptotic behavior. If production measurements miss the target, the diagnostic
run separates reverse traversal, localization, SCC, condensation, key computation, scheduling, and
materialization so optimization follows measured work. In particular, region-scoped hub incidents can
return only ~2,000 services while still traversing the entire fleet; region-partitioned traversal would
need a semantics decision because propagation currently crosses regions by design.

## Scale verification

The production-shape validation is intentionally separate from the unit-test gate:

```bash
# Full defaults: 200k services, 1M rows, >=200 samples per stratum, 10k queries.
python3 scripts/bench_scale.py --report /tmp/recoverywave-scale-report.json

# Fast automation/E2E profile (also covered by test_scale_tools.py).
python3 scripts/bench_scale.py --services 800 --dependency-rows 4000 \
  --cluster-size 100 --samples-per-stratum 3 --warmup 2 \
  --throughput-queries 20 --sweep-repetitions 1 \
  --allow-insufficient-samples --report /tmp/recoverywave-smoke.json
```

The generator uses a fixed seed and writes its large CSVs to a temporary directory outside the
repository by default. Its graph includes duplicate, soft, malformed, self-loop, small-cycle,
large-SCC, multi-region, high-fan-in hub, and 1%-region cases. Workload strata are declared from graph
position before planning; no incident is selected or discarded based on measured output.

The harness launches three fresh processes: A uses only `perf_counter` for the latency gate, B samples
normalized `ru_maxrss` after every stratum, every hub/region sweep point, and the 10k run, and C uses
`tracemalloc`, graph-work counters, and phase timers for explanation. Quantiles use nearest rank and are
only reported for samples of at least 200; smaller sweep samples expose their sorted tail.

On 2026-08-22, the full default run on arm64 macOS 26.5.2 and Python 3.14.2 produced:

- 200,000 services and 1,000,000 rows; 899,941 unique hard edges and 1,000 ignored malformed rows.
- **Latency PASS:** nearest-rank pooled in-band p95 **62.77 ms** over 1,750 incidents; p99 64.26 ms,
  max 85.90 ms. The 1%-region hub stratum had p95 64.83 ms for 2,001 returned services.
- **Memory PASS:** `ru_maxrss` high-water **221,282,304 bytes (211.0 MiB)**, established by the
  199,997-service unscoped hub sweep and still below the 512 MiB gate after the full query run.
- Startup was about 2.0 seconds. The ungated heterogeneous 10k run took 106.34 seconds
  (94.04 queries/second).
- The sweep crossed 100 ms for unscoped 30% fan-in and for several large out-of-band result cases;
  sampled 1% and 5% region cases stayed below 100 ms. Instrumented diagnostics confirmed the
  in-band 1%-region hub reaches 199,997 nodes and scans 799,945 reverse edges to retain 2,001 nodes,
  with reverse traversal dominating that class.

These figures describe one synthetic seed on one machine, not a cross-platform production guarantee.
The JSON report retains every timed incident and every diagnostic record so the result-size histogram,
structural strata, sweep tails, and phase costs remain auditable.
