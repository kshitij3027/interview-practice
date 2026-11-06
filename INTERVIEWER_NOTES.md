# POST-PRACTICE ONLY — CryoRelay Interviewer Notes

**Evaluator-only content. Do not copy into the candidate branch, tests, filenames, comments, or commit history.**

## Intended underlying structure

This is a **time-dependent directed reachability / earliest-arrival route problem** in a scheduled-event graph, with a **bounded number of edges**, waiting-window constraints, and lexicographic objective. Services are directed edges between hubs with fixed departure/arrival times. At most six services may be used. The transfer policy applies at intermediate hubs, not before the first service. For cold cargo at an uncooled hub, a state arriving earlier does **not always dominate** a later arrival at the same hub: the earlier sample may exceed its 45-minute holding window before an outbound departure. This is a key discriminator between a naive graph shortest path and a correct label/event-state approach.

## Strong solution approaches

1. Pre-index services by origin and departure time (and optionally cold eligibility), discarding zero-slot services from routing while retaining catalog validation. Treat each selected service's **arrival event** as a distinct state `(service_id, number_of_legs)`. For each state, its arrival time and hub are fixed; retain the lexicographically best service-ID path for that exact state/leg count. Expand from a state only to eligible departures at that destination hub in the interval `[arrival + transfer_min, arrival + 45]` if the shipment is cold and the hub lacks cold storage; otherwise departures after `arrival + transfer_min`. The initial expansion uses `ready_min` with no transfer buffer. All chosen service times strictly increase. Evaluate all feasible terminal states under `(arrival, legs, tuple(service_ids))` and return the minimum. This is exact but a simple search may expand the same service state repeatedly from different prefixes; use per-layer state deduplication and sorted-departure interval lookups.
2. For better repeated-query performance, use layered event reachability or dynamic programming over time-indexed service events. At each layer and hub, store eligible inbound arrival labels with the lexicographically best path prefix for the same service-event/leg state; support a range-min lex-prefix query on allowable inbound arrival times for each outbound departure. A cold-equipped hub has a prefix range (any sufficiently early arrival), while a warm hub with cold cargo has a bounded arrival interval. This avoids enumerating every pair of intersecting services at a hot hub. Process layers up to `max_legs`, using compact integer IDs and immutable catalog indices. Make sure path comparison is on the **full** path, not on local IDs alone.
3. An alternative defensible technique is query-specific time-expanded state search with careful dominance rules. Monotonic arrival pruning is safe only when no upper dwell bound applies and ties cannot affect the required lexicographic optimum; otherwise preserve distinct arrival labels. A hybrid heuristic is acceptable only if it can **certify** the chosen exact optimum within the stated contract, or clearly explain where it forfeits correctness points.

## Complexity

Let `H` be hubs, `S` eligible scheduled services, `K <= 6` the maximum legs, `R` the count of service transitions examined for a query. Index-building by sorting departures is `O(S log S)` time and `O(S + H)` space. A straightforward deduplicated expansion over service-event states can take `O(K(S + R))` time and `O(K S)` path/state space in the reachable subgraph; **R can be quadratic** for one popular hub if every inbound event connects to every outbound event. Using departure and arrival indices with interval/range-min retrieval allows a layered sweep with roughly `O(K S log S)` worst-case time per broadly reachable query and `O(K S)` labels (plus path storage), with lower typical cost by limiting exploration to reachable hubs and service windows. The practical 150 ms p95 goal may require query caching, per-origin-time indexes, restricted temporal scans, or a compiled implementation; don't assert that a pure-Python full scan meets p95 without measurement. A materialized all-pairs service-to-service transition graph can exceed RAM under skew.

## Why naive approaches fail

- FIFO or earliest-arrival-per-hub only: false when a cooler is unavailable and the 45-minute dwell ceiling expires. A later arrival at the same hub can still catch a service.
- Greedy earliest outgoing arrival: a local best can miss a better final arrival and overlook maximum leg budget.
- Enumerate all itineraries / all pairs of services: combinatorial blowup under parallel departures and high-degree hubs.
- Build a single static shortest path ignoring scheduled departures: invents impossible connections.
- Minimize leg count first: violates primary earliest-arrival objective.
- Compare only arrival/leg count, taking any tie: fails required lexicographically smallest full ID sequence.
- Treat queries as actual bookings: consumes available slots and makes query order affect results.

## Data observations and subtle traps

The fixtures deliberately include an exact duplicate service (`R-101`), parallel outbound services (`R-101`/`R-118`), a zero-slot service (`R-120`), a warmer transfer hub (`ALT-Q`), a late service that cannot be caught with insufficient transfer time, a cycle, one cold-disabled shortcut (`R-111`), arrivals at exact transfer boundaries, a refrigerated alternate hub (`CHILL-X`), missing destinations, zero-hop trips, invalid request lines, and repeated request IDs. In particular, `R-114` reaches `ALT-Q` early but cannot wait until `R-115` on a cold shipment; `R-117` arrives there later and can make that same departure. Check that the candidate discovers this rather than collapsing to one arrival per hub. The fixture also has an attractive later direct delivery versus an earlier multi-leg delivery; earliest arrival beats convenience.

## Hidden checks to run after implementation

- Same hub: empty path at exact ready/deadline, even if service cycles exist.
- No path, capacity zero, cold-disabled service, and max-legs exhaustion.
- Cold at a warm hub with `(depart - previous_arrival) == 45` allowed; 46 rejected; minimum transfer exact equality accepted.
- Earlier arrival at warm hub **not** enough; later arrival must survive pruning to catch a service within the dwell window.
- Intermediate transfer at refrigerated hub may wait arbitrarily long.
- Parallel distinct services with equal arrival and number of legs: full lexicographic service-ID sequence wins, independent of file order.
- Path with 3 legs arriving before 1-leg path must win; if arrival ties then 1 leg wins.
- Cases at week boundary, self-loop service, repeated route IDs (identical accepted/conflicting fatal), malformed CSV, malformed JSON line isolation, `true` where an integer is required, duplicate query IDs.
- Many arrivals and departures at one hot hub to catch quadratic pair enumeration; repeated queries must not alter available slots.

## Alternatives and AI failure modes

An LLM can help inspect schemas and generate test fixtures, but an LLM call to choose each itinerary cannot certify exact schedule feasibility and stable tie order at this scale. Other valid implementations: label-setting with a schedule-aware index, bounded-layer DP over service events, or custom interval minima. Treat a carefully justified deterministic algorithm as full-credit. AI agents often infer `cold_storage` applies to the *whole itinerary* instead of only dwell at intermediate hubs, confuse `<= 45` with `< 45`, subtract transfer buffer at the origin, treat capacity as shared across requests, collapse to the earliest hub arrival, or introduce sorting by arrival then ID without full-path comparison. Demand independently computed tests.

## Recommended 60-minute pacing

- 0–8 min: read README, inspect fixture, paraphrase invariants and ask about departure/arrival and cold-holding semantics.
- 8–18 min: model event states and explain ranking and pruning constraints; get the first feasible itinerary plan.
- 18–42 min: implement index, valid expansion/path reconstruction, secondary ordering.
- 42–52 min: targeted tests for 45-minute counterexample, transfer boundaries, ties and zero slots; run CLI.
- 52–60 min: demonstrate outputs, complexity, skew mitigation and failure-mode review.

## Walkthrough focus

Ask the candidate why the earliest arrival at a hub can be insufficient, how they select the best *complete* path (rather than locally best next leg), what happens at exactly 45 minutes, how they avoid high-degree Cartesian expansion, why a cheaper or fewer-leg route need not be optimal, how repeated IDs/invalid records behave, and which guarantees an LLM or heuristic could violate. In addition, ask them to name an adversarial test they wrote without seeing the evaluator checks.
