# SkyParcel — HARD 60-minute AI-assisted customer interview

## A message from the customer

Hi! We operate a fleet of delivery drones. Our compliance team receives **waypoint review** requests from partner dispatchers before individual takeoff decisions. Each review asks which local operating restrictions cover one waypoint at one time and altitude. Restrictions can be concave, contain exempt interior areas, overlap at different priorities, and expire on different schedules. The current service checks every restriction for every waypoint and sometimes incorrectly approves a point directly on a boundary.

We need a component that returns the **highest-ranked matching restrictions**, with the same answer regardless of catalog row order. This is a *lookup and audit* feature, not a flight-plan generator or flight-control system. Please deliver a runnable, explainable implementation and describe your performance tradeoffs. You own the technical approach; deterministic, heuristic, LLM-assisted, and hybrid designs are allowed, but outputs must meet the exact contract. No credentials, network service, or extra packages are required.

## Supplied data

- `fixtures/zones.jsonl`: one JSON restriction per physical line (unordered, with one harmless replay). Every record has `zone_id`, `region`, `priority`, `active_from_ms`, `active_until_ms`, `altitude_min_m`, `altitude_max_m`, `outer`, and `holes`.
- `fixtures/queries.jsonl`: one waypoint review per physical line, including invalid examples. Queries need not be ordered by time. Each valid query contains `request_id`, `region`, `x`, `y`, `at_ms`, `altitude_m`, and optional `limit` (default `3`).
- `airspace/io.py`: strict structural input parsing and error isolation; `airspace/engine.py`: the unfinished lookup component; `review.py`: CLI; `tests/`: starter tests and `scripts/`: local commands.

Coordinates are integer points on a **fictional planar grid**, not latitude/longitude. A ring is a list of at least three vertices `[x,y]`. Its closing edge, from last vertex to first, is implied: do **not** repeat the initial point. Edges can be diagonal, horizontal, or vertical, and may include collinear intermediate vertices. Rings may have either winding direction. Each restriction has one `outer` ring and zero or more `holes` (rings). The upstream authoring system **guarantees** each ring is simple with positive enclosed area, all holes are strictly inside the outer ring, and holes never touch/overlap each other or the outer ring. You do not have to detect crossings or repair invalid geometric topology.

All IDs (`zone_id`, `region`, `request_id`) are case-sensitive ASCII letters, digits, `_`, `-`, 1–48 characters (request IDs up to 128). JSON numbers must be actual integers (never booleans or numeric strings). Vertex coordinates `x,y` are in `[-10^9,10^9]`; catalog/query times in `[0,10^12]`; altitude in `[0,100000]`; priority in `[0,1000]`. Each zone requires `active_from_ms < active_until_ms` and `altitude_min_m < altitude_max_m`. Each ring has 3–1000 vertices, and each zone has at most 20 holes. Extra object keys may be ignored. Each JSONL physical line must contain one JSON object. Blank catalog lines are invalid.

An identical replay of a `zone_id` with the same parsed business fields counts once. Reusing an ID with different fields, invalid data, or an invalid catalog line **invalidates the whole snapshot** before any query output. Invalid query lines receive an isolated error response, and later lines are still processed. Duplicate `request_id` values are separate, independent queries.

## Your one primary task

Implement `AirspaceReview.select(query)` in `airspace/engine.py` (and supporting files if useful). For each valid request, select restrictions satisfying **every** condition:

1. The zone has exactly the query's `region`.
2. Its time window contains `at_ms`: `active_from_ms <= at_ms < active_until_ms`.
3. Its altitude interval contains `altitude_m`: `altitude_min_m <= altitude_m < altitude_max_m`.
4. The waypoint is inside its outer boundary **or on any outer edge or vertex**, and is **not inside or on the boundary of any hole**. A hole excludes its boundary. The exact point, not a rounded or approximate position, determines membership.

Rank all eligible zones by **higher priority first**, then **smaller net enclosed area first** (outer area minus the areas of all holes), then **lexicographically smaller case-sensitive `zone_id`**. Area comparisons must be exact; ties are valid. Return at most `limit` zone IDs in ranked order, with no duplicates. For no matches, return an empty list. Query and catalog ordering must not alter results.

The existing `review.py` emits exactly one compact JSON result for every physical query line, in original order:

- Valid: `{"request_id":"q01","status":"ok","zone_ids":["zone_a","zone_b"]}`.
- Invalid: `{"request_id":"q_bad","status":"error","error":"invalid_request"}`. If the request ID itself cannot be read as a valid ID, use JSON `null`.

The CLI's parser validates data; you may refactor it, but preserve the observable output/error contract. The starter's `select` currently returns `[]` for all queries **on purpose**; it is not the desired solution. Starter tests validate only parsing, execution, and scaffolding, not full correctness.

## Realistic production constraints

- Around **300,000 zones** per regional catalog snapshot and **4 million total boundary vertices**; dozens of separate regions.
- Around **12 million waypoint reviews/day**, with up to **30,000 zones sharing broad overlapping bounds** in dense urban regions. Most points match no restrictions; a minority may match dozens.
- A **2 GB process memory budget** and **p95 under 15 ms for typical waypoint lookups after catalog loading**. The tiny fixture is not a performance benchmark.
- Multi-hour catalog preprocessing is unacceptable; explain startup cost, memory, and worst-case behavior. A full scan on every query will not meet the stated scale.
- Correctness is mandatory for boundaries, concavity, holes, negative/large coordinates, region/time/altitude limits, duplicate catalog deliveries, ranking ties, and query errors. Partial credit is available for a correct baseline plus a defensible plan to scale.

## Scope, acceptance, and interview conduct

Build only the waypoint restriction lookup. Do **not** perform route planning, geodesic/latitude-longitude conversion, dynamic live catalog edits, policy interpretation, or drone actuation. Do not assume rings are rectangles or convex. Decide what you should precompute and how to avoid examining unrelated zones; explain exactness and complexity, including dense overlapping cases.

You have **60 minutes** and **should use AI assistants as you would on the job**. Read the data and contract before coding. Tell your interviewer your proposed approach, ask questions where real customer requirements are ambiguous, implement a useful vertical slice, run tests, add your own boundary and scale tests, and explain compromises. A one-shot implementation without verification is not the goal.

From this directory:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 review.py --zones fixtures/zones.jsonl --queries fixtures/queries.jsonl
```

Only the first three commands are starter-baseline checks. `verify.sh` checks the CLI's line/error structure; it **does not** assert complete zone matching. You should write additional tests before considering the problem solved.
