# POST-PRACTICE ONLY — INTERVIEWER NOTES

## Intended underlying problem structure
Each pool has a time-varying free-capacity function formed by base capacity, effective capacity changes, reservation starts, and reservation ends. Equal-time deltas should be combined before evaluating the state, yielding piecewise-constant capacity segments. Eligibility can be indexed by region and SKU, then filtered by exact capability-tag containment.

The temporal task is to find, for each eligible pool, the earliest aligned start whose whole booking interval stays at or above the requested unit threshold. The main systems insight is to reuse the immutable timeline and avoid rechecking unchanged ranges for every possible five-minute start.

## Strong solution approaches
A strong exact implementation preprocesses sorted change points into constant-capacity segments and uses an indexed range query that can test the minimum capacity across a booking interval. When a candidate fails, the implementation should be able to locate a violating segment and advance beyond it rather than retrying every five-minute position. An implementation based on compressed segments plus a range-minimum index is one strong option; block decomposition or threshold-aware indexes for very hot pools are also defensible.

For a pool with C change points, a credible target is roughly O(C log C) preprocessing and logarithmic interval checks, plus work proportional to the number of violating runs skipped. Eligibility lookup should avoid touching unrelated pools.

## Why naive approaches fail
- Scanning every pool per query wastes repeated region/SKU/tag structure.
- Trying every five-minute start and rescanning the entire requested duration multiplies long search windows by long durations.
- Rechecking raw reservations for every candidate ignores that the snapshot is immutable.
- A dense 90-day five-minute matrix across all pools exceeds the stated memory budget.
- Looking only at capacity at the booking start or finish misses interior dips.

## Subtle traps and evaluator checks
1. A capacity drop exactly at `finish_at` does not invalidate the booking.
2. A reservation ending exactly at `start_at` frees units immediately.
3. Multiple changes at one instant are cumulative and input-row order must not matter.
4. Exact replayed event/reservation IDs apply once; conflicting definitions fail validation.
5. Different RFC3339 offsets representing the same instant must behave identically.
6. A window can have enough capacity at both ends but fail in the middle.
7. When starts tie, price precedes pool ID; spare capacity is not a tie-breaker.
8. Capability matching is exact-token set membership, not substring matching.
9. A long continuous low-capacity run should not require checking every five-minute candidate independently.
10. Combined reservation load and maintenance changes can make an otherwise individually valid baseline oversubscribed.
11. Queries are independent; resolving one must not consume capacity for later queries.

## Alternative defensible designs
Compressed segments with block minima, per-threshold feasible-run caches, or a hybrid strategy that uses a heavier index only for hot pools can all be reasonable. A heuristic or approximate strategy is acceptable only when its correctness tradeoff is stated explicitly; no model or external API is needed for the exact contract.

## What should be discovered from the supplied data
- `west-a100-01` has a maintenance dip from 09:30 to 10:00 layered over reservations.
- `west-a100-02` is cheaper but loses capacity at 09:45 and later carries a four-unit reservation.
- `west-a100-04` has two simultaneous capacity changes whose net effect matters, plus a reservation boundary at 09:20.
- `west-a100-03` lacks the `ib` tag despite having high nominal capacity.
- Replayed `e9` and `r9` records must not double-apply.
- One query expresses an instant using a non-UTC offset.

## Likely AI-agent failure modes
A one-shot agent may expand the tiny fixture into five-minute slots, apply simultaneous deltas sequentially, forget reservation-end deltas, treat `latest_finish` as exclusive, choose the first map-iteration winner instead of honoring tie-breaks, deduplicate by full row rather than logical ID, or mutate capacity after answering a query.

## Recommended prioritization
First lock down time and eligibility semantics. Then build reusable free-capacity timelines, implement correct one-pool earliest-window resolution, add global pool selection, and finish with targeted boundary tests plus a complexity discussion for the hottest pools.

## Walkthrough inspection points
Inspect the candidate's per-pool representation, same-time coalescing, full-interval safety check, failure-skip logic, complexity for 200k change points and a seven-day request, eligibility filtering, exact-boundary tests, an interior-dip test, and any cache key used for repeated query shapes.
