# BundleLock — HARD One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

An enterprise SaaS platform ships a core product plus customer-installed extensions. Every extension release can require version ranges of other extensions. A rollout may target several packages at once, and incident response may temporarily block specific releases.

The current deployment tool walks dependencies and picks a locally attractive release. That fails when several packages constrain the same dependency, when changing one version changes downstream dependency scope, or when dependencies form cycles.

Build the in-process compatibility planner for one immutable release catalog, one current installation, and many independent rollout requests. The observable behavior is exact; the technical approach is yours.

## Supplied data

packages.csv contains package_id and display_name.

versions.csv contains package_id, version, channel, and artifact_mb. Versions use strict MAJOR.MINOR.PATCH form and compare numerically by major, minor, then patch. channel is stable or canary. artifact_mb is a positive integer.

dependencies.csv contains dependency_id, package_id, version, requires_package_id, min_version, and max_version_exclusive. Selecting the declaring concrete release activates that mandatory requirement. Exact replay rows with the same dependency_id deduplicate; conflicting reuse is invalid. Dependencies are conjunctive and may form cycles.

installed.csv contains the customer's current package/version pairs.

requests.jsonl contains independent requests with request_id, a non-empty targets array, blocked_versions, allow_canary, and max_changes. A target has package_id, min_version, and max_version_exclusive. blocked_versions contains exact package_id@version strings.

## Goal and semantics

A range [min_version, max_version_exclusive) accepts v exactly when min_version <= v < max_version_exclusive. The lower bound must be strictly smaller than the upper bound.

A release can be selected only when it satisfies every active requirement on its package, is not request-blocked, and is stable unless allow_canary is true.

A plan selects exactly one release for every package in scope. Scope starts with targets. Selecting a release activates that release's dependencies, which can add packages to scope. Only dependencies of the final selected releases are active, so changing one version may add or remove downstream packages.

A valid plan must satisfy every target, every dependency of every final selected release, request eligibility rules, and max_changes.

## Plan quality

Among all valid plans with change_count <= max_changes, choose exactly one by:

1. minimum change_count;
2. then minimum artifact_mb summed only over changed or newly installed packages;
3. then minimum final selected-package count;
4. then lexicographically smallest sorted sequence of package_id@version strings.

A package is changed if newly installed or selected at a version different from installed.csv. Installed packages outside final scope do not affect score.

Selections in output must be sorted by package_id. A successful result has status planned plus selections, change_count, and changed_artifact_mb. A well-formed request with no valid plan has status unsatisfiable. Malformed requests or unknown request references have status invalid with reason invalid_request. One bad request must not stop later requests.

## Acceptance criteria

- Emit exactly one result per request in input order.
- Reordering CSV rows, targets, blocked_versions, maps, or sets must not change results.
- Duplicate identical target requirements behave as one; different requirements on the same package all remain active.
- Lower range bounds are inclusive; upper bounds are exclusive.
- Numeric version comparison matters: 2.10.0 is greater than 2.9.9.
- Installed releases are not automatically eligible if blocked, out of range, or canary when canary is disallowed.
- Requirements from multiple selected packages on one dependency must all hold simultaneously.
- Cyclic dependencies must terminate and may be satisfiable or unsatisfiable.
- A discarded release choice must not leave stale downstream packages or requirements.
- max_changes is inclusive.
- Only packages in the final transitive scope participate in scoring.
- Exact dependency replays deduplicate; conflicting dependency IDs fail catalog validation.
- Unknown package/version references in dependencies or installed rows fail catalog validation.
- Invalid versions, channels, artifact sizes, dependency ranges, duplicate package/release identifiers, or empty required fields fail catalog validation.
- Diagnostic logs belong on stderr; stdout remains JSONL.

## Production constraints

Design for roughly 120,000 packages, 1.8 million releases, 6 million dependency rows, and 20,000 requests against one immutable catalog. Typical requests target 1–8 packages and reach 20–150 packages; incident cases may reach about 500. After broad filtering, a package often has 5–30 candidate releases. Cycles are uncommon but legal. Memory budget is about 1.5 GB and target p95 is under 250 ms for typical requests after startup.

A production-credible solution should not enumerate every version combination, copy the full catalog for each request, or assume newest-compatible, installed-first, or locally cheapest choices are globally correct. Reusable preprocessing is allowed. Be ready to explain request-local state, how impossible choices are eliminated, how equivalent work is avoided, worst-case behavior, and what exact guarantee you would relax if latency became unacceptable.

## Expected deliverable

Implement CompatibilityPlanner.plan(request) in bundlelock/planner.py and change supporting code as needed. Add focused tests for the risks you consider most important.

Be ready to explain requirement reconciliation, dynamic dependency scope, cycle handling, exact optimization order, branch/state isolation when a choice is abandoned, time/memory behavior, and the role—if any—of an LLM or heuristic in the critical planner.

## Run / verify

Python 3.11+ and the standard library are sufficient.

    bash scripts/test.sh
    bash scripts/build.sh
    bash scripts/verify.sh

After implementation:

    python3 compat_plan.py resolve --packages fixtures/packages.csv --versions fixtures/versions.csv --dependencies fixtures/dependencies.csv --installed fixtures/installed.csv --requests fixtures/requests.jsonl

## Scope / out of scope

In scope: immutable catalog loading, exact version/range semantics, conditional dependency scope, cyclic requirements, blocked/channel eligibility, deterministic optimal planning, validation, tests, and scale reasoning.

Out of scope: downloading artifacts, executing deployments, persistence, distributed locks, live catalog mutation, rollback execution, authentication, vulnerability scoring, prerelease/build metadata, and UI work.

## 60-minute AI-assisted interview instruction

You have 60 minutes and may use Claude Code, Codex, ChatGPT, or similar tools. Inspect the repository and fixtures yourself before delegating implementation. Restate the compatibility and scoring rules, implement incrementally, verify conflicting requirements and dependency-scope changes, and reserve time to defend correctness and scaling. A one-shot solution that merely fits the tiny fixture is not sufficient.
