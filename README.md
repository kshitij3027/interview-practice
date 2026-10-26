# YardPulse — HARD 60-minute AI-assisted customer interview

## Customer / business context
A container-terminal operator coordinates temporary **joint-handling groups** of freight containers. A link indicates that two containers must be handled as part of the same coordinated movement. Links can be activated, deactivated, and reactivated as crane plans change; several independent links can connect the same containers, and a group may contain alternative paths. The operator needs to answer questions about *historical* groups without recreating the yard state from the beginning for every question. The existing prototype becomes unusable with millions of events and out-of-order investigation requests.

You own the technical approach. Deterministic, heuristic, AI-based, and hybrid designs are permissible, but every returned result must satisfy the exact contract. No credentials or external APIs are required.

## Supplied data
- `fixtures/yards.csv`: `yard_id,max_group_kg`. The mass threshold applies to the **entire connected group** in that yard, not to each container. Multiple yards are independent.
- `fixtures/containers.csv`: `container_id,yard_id,gross_kg`. Every container is permanently assigned to one yard; its gross mass never changes in this snapshot.
- `fixtures/links.csv`: `link_id,left_id,right_id`. A link joins two *distinct* containers in the same yard. It is undirected. Two different link IDs may join the same pair; both remain independently active or inactive. Identical replays of a link definition, including reversed endpoint order, count once; conflicting reuse is invalid.
- `fixtures/events.csv`: `event_id,occurred_ms,sequence,link_id,state`. A state is `open` or `close`. A row **sets the absolute active state** of the named link; it is not an increment/decrement. Setting an already-current state is a harmless no-op. An identical replay of an event ID counts once, even when placed elsewhere in the file; conflicting reuse invalidates the snapshot. Distinct events may not share `(occurred_ms,sequence)`. Events are applied in ascending `(occurred_ms,sequence)` order regardless of file row order. Before any event, every link is closed.
- `fixtures/queries.jsonl`: one independent investigation request per physical line, not necessarily chronological. Each valid record has a nonempty `request_id` (at most 128 characters), `kind` (`group` or `connected`), and `as_of_ms`. `group` requires `container_id`; `connected` requires `left_id` and `right_id`. Request IDs may repeat and do not imply caching or deduplication.

All catalog IDs use 1–48 case-sensitive ASCII letters, digits, `_`, or `-`. CSV numeric values are canonical nonnegative base-10 integers (no signs or leading zeroes) up to 10^12; `gross_kg` must additionally be at most 10^9. Query `as_of_ms` must be a JSON integer in `[0,10^12]`, **not** a boolean or numeric string. Extra query fields may be ignored. Catalog references must exist. Duplicate yard or container IDs, conflicting link/event replays, self-links, cross-yard links, invalid CSV values, and duplicate ordering pairs fail the entire snapshot before any query results.

## Primary customer request
Implement the historical group resolver in `yardkit/engine.py`, changing other starter files if your approach requires it. Return one compact JSON object on stdout for every query line, in the **original** input order. For a query at `as_of_ms = t`, apply **all** deduplicated events whose `occurred_ms <= t`, including every event at the exact millisecond (in sequence order). Queries do not change state. Two containers belong to the same handling group when they are joined by a chain of currently active links; a container with no active links forms a one-container group.

For `group`, return exactly these fields:

```json
{"request_id":"r-1","status":"ok","as_of_ms":180,"yard_id":"WEST","component_id":"C-01","container_count":3,"gross_kg":33000,"over_limit":false}
```

The values above illustrate the shape only. `component_id` is the **lexicographically smallest case-sensitive container ID** in the group (not necessarily the requested ID); `container_count` counts unique containers; `gross_kg` is the sum of each member's gross mass exactly once; `over_limit` is true iff that sum is **strictly greater** than the group's yard threshold.

For `connected`, return exactly:

```json
{"request_id":"r-2","status":"ok","as_of_ms":180,"connected":false}
```

The two containers are connected to themselves, regardless of active links. Containers in different yards are never connected.

## Observable acceptance criteria
- Every physical query line gets exactly one JSON result; diagnostics belong on stderr. Invalid lines do not stop later queries.
- Bad JSON, non-object values, missing/invalid fields, invalid ID formats, unsupported kinds, or invalid timestamps return `{"request_id":null,"status":"invalid","reason":"invalid_query"}`; preserve a valid nonempty request ID when recoverable.
- A structurally valid query mentioning an unknown container returns `status:"invalid",reason:"unknown_container"`, retaining `request_id`. Queries involving different known yards resolve normally with `connected:false`.
- An unlinked container belongs to its own group. Groups can merge and **split again** when links close; the minimum-ID leader, member count, and mass must reflect the historical instant, not the latest snapshot.
- Alternate paths and distinct link IDs between the same endpoints matter. Closing one link does not necessarily split a group. Reopening restores it. Repeated opens/closes do not create extra memberships.
- Events at the same millisecond are all effective for a query at that millisecond; those after the queried millisecond are not. Input order must not change results.
- Totals use exact integers; mass equal to the threshold is **not** over the limit. Repeated query IDs are separate queries. Tie-breaking by ID is case-sensitive.
- No query may mutate state seen by another query. Results must be independent of request order, CSV row ordering, and hash iteration.

## Production constraints
One immutable snapshot may contain **250,000 containers**, **500,000 link IDs**, **3 million link-state events**, and **400,000 historical queries** across 60 yards. A few yards and link IDs dominate the data. Query times move arbitrarily backward and forward, and densely connected groups may contain many alternative paths. Aim for approximately **1.5 GB memory** and **under 30 ms typical p95/query after snapshot preparation**. These are engineering targets, not fixture benchmark guarantees. Scanning all previous events or rebuilding an entire yard's groups independently for every query is not a credible production design. Discuss preprocessing, time/space complexity, and skew in your walkthrough.

## Scope and deliverable
In scope: historical group and connected answers, exact mass/count/leader and threshold behavior, robust validation and per-line recovery, focused adversarial tests, and a justified scalability plan. Out of scope: changing link membership definitions, real-time network ingestion after load, actual crane scheduling, distributing across machines, UI, authentication, and persistence. Do not modify supplied fixture semantics to simplify the problem.

## Setup / run / verification
Python **3.11+**, standard library only:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 yardpulse.py validate --yards fixtures/yards.csv --containers fixtures/containers.csv --links fixtures/links.csv --events fixtures/events.csv --queries fixtures/queries.jsonl
```

After implementing the resolver:

```bash
python3 yardpulse.py resolve --yards fixtures/yards.csv --containers fixtures/containers.csv --links fixtures/links.csv --events fixtures/events.csv --queries fixtures/queries.jsonl
```

The starter loader, command line, sample data, and basic tests are operational. The historical resolver intentionally reports `not_implemented` for valid queries; the green starter tests do not establish feature correctness.

## 60-minute AI-assisted interview instruction
**Timebox: 60 minutes.** Use Claude Code, Codex, ChatGPT, or other AI tools just as you would on a customer engineering problem. Read the data and contract before coding, identify ambiguities and assumptions, choose an approach, implement incrementally, run verification and your own targeted tests, then explain correctness, efficiency, tradeoffs, and any AI-generated code that you retained. A plausible result on the fixture alone is not enough to meet the stated scale and boundary requirements.
