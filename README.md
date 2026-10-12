# BundlePort — HARD 60-Minute AI-Assisted Systems Interview

## Customer and business context

A managed enterprise software platform provisions offline application bundles for field devices. Each bundle contains one or more requested applications and whatever supporting modules their selected releases require. The release catalog changes daily; customers download a single consistent bundle for one device platform. Failed bundles strand field technicians without network access.

The current picker chooses the cheapest individual release for each requested application and then adds dependencies. On realistic catalogs this may result in mutually incompatible releases, unnecessary downloads, or an incorrect claim that no bundle is possible. Build the planner for **one immutable catalog and a stream of independent bundle requests**. Choose the technical approach yourself.

## Supplied data

- `fixtures/releases.csv`: `name`, `version` (`major.minor.patch`, nonnegative integer components), `platform` (`*`, `linux-x64`, `mac-arm64`), `download_kb` (positive integer), `active` (`true`/`false`). The `(name, version)` pair identifies a release; a package may have multiple versions. Inactive releases cannot be selected.
- `fixtures/requirements.csv`: one mandatory requirement made by a specific parent release: `parent_name`, `parent_version`, `target_name`, `min_version` (inclusive), `max_version_exclusive` (exclusive). Every requirement on a selected release must be satisfied, including multiple requirements on the same target.
- `fixtures/conflicts.csv`: `name`, `version`, `other_name`, `other_version`. The two specified releases cannot coexist; the relationship is symmetric. Duplicate or reversed copies mean the same restriction.
- `fixtures/requests.jsonl`: one independent request per line with `request_id`, `platform`, `max_download_kb`, and nonempty `roots`: `{ "name", "min_version", "max_version_exclusive" }`. A repeated root applies all its ranges simultaneously. All ranges use numeric version comparison, not string comparison.

An identical duplicate release or requirement row is a harmless catalog replay. Reusing a `(name, version)` release key with different data is a catalog error. Conflicts and requirements must reference real parent releases. Some listed releases may be unusable due to platform or inactive status; these rows are still legitimate catalog data.

## Primary customer request

For each valid request, **choose exactly one active, platform-compatible release for every needed package**, including every explicitly requested root and all mandatory transitive requirements. A selected release may require other releases; follow those requirements until the entire selection is consistent. No two selected releases may conflict. The bundle's total download size must not exceed `max_download_kb`.

When multiple valid bundles exist, select the unique best bundle under the following precedence:

1. Lowest `total_download_kb`.
2. Fewest distinct packages selected.
3. Lexicographically smallest complete sequence of `(name, version)` pairs after sorting by `name`; compare version components numerically at the first differing pair. If one sequence is a proper prefix of the other, the shorter sequence is smaller.

If no bundle satisfies all conditions, return `status: "unsatisfiable"`, not a partially successful bundle. Cyclic requirements are legal if all selected releases can be satisfied together; the output is a set of releases, not an installation order.

## Observable behavior and acceptance criteria

The `plan` command must output exactly one JSON object per input line in original order, with no diagnostics on stdout. For a satisfied request:

```json
{"request_id":"demo","status":"planned","total_download_kb":42,"selected":[{"name":"agent","version":"1.0.0","download_kb":42}]}
```

This illustrates output shape, not a fixture answer. `selected` is sorted by package name. For a valid request with no valid selection emit `{"request_id":"demo","status":"unsatisfiable"}`. For malformed JSON or an invalid request emit `{"request_id":null,"status":"invalid","reason":"invalid_request"}` (preserve `request_id` only if it is a nonempty string).

Required behavior includes:

- Respect all root requirements, including duplicate names with overlapping or contradictory version ranges.
- Enforce every requirement belonging to the **chosen release**, even when requirements form cycles or a package is required from several places.
- Select at most one version of any package. An active version with a compatible platform may still be impossible due to other constraints.
- Apply conflict restrictions regardless of which side appears first in the catalog.
- Honor `*` platform releases on either supported request platform; never select a release for a different platform.
- Apply the download budget inclusively at equality; do not double-count the size of a shared dependency.
- Find the globally best *complete* bundle, not the locally cheapest or highest release at each step.
- Apply all ranking levels deterministically independent of CSV row order, request ordering, set/map iteration, or hash randomization.
- Treat catalog replay rows correctly, reject invalid/conflicting catalog definitions, and continue after a query-level JSON/validation error.
- Process each query independently, even when request IDs are repeated.

## Production constraints and expected deliverable

The checked-in fixtures are small and intentionally contain ambiguity. In production, a catalog can have **200,000 releases**, **750,000 requirement rows**, and **100,000 incompatibility pairs**; a batch can contain **10,000 requests**. Most requests reach 20–150 package names and 2–8 versions per name, but a few reach thousands of candidate releases. Device constraints are `linux-x64` and `mac-arm64`. Memory target is **1 GB** for shared catalog state, and an ordinary request should ideally resolve in **under 500 ms after catalog loading**. Explain worst-case complexity and where the latency goal may fail. There is no requirement to contact an LLM or an external service; you may choose an exact, heuristic, or hybrid strategy, but explain any observable guarantee it gives up.

Implement `BundlePlanner.plan_request(...)` in `resolver/service.py` and any supporting code/tests. The starter already loads and validates the catalog and requests, exposes a runnable CLI, and has green tests, but it **does not implement bundle planning**. Keep checked-in data small; do not edit fixtures to pass tests.

## Scope and out of scope

In scope: immutable catalog loading, correct feasible bundle selection, optimality and deterministic ranking, budget, platform, cyclic relationships, independent queries, validation, and verification. Out of scope: downloading binaries, solving real package-install order, authorization, persistent caches, mutable registries, security signatures, network calls, or a web UI.

## Setup, verification, and run commands

Python **3.11+**, standard library only:

```bash
bash scripts/test.sh
bash scripts/build.sh
bash scripts/verify.sh
```

After implementing the planner:

```bash
python3 bundleport.py plan --releases fixtures/releases.csv --requirements fixtures/requirements.csv --conflicts fixtures/conflicts.csv --requests fixtures/requests.jsonl
```

The `validate` command checks the catalog and request format. A green baseline or successful validation **does not** mean planning is implemented.

## 60-minute AI-assisted interview instruction

You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or other AI tools as you would at work. Inspect the fixtures and starter interfaces first. Determine how to preserve correctness when local choices interact, implement incrementally, verify adversarial cases, and defend your solution's complexity, memory use, failure modes, and tradeoffs. Prioritize a correct, explainable slice over untested code volume.
