# LockerLens — HARD One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

A delivery platform lets shoppers redirect parcels to self-service pickup lockers. Its current resolver scans every locker for every request. That is correct on a tiny sample and unusable at production scale.

You are given one immutable locker snapshot plus independent search requests. Build the in-process resolver used by the API tier. The required behavior is exact; the implementation strategy is yours.

## Supplied data

`fixtures/lockers.csv` contains `locker_id`, coordinates, status, maximum parcel size, available slots, queue minutes, and pipe-separated capabilities. `fixtures/queries.jsonl` contains one independent request per line with a shopper location, parcel size, required capabilities, maximum radius, and result limit. Locker capacity is not consumed across queries.

## Distance contract

Use the supplied `locator.distance.great_circle_meters(...)` helper as the exact distance definition. Ranking uses the full floating-point distance. Only after ranking should emitted `distance_meters` be rounded with `floor(distance + 0.5)`. Longitudes near `+180` and `-180` are geographically close.

## Eligibility

A locker is eligible only when `status == "active"`, `available_slots > 0`, it fits the parcel under `S < M < L < XL`, it contains every required capability token exactly, and its exact great-circle distance is within the query radius. `cold` does not match `cold-storage`.

## Result ranking

Rank eligible lockers by smaller exact distance, then smaller `queue_minutes`, then lexicographically smaller `locker_id`. Return at most `limit` lockers. If nothing qualifies, return a resolved result with an empty `lockers` array. Malformed JSON or invalid query fields produce one query-level `invalid_query` result and must not stop later queries.

## Acceptance criteria / traps

- Preserve query-file order and emit exactly one result per line.
- Results must not depend on locker row order, capability order, map iteration, or process hash behavior.
- Duplicate required capability tokens collapse to one requirement.
- Maintenance/offline lockers and active lockers with zero slots are ineligible.
- Size ordering is ordinal, not lexicographic.
- A locker exactly on the radius boundary is eligible.
- Ranking uses unrounded distance; rounded output must not create artificial ties.
- Identical coordinates are valid; break ties by queue then locker ID.
- Search correctly across the date line and near the poles.
- Latitude must be in `[-90,90]`, longitude in `[-180,180]`, and coordinates must be finite.
- Duplicate locker IDs, invalid snapshot fields, malformed/duplicate capability tokens, or empty IDs fail snapshot validation.
- Query integer fields must reject booleans and numeric strings.
- Diagnostics belong on stderr; stdout is a JSONL result stream.

## Production constraints

Design for roughly 8 million lockers, 1.2 million queries per immutable snapshot, at most 16 capability tokens, dense cities with hundreds of thousands of lockers inside 100 km, `limit <= 20`, radius `<= 200 km`, about 1.25 GB memory, and target p95 below 10 ms after preprocessing.

A production-credible solution should not scan all 8 million lockers per query, sort every qualifying locker when only a few are needed, or duplicate the full snapshot for every capability combination. Think about reusable search state, safe lower bounds, attribute filtering, and the small result limit.

## Expected deliverable

Implement `LockerFinder.resolve_all(...)` / `resolve(...)` in `locator/finder.py`, adding supporting code and focused tests as needed. Be prepared to explain preprocessing, pruning exactness, top-result extraction, complexity/memory, dense-city worst cases, and date-line/polar correctness.

## Run / verify

Python 3.11+; no third-party dependencies.

```bash
bash scripts/test.sh
bash scripts/build.sh
bash scripts/verify.sh
```

After implementation:

```bash
python3 locker_search.py search --lockers fixtures/lockers.csv --queries fixtures/queries.jsonl
```

## Scope / out of scope

In scope: immutable snapshot loading, validation, exact geographic eligibility, deterministic top results, query-level errors, tests, and scale reasoning. Out of scope: consuming capacity, writes, live mutation, road routing, traffic, persistence, authentication, distributed coordination, external APIs, and UI.

## 60-minute AI-assisted interview instruction

You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or similar tools. Inspect the fixture and starter code yourself first. Restate eligibility and ranking, implement incrementally, verify risky geographic and ordering boundaries, and reserve time to explain the production-scale design. A one-shot solution that merely scans the sample correctly is not sufficient.
