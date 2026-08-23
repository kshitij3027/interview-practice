# Repository Guidelines

## Project Structure & Module Organization

This branch contains the RecoveryWave interview exercise. Treat `README.md` as the authoritative specification because other branches host unrelated exercises.

- `planner.py`: CSV/JSONL loaders, recovery-planning implementation, and CLI entry point.
- `test_baseline.py`: baseline `unittest` coverage for the supplied parsers. Add focused tests here or in new `test_*.py` modules at the repository root.
- `fixtures/`: representative service, dependency, and incident inputs. Preserve adversarial cases such as duplicate edges and cycles.
- `scripts/check.sh`: repository verification gate.

Directories such as `backend/`, `node_modules/`, `test-results/`, and `.venv/` are leftovers from other exercise branches and are not part of this implementation.

## Build, Test, and Development Commands

The project targets Python 3.14 and uses only the standard library; there is no build or dependency-install step.

```bash
python3 -m unittest -v
python3 -m unittest -v test_baseline.py
bash scripts/check.sh
python3 planner.py --services fixtures/services.csv \
  --dependencies fixtures/dependencies.csv --incidents fixtures/incidents.jsonl
```

The check script runs all unit tests and verifies CLI argument parsing. The final command emits one JSON object per incident to stdout; send diagnostics to stderr.

## Coding Style & Naming Conventions

Follow standard Python conventions: four-space indentation, type annotations for public functions, `snake_case` for functions and variables, and `PascalCase` for classes. Prefer small, deterministic functions and standard-library data structures. Keep static graph preprocessing separate from per-incident planning so indexes are built once. Do not depend on dictionary or CSV iteration order; apply the sorting rules in `README.md` explicitly.

## Testing Guidelines

Use `unittest`. Name files `test_*.py`, test classes `*Tests`, and methods `test_*`. Cover hard versus soft dependencies, region filtering, duplicate rows, unknown services, self-loops, multi-service cycles, deterministic wave ordering, and malformed dependency metrics. Run `bash scripts/check.sh` before submitting.

## Commit & Pull Request Guidelines

Recent commits use short, imperative, sentence-case subjects, for example `Add recovery wave planning interview exercise`. Keep each commit focused. Because there is no `.gitignore`, never use `git add -A`; stage only intended paths explicitly.

Pull requests should summarize the approach, call out startup and per-query complexity, list verification commands, and link the relevant issue when one exists. Include sample CLI output for behavior changes; screenshots are unnecessary for this CLI-only project.
