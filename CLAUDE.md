# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A personal practice repo for timed (≈60 minute) AI-assisted engineering interview exercises. It is **not** one evolving product: each exercise is a self-contained codebase living on its own branch, and `main` holds only a `README.md`. Branch naming:

- `exercise/<date>-<slug>` / `problem/<date>-<slug>` — the candidate-facing starter (what you work in)
- `evaluator/<date>-<slug>` / `problem-evaluator/<date>-<slug>` — the same starter plus `GRADING_RUBRIC.md` and `INTERVIEWER_NOTES.md`

Because exercises differ completely (past ones were FastAPI + pytest services with `backend/app/…`, Playwright e2e, etc.), **always read the current branch's `README.md` first** — it is the authoritative spec, including the observable requirements the work is graded against. Do not generalize commands or architecture from this file across branches.

Untracked `backend/`, `node_modules/`, `test-results/`, and `.venv/` in the working tree are leftovers from earlier exercises' branches. There is no `.gitignore`, so never `git add -A`; stage explicit paths.

## Current branch: `problem/2026-08-21-recovery-wave-planner` (RecoveryWave)

Pure-stdlib Python 3.14 CLI. No package manifest, no external deps (the `.venv/` with FastAPI/pytest is stale from another exercise; `python3` on PATH is already 3.14).

```bash
python3 -m unittest -v                      # all tests
python3 -m unittest -v test_baseline.py     # one module
python3 -m unittest -v test_baseline.BaselineParsingTests.test_load_services  # one test
bash scripts/check.sh                       # baseline gate: unittest + `planner.py --help`

python3 planner.py --services fixtures/services.csv \
  --dependencies fixtures/dependencies.csv --incidents fixtures/incidents.jsonl
```

Results go to stdout as one JSON object per incident; any diagnostics go to stderr.

### Structure

`planner.py` is the whole program. Parsing (`load_services`, `load_dependencies`, `load_incidents`) and the argparse CLI are given; `plan_recovery` raises `NotImplementedError` and is the exercise. The starter signature `plan_recovery(services, dependencies, incident)` is explicitly a placeholder — the README expects it to be replaced by a preprocessed index/planner object built once and reused across incidents (rebuilding indexes per incident, materializing transitive closure, or all-pairs work is a stated failure).

### Domain semantics that drive the design

- Dependency edges are stored **forward** (`service_id depends_on depends_on`), but recovery propagates **backward**: a failed service forces restarts of its transitive *dependents*. The core index is therefore a reverse adjacency map over `hard` edges only.
- `soft` edges never force a restart and never constrain wave ordering.
- Waves are a layered topological order of the affected subgraph; mutually unorderable services (cycles) share a wave. IDs within a wave sort lexicographically; ties when choosing what becomes eligible break on `(tier, service_id)` — never on CSV or dict iteration order.
- `region`, when present on an incident, filters both the failed seeds and the affected dependents.
- Unknown incident services are reported in `unknown_services` rather than crashing; dependency rows with unknown endpoints are skipped and counted once in a top-level `ignored_dependency_rows`.

`fixtures/` is deliberately adversarial and small enough to reason about by hand: a duplicate edge (`checkout,pricing`), a self-loop (`search,search`), a 2-cycle (`legacy-sync` ↔ `partner-feed`), another cycle across regions (`shipping` ↔ `routing`), soft edges off `orders`/`catalog`, and two malformed rows (`ghost,…` and `…,missing-service`). Production shape to design for: ~200k services, ~1M edges, 10k queries per process, p95 < 100 ms per query after startup, 512 MB.
