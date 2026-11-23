# BatchPath — HARD 60-Minute AI-Assisted Interview

## Customer and business context

A B2B analytics platform refreshes interdependent datasets for enterprise customers. Each dataset has an earliest allowed start and processing time. A required upstream dataset must finish, plus any specified handoff delay, before the dependent dataset can begin. The team's spreadsheet adds all upstream durations together and sometimes promises a delivery that cannot complete.

**Build one dataset readiness assessor** that returns the earliest finish time, deadline status, and a deterministic chain of work that governs the completion time. You own the solution strategy. Deterministic, heuristic, LLM-assisted or hybrid approaches may be defensible; results must meet the exact contract and scale. No external APIs, services or model keys required.

## Supplied data and starter

- fixtures/datasets.csv: columns dataset_id,tenant_id,run_min,earliest_min.
- fixtures/links.csv: columns link_id,revision,op,tenant_id,prerequisite_id,target_id,lag_min.
- fixtures/queries.jsonl: one independent question per physical line, with some deliberately malformed records.
- batchpath/ and batchpath.py: functioning strict snapshot loader, request parser and CLI, plus unfinished readiness engine.
- scripts/ and tests/: green foundation checks, not complete acceptance checks.

CSV headers must contain exactly the named columns, in any order. IDs use case-sensitive ASCII letters, digits, underscore or hyphen, length 1–48 (request IDs length 1–128). CSV integer notation is canonical unsigned decimal, without a plus sign or leading zero other than zero. run_min: 1..1000000; earliest_min: 0..1000000000; revision: 1..2000000000; lag_min: 0..1000000. All times are whole minutes on one shared timeline.

An identical replay of a dataset ID is harmless; a conflicting definition invalidates the whole catalog. Identical copies of the same (link_id, revision) are harmless, but conflicting copies invalidate the catalog. Each link ID belongs to one tenant permanently, although newer revisions may change endpoints. Every upsert must reference existing datasets belonging to that tenant, even if later superseded. A retract row has blank prerequisite_id, target_id and lag_min. The numerically highest revision wins irrespective of CSV order. Different link IDs may describe identical endpoints and are separate, valid requirements. Invalid catalogs must fail before emitting any query results.

## One primary deliverable

Implement BatchPath.assess(query) in batchpath/engine.py with any justified preprocessing, preserving the CLI.

Example valid JSONL query:

~~~json
{"request_id":"plan-1","tenant_id":"ACME","target_id":"MART","deadline_min":50}
~~~

deadline_min is an actual JSON integer in [0, 1000000000000000], not a boolean, float or decimal string. Other required fields must be syntactically valid IDs. Extra fields may be ignored. Every query uses the same latest snapshot and is independent, even when request_id repeats.

A node without requirements finishes at earliest_min + run_min. Otherwise it cannot start before its local earliest_min or before *any* active prerequisite finishes plus its link's lag_min. Independent prerequisites run concurrently with no worker/capacity limits. Impossible circular requirements, including a self-dependency, block any target that needs them. Disconnected cycles do not block healthy targets.

For a deliverable target, return exactly this shape (illustrative values, not fixture answers):

~~~json
{"request_id":"plan-1","status":"ok","ready_min":42,"meets_deadline":true,"critical_chain":["RAW","CLEAN","MART"]}
~~~

The critical_chain lists a controlling chain, from its earliest upstream member through the target. At each node, look for an incoming requirement whose (prerequisite's ready_min + link lag_min) **equals** that node's earliest feasible start. If multiple incoming requirements tie, choose the case-sensitive lexicographically smallest prerequisite dataset ID. If no incoming requirement ties, the chain begins at this node because its own earliest_min controls its start. Even when a requirement merely ties the local earliest_min, prefer that requirement. Follow this rule upstream and reverse into root-to-target order. Repeated endpoints do not duplicate nodes in the chain.

For a blocked target, return exactly:

~~~json
{"request_id":"plan-1","status":"blocked","reason":"dependency_cycle"}
~~~

Malformed JSON, empty physical lines, wrong types, missing/out-of-range values or invalid IDs yield status invalid, reason invalid_query and request_id null (retain the ID when syntactically valid). A structurally valid query referring to an undeclared dataset in its specified tenant yields status invalid, reason unknown_dataset and the valid request ID. One bad query must not prevent processing later input lines. Print exactly one compact JSON object per physical query line, in input order, with no logs on stdout.

## Observable acceptance criteria

1. Correct finish times with parallel branches and local earliest starts at intermediate datasets.
2. Honor every active requirement, including multiple links with identical endpoints.
3. Highest revision and retraction semantics work independent of file order; superseded malformed records still reject the catalog.
4. Detect self cycles, multi-node cycles and downstream blocking, without affecting unrelated tasks.
5. Apply the specified deterministic tie-breaking chain, including ties to a local start restriction.
6. Deadline equality counts as on-time; queries are independent and result order matches input.
7. Validate bad catalog rows atomically and isolate malformed JSONL lines and tenant mismatches.
8. Handle very deep dependency chains and repeated queries without recursion-depth failures or traversing the whole catalog per query.

## Constraints

Production may contain 200000 datasets, 600000 link revision rows, 100000 queries and 200 tenants. There may be deep chains, wide fan-in, large shared prerequisites and isolated cycles. Prefer near-linear snapshot preparation with efficient reused answers and memory under roughly 512 MiB aside from input/output. A printed chain can itself be long; proportional work to output its members is acceptable. Python 3.11+ standard library only.

## Scope and out of scope

Implement the readiness assessment and preserve loader/parser contracts. Refactors and tests are allowed. No UI, network service, external SDK, persistence, real-time link updates, model serving or resource-limited scheduling.

## 60-minute AI-assisted interview instruction

You have **60 minutes**. You may use Claude Code, Codex, ChatGPT or other assistants; inspect the fixtures and code, select and defend an approach, review generated changes, implement incrementally and verify representative edge cases. Be prepared to explain correctness, time/space complexity and tradeoffs. The existing tests do not exercise the full requested feature.

## Commands

~~~bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 batchpath.py validate --datasets fixtures/datasets.csv --links fixtures/links.csv
python3 batchpath.py assess --datasets fixtures/datasets.csv --links fixtures/links.csv --queries fixtures/queries.jsonl
~~~

The assess capability is intentionally unfinished in the starter.