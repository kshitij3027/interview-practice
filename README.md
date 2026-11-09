# VaultScope — HARD 60-Minute AI-Assisted Customer Interview

## Customer and business context

A B2B document platform serves multiple companies. Users gain access to a document either directly or through one or more nested teams. Security administrators publish allow and deny policies, periodically correct team memberships, and retire old policies. The current audit spreadsheet checks direct policies only and sometimes grants access that a nested-team denial should block. Analysts also need to explain **which policy decided the outcome, and how the user reached that policy**, as of an arbitrary historical timestamp.

Your single task is to build a **trustworthy effective-access auditor**. You own the technical strategy, including any preprocessing, indexes, deterministic logic, heuristic, LLM-assisted, or hybrid implementation. All observable decisions and explanations must be exact. No third-party service, network access, or LLM key is required. Inspect the data and contracts before picking your approach.

## Supplied data

The `fixtures/` directory contains six small, representative exports:

- `users.csv`, `groups.csv`, `resources.csv`: declarations of `user_id`, `group_id`, and `resource_id`, each paired with `tenant_id`.
- `memberships.csv`: historical changes to membership relationships, with columns `membership_id,revision,op,member_type,member_id,group_id,active_from_ms,active_until_ms`.
- `policies.csv`: historical policy changes, with columns `policy_id,revision,op,resource_id,subject_type,subject_id,action,effect,active_from_ms,active_until_ms`.
- `queries.jsonl`: independent access-audit requests, one **physical line** per request, including some deliberately invalid examples and repeated query IDs.

`vaultscope/data.py` contains a functioning snapshot loader and request parser. `vaultscope/engine.py` contains the unfinished `VaultScope.decide(query)` capability. `vaultscope.py` and `vaultscope/cli.py` provide the running CLI; `tests/` and `scripts/` are the existing baseline checks. You may reorganize the implementation while preserving the input/output contract.

CSV files have exactly the named headers, in any column order. All IDs are case-sensitive ASCII letters, digits, `_` or `-`, 1–48 characters (`query_id` permits 1–128); tenants are isolated. Canonical CSV unsigned integers have no leading zeros except `0`. Repeated declaration rows with identical fields are harmless; conflicting declarations invalidate the snapshot.

For memberships, `member_type` is `user` or `group`, identifying the entity being included in `group_id`. A group may itself be included in another group. **Repeated and cyclic membership relationships are valid** and do not imply unlimited permissions. For policies, `subject_type` is `user` or `group`; `action` is precisely one of `view`, `edit`, `export` (no action implies another), and `effect` is `allow` or `deny`. A policy always concerns exactly one resource.

Membership/policy changes are identified by `(membership_id,revision)` or `(policy_id,revision)`. Rows can be unordered. Identical repeats of the same ID/revision are retries. Conflicting repeats invalidate the entire snapshot. **Only the highest numeric revision** of each ID governs the snapshot, even if it is a deletion; revisions need not be consecutive. An `upsert` contains the full business record. A `delete` has all business fields blank; a delete without an earlier upsert is valid. Higher revisions are authoritative regardless of CSV row ordering. A superseded malformed or cross-tenant upsert still invalidates the entire snapshot.

Timestamps are absolute integer milliseconds on a fictional common clock, in `[0,10^12]`. An active membership or policy applies exactly when `active_from_ms <= at_ms < active_until_ms`; an upsert requires `active_from_ms < active_until_ms`. No implicit expiration extension, inheritance between `view`/`edit`/`export`, or clock conversion occurs.

All referenced members, groups, resource targets and subjects must exist and must belong to the **same tenant** as the membership or policy's target. An unknown reference, cross-tenant catalog relationship, malformed CSV, invalid revision, or conflicting ID invalidates the **entire catalog before any query output**. The provided loader handles this validation. Malformed JSONL query lines do not invalidate the catalog or prevent later lines from being processed.

## Primary customer request

Implement `VaultScope.decide(query)` so each valid request for `user_id`, `resource_id`, `action`, and `at_ms` receives the **effective access decision at that timestamp**. A valid request looks like:

```json
{"query_id":"example","user_id":"alice","resource_id":"handbook","action":"view","at_ms":300}
```

A policy matches if its latest version is an active upsert; it has the requested resource and exact action; its time window contains the request time; and either it targets the user directly or its group target includes the user through **zero or more nested team memberships** whose latest versions are active at that time. A membership chain may pass through any number of groups, but must start at the requested user. A direct user policy uses no memberships.

If **any** matching policy denies, the decision is `deny` even if another matching policy allows. Otherwise, if any matches allow, the decision is `allow`; otherwise it is `none`. An absent policy cannot create a grant or denial. Return a **single deterministic explanatory witness** when a policy matches:

1. Only policies whose effect equals the final decision are eligible as witnesses.
2. Among them, prefer the one reachable through the **fewest membership relationships** (direct user policy has zero).
3. If tied, prefer the lexicographically smaller case-sensitive `policy_id`.
4. For one chosen group policy with multiple equally short routes, prefer the **lexicographically smallest sequence of group IDs** from the user's first group to the policy's target group.

For `allow` or `deny`, return exactly this JSON shape (example values are illustrative, not fixture answers):

```json
{"query_id":"example","status":"ok","decision":"allow","policy_id":"policy_7","via":["team_a","team_b"]}
```

`via` is the sequence of group IDs traversed **including the policy target group**, or `[]` for a direct user policy. Every adjacent pair must be justified by an active membership and the first group must contain the user. For `none`, return `{"query_id":"example","status":"ok","decision":"none","policy_id":null,"via":[]}`. No explanations may mix inactive edges, skip groups, or cross tenant boundaries. Multiple matching policies do not create multiple result lines.

The existing CLI emits one compact UTF-8 JSON object per **physical query line**, in file order. Duplicate `query_id` values are independent requests. Unknown user or resource returns `{"query_id":"id","status":"invalid","reason":"unknown_entity"}`; known user and resource from different tenants returns `reason:"tenant_mismatch"`; malformed requests return `reason:"invalid_query"`, preserving a valid query ID if possible and otherwise using `null`. Extra query keys are ignored. JSON `at_ms` must be an actual integer (not a boolean, numeric string, or float) in `[0,10^12]`. A malformed catalog exits nonzero with a useful stderr diagnostic **and no query result lines**. Keep diagnostics off stdout.

## Observable acceptance criteria

- Results are invariant under CSV input row order, replayed identical revisions, and the order of unrelated queries; only each ID's highest revision counts.
- Direct policies and nested teams both apply. Multiple group parents, paths of different lengths, and actual cycles are supported without infinite work; membership paths are meaningful at the query's timestamp.
- A matching deny wins over any number of allows, regardless of path length. Only an exact action matches, and no path across tenants is permitted.
- Time windows are half-open. At exactly `active_from_ms` an entry applies; at exactly `active_until_ms` it does not. Later revisions can replace intervals or delete entries entirely.
- Explain a winning decision through the shortest valid chain, with case-sensitive policy ID and group-sequence tie breaks. A direct policy has `via:[]`.
- A query with no matching policy returns `none` with null policy and empty path. A group-only policy does not apply to a user who is not currently its member.
- Invalid queries are individually rejected without disrupting following lines. Unknown references or cross-tenant catalog rows reject the complete snapshot before output. Repeated query IDs remain independent.

## Production constraints and expected deliverable

The fixture is intentionally compact. A production snapshot can contain **300,000 users, 90,000 groups, 1.5 million distinct membership revisions, 220,000 policy revisions, and 400,000 audit queries**. Popular teams can have thousands of nested members and thousands of audit queries may repeat a user at different times. Query timestamps are arbitrary; an edge can start or end in the middle of a reporting interval. Target roughly **768 MB memory** and **p95 below 40 ms per typical query after snapshot loading**, on a single worker. These are design targets to explain, not tiny-fixture benchmarks.

A full catalog scan for every query, treating all group relationships as permanently active, or enumerating every possible path is not a credible strategy. Discuss validation cost, preparation cost, correctness, repeated-query performance, worst-case highly connected groups, invalidation/caching risks, and memory. A correct narrow slice with measured tests and a defensible scaling design beats a broad, unverified one-shot attempt.

Deliver a runnable auditor, additional focused or adversarial tests you write, and a short walkthrough of correctness and time/space complexity. You may refactor supplied code without breaking the CLI contract. Out of scope: a web UI, live user authentication, changing the catalog after snapshot load, external identity providers, tenant administration, OAuth, role hierarchies, and assigning policies.

## 60-minute AI-assisted interview instructions

You have **60 minutes**. Use Claude Code, Codex, ChatGPT or any other AI tools as you would on the job. First read the README and representative fixtures. Explain your intended approach and tradeoffs to the interviewer, inspect the starter code, implement iteratively, verify outputs with added tests and boundary cases, and be ready to defend your choices. You do not have to memorize an algorithm or use an LLM. The interviewer will focus on whether the customer's problem is solved and how you verified it.

Python **3.11+**, standard library only. From the branch root:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 vaultscope.py audit --catalog fixtures --queries fixtures/queries.jsonl
```

The supplied tests and verifier establish a working CLI and parsing baseline; they **do not** certify effective-access decisions. The requested decision capability is intentionally absent.
