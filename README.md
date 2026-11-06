# CryoRelay — HARD 60-Minute AI-Assisted Customer Interview

## A request from the customer

Our clinical logistics team transfers temperature-sensitive tissue samples between laboratories and hospitals using independently scheduled couriers. A sample may change vehicles at intermediate hubs, but each courier has a published departure time, arrival time, temperature capability, and remaining slots. Some hubs have refrigerated storage; others can hold a cold sample outside a controlled vehicle for **at most 45 minutes**. A spreadsheet-based dispatcher currently chooses the first arrival it sees at each hub and sometimes produces an impossible itinerary.

Build a **trustworthy transfer planner** that returns the earliest feasible delivery itinerary for an individual sample, subject to shipment-specific restrictions. The team needs reproducible answers and an explanation of your performance choices. You decide the implementation strategy: deterministic, heuristic, LLM-assisted, or hybrid is your call, provided the observable guarantees hold. No SDK, credentials, model, or network service is required.

This is **one primary problem**, not a CRUD app or a live fleet-dispatch system. Read the data before deciding on an approach.

## Supplied data and starter

- `fixtures/hubs.csv`: `hub_id,transfer_min,cold_storage`. `transfer_min` is the required minutes between **arrival on an inbound service** and departure on the next outbound service. `cold_storage` is exactly `true` or `false`.
- `fixtures/services.csv`: `service_id,from_hub,to_hub,depart_min,arrive_min,cold_enabled,slots`. Times are **absolute minute offsets within one fixed operating week**; there is no wrapping or recurring timetable. `cold_enabled` marks an independently temperature-controlled courier; `slots` is the number of *remaining* shipment slots, not a value to decrement when a query is answered. CSV rows are unordered, and one exact repeated delivery is present.
- `fixtures/requests.jsonl`: one independent shipment request per physical line, including malformed records, repeated request IDs, and a zero-distance shipment. Fields: `request_id,origin,destination,ready_min,deadline_min,max_legs,requires_cold`.
- `relay.py`: validated snapshot loader, query parser, streaming JSONL CLI, and a deliberately unfinished `RelayPlanner.plan(request)` method. You can change or split this file as needed.
- `tests/test_starter.py` and `scripts/`: baseline smoke checks (not a full acceptance suite).

All hub and service IDs are case-sensitive ASCII `[A-Za-z0-9_-]`, 1–48 chars; request IDs may have up to 128. CSV integers are canonical unsigned base-10 (`0` or no leading zeroes). Hub transfer time is 0..180. Service times are integers with `0 <= depart_min < arrive_min <= 10080`; slots are 0..999. JSON time fields are **actual** integers 0..10080 (not booleans, numeric strings, or floats), `max_legs` is 1..6, and `requires_cold` is a JSON boolean. The ready time may equal the deadline. Extra JSON keys are ignored. All referenced hubs must exist.

Identical repeated hub or service IDs with identical business fields count once. Conflicting reuse of an ID, missing hub references, invalid CSV values or headers, or invalid service timing **invalidates the entire snapshot** before any query output. A malformed JSONL request instead produces one isolated error line and does not block later requests. A repeated request ID is a *new, independent query*.

## The required capability

Implement `RelayPlanner.plan(request)` in `relay.py`. A shipment may travel along **zero to `max_legs` scheduled services**. Every selected service must have `slots > 0`; for a `requires_cold=true` request, each selected service must also have `cold_enabled=true`.

An itinerary is feasible only when all of these conditions hold:

1. Its first service departs from `origin` at or after `ready_min`. The initial pickup has **no intermediate-hub transfer buffer**.
2. Every subsequent service departs from exactly the previous service's destination hub, at or after `previous_arrive_min + hub.transfer_min`. The hub transfer time is charged **only between services**, never at the origin before the first service or after the last service.
3. For a cold-required shipment, whenever an intermediate hub has `cold_storage=false`, its **waiting time** from inbound arrival until next outbound departure is at most **45 minutes inclusive**. Minimum transfer time still applies. Cold-equipped hubs have no maximum waiting duration; non-cold shipments have no maximum waiting duration at any hub.
4. The last service arrives at `destination` at or before `deadline_min`. Arrival exactly at the deadline is acceptable. There are no implicit journeys, inferred routes, or mid-service boarding.
5. If `origin == destination`, the empty itinerary is valid, arrives at `ready_min`, and is always preferable to a journey. The destination need not have refrigeration to complete delivery.

Among feasible itineraries, choose, **in this exact order**: (a) earliest arrival time, (b) fewest services, (c) lexicographically smallest sequence of case-sensitive `service_id` strings. A path with a better arrival time wins even if it needs more changes. Query results never reserve capacity or modify the snapshot. Itineraries may revisit hubs; suppressing a revisited hub is not automatically valid.

For a feasible request return exactly this JSON-object shape (the values are illustrative, **not** a supplied fixture answer):

```json
{"request_id":"demo","status":"ok","arrival_min":160,"legs":["S-7","S-19"]}
```

For a request with no feasible itinerary, return:

```json
{"request_id":"demo","status":"unreachable","arrival_min":null,"legs":[]}
```

The CLI writes **one compact JSON object per physical request line** in original order. The supplied parser handles malformed requests by writing `{"request_id":null,"status":"invalid_request","error":"..."}` (recovering an otherwise valid request ID when possible). Invalid snapshot input fails before writing any request results, reports a diagnostic on stderr, and exits nonzero. Do not print progress messages on stdout. Preserve these interfaces when changing the starter.

## Scale and performance constraints

The checked-in fixture is representative, not production-sized. Production planning uses approximately **250,000 distinct scheduled services**, **30,000 hubs**, and **150,000 independent shipment requests per day**, with `max_legs <= 6`, very uneven hub traffic, and many overlapping departures. Target **768 MB working memory** and **150 ms p95 for typical requests after one snapshot load** on a single worker. Do not expand a 10,081-minute grid for *every* hub *and* request or enumerate all possible itineraries. A full snapshot scan on every request is not a defensible production strategy. Describe worst-case behavior when a hub has unusually many services.

Important sources of complexity to investigate include parallel services, zero-slot departures, overnight offsets (the week is absolute), exact transfer boundaries, per-hub holding limits, arriving earlier at a hub but being unable to wait for a later departure, arrival/leg-count ties, repeated IDs, and loops. The supplied starter tests intentionally do **not** tell you how to implement the planner.

## Expected deliverable and verification

Deliver a runnable implementation through `RelayPlanner.plan`, any justified preprocessing, and additional tests you derive. Be prepared to demonstrate a few sample queries; discuss correctness, time and space costs, invalid inputs, and failure modes. No frontend, HTTP API, real-time capacity reservation, model training, live location feed, or external integration is in scope.

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 relay.py --hubs fixtures/hubs.csv --services fixtures/services.csv --requests fixtures/requests.jsonl
```

`build.sh` checks syntax, `test.sh` runs six baseline smoke tests, and `verify.sh` exercises the CLI. **Passing starter tests is not sufficient to satisfy the customer contract**; the starter's `not_implemented` answer is only a runnable starting state.

## The 60-minute interview

**You have 60 minutes. AI assistance is explicitly encouraged.** Use Claude Code, Codex, ChatGPT, or other tools the way you would on the job, but validate code and outputs yourself. Inspect the fixture and clarify assumptions, choose and explain a strategy, implement incrementally, write meaningful tests beyond the starter, and walk through tradeoffs. You are responsible for correctness and for explaining the implementation, not for memorizing a prescribed algorithm.
