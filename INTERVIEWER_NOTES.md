# POST-PRACTICE ONLY — FreshClaim interviewer notes

**Evaluator material. Never open or copy to the candidate branch.**

## Intended underlying structure

This is a bounded **subset-selection optimization** coupled with a capacitated **time-window inventory feasibility** subproblem. Every batch contributes a supply quantity across the subset of fixed pickup times in its `[ready,expiry)` interval. An accepted order is an indivisible all-or-nothing demand at one instant; individual *units* within an accepted order may come from multiple lots. The global optimum is lexicographic over `(accepted_count, accepted_units, negative/sorted ID lex order)`.

The first trap is summing stock by SKU; another is considering each order independently. A greedy policy that accepts orders by earliest pickup, highest units, or ID cannot in general maximize completed-order count. Distinguish a subset selection from the feasibility of allocating its aggregate demands.

## Strong solution approaches

**A. Exact bounded subset search + earliest-expiry feasibility.** With at most 12 orders per basket, consider subsets in descending population count, then descending summed demand, and compare sorted IDs for ties. Prune subsets that cannot overtake the best objective. For a candidate subset, aggregate accepted-unit demand by pickup minute, sort minutes ascending and process inventory arrivals chronologically. Keep eligible lot capacities ordered by expiration; at each pickup, expire stock with `expiry <= pickup_min` and draw earliest-expiring eligible lots until the whole timestamp demand is covered or stock runs out. This works for *fixed pickup times and divisible lot units*: an exchange argument swaps later-expiring inventory consumed earlier with earlier-expiring inventory without making a future pickup less feasible. It is not correct to run this rule independently for each order while committing to a subset selection greedily.

For k<=12, full enumeration is O(2^k) subsets. A naive feasibility pass over L lots per subset costs O(2^k (L+k) log L), unacceptable for hot SKUs. Group orders by pickup time, memoize demand vectors, prune objective and simple capacity bounds, and build a per-partition ready-time index to ignore irrelevant lots. Further compress lots that yield identical feasible pickup-time ranges for the current basket, aggregating their units (at most O(k²) relevant eligibility ranges); calculate these totals via indexed/offline range counting or scan a limited filtered slice. Explain that efficient repeated queries on hot SKUs require serious preprocessing/retained summaries, not only a heap. Sorting 12 orders or enumerating 4096 masks is not the bottleneck versus scanning 500k lots for every mask.

**B. Exact small flow feasibility + subset search.** For one candidate subset, form a capacitated bipartite network from lots to distinct pickup-time nodes when the lot is usable at that time, with lot capacity and pickup demands. Max flow equals total accepted demand iff feasible. A large raw network per query is prohibitive; compress inventory intervals relative to at most 12 pickup times and reuse the compressed network. This is slower in practice than the chronological greedy check for this special eligibility geometry but straightforward to reason about, verify, and generalize. An ILP/SAT solver is an alternative if separately justified (not in the provided standard-library baseline).

**Oracle and proof.** For small random examples, enumerate chosen subsets and construct all feasible unit allocations or a tiny max-flow model. Compare feasibility, primary/secondary objective, exact tie set, and boundary behavior with the production algorithm. When proving earliest-expiry correctness, be explicit that a lot has *unit capacity across all pickups*, pickup times are fixed, and availability is a single contiguous time interval; relaxing any of these assumptions may break that strategy.

## Complexity and practicality

Let k <=12, L be lots in the queried store/SKU, and T<=k distinct pickup instants. Naive exact search has <=2^k candidates, each evaluated by O((L+T)log L) sorted arrival/expiry operations; this is an upper-bound baseline, not a production solution. Pre-sort lots at load by readiness and optionally expiry, O(total_L log total_L) time and O(total_L) retained space. With a basket-specific compression, aggregate each batch into its eligible consecutive-time interval; there are O(T²) interval types and feasibility can use aggregated supply. A naive per-request O(L*T) scan still fails 100 ms typical for very hot SKUs, and a 2-D time-index/range-aggregate or cached hot-partition summary is needed to accelerate repeated lookups. Subset objective computations cost O(2^k*k), ignoring feasibility. Memory and query latency need empirical evaluation on skewed distributions. No exact solution can promise 100ms for all adversarial 2m-lot/12-order cases in Python merely from the starter fixtures.

## Why naive AI solutions fail

- Sum of eligible lots at each pickup independently double-spends units used by earlier pickups.
- Sum of *all* lots ignores stock arriving after pickup and units expiring exactly at pickup.
- Greedy accept-highest-units violates the **count-first** objective; greedy accept-earliest can prevent two later complete orders.
- A greedy lot assignment based on lot ID or latest expiry can waste short-lived stock. If selecting all 12 orders is impossible, falling back to the first 11 is not necessarily optimal.
- Counting a duplicate lot declaration twice overstates inventory.
- Returning only the first feasible optimum candidate without lexicographic ID comparison loses a tie.
- Boolean `true` is an integer in Python (`isinstance(True,int)`); input parser intentionally guards this.
- A model may generate convincing but non-optimal allocations, violate half-open expiration, or omit distinct store/SKU partitioning.

## What a strong candidate discovers in the supplied data

The OAK/APPLE partition has a replay of `O-A1`, a zero-unit lot, a lot that expires at minute 7, and lots only ready after earlier pickup times. BER/MILK has a hard handoff at minute 8: the first batch cannot serve a minute-8 pickup. OAK/PEAR has different completion-count and demand-maximization incentives. TX/APPLE is a **known** partition with zero usable stock, not an `unknown_stock` error. The repeated `split` request ID does not consume stock from previous requests. Fixture requests include invalid booleans, duplicate order IDs, unknown SKU, malformed JSON, and an empty physical line.

## Hidden checks / cases to ask verbally

1. Inventory single lot 10 units usable at time 5: three orders of 6,5,5 at minute 5. Best subset is both fives, not the six; complete count outranks units.
2. One batch of 4 units usable at minute 2 but expiring at minute 4; one batch of 4 arriving at minute 4. Pickup 2 needs 4, pickup 4 needs 4: both are feasible; reverse allocation is not.
3. One lot 6 units ready at 5, a pickup at 4 with 6 and a pickup at 5 with 6: only the later order is feasible despite any catalog order.
4. Same count but unequal total units; pick higher summed units, not smaller ID.
5. Equal count and units; use sorted case-sensitive ID array ordering, independent of JSON array order.
6. Multiple lots with identical attributes but distinct IDs are additive; identical replay of one ID is not.
7. Empty basket is the unique optimum of count zero and units zero, even with no positive stock.
8. At time `expiry_min` the batch is unavailable; at time `ready_min` it is available. Zero-unit stock partition remains known.
9. Invalid bool for time/units, duplicate order ID, unknown partition only after well-formed payload, corrupt catalog row even if a duplicate of a legitimate one elsewhere.
10. A dozen orders with overlapping eligibility and a hot partition; force a realistic complexity explanation rather than trusting the fixture's size.

## Defensible alternatives

A bounded branch-and-bound optimizer with a flow-based feasibility oracle earns full correctness credit if it meets constraints. Tiny ILP formulations, a compiled helper, or precomputed cumulative capacity structures can be defended in design discussion, though the candidate deliverable must run with Python standard library only. An LLM can help generate tests or optimize code; arbitrary LLM allocation suggestions alone do not provide an exactness guarantee. If the candidate proposes a heuristic for sub-100ms while explicitly returning an uncertainty/approximation state, discuss that as a business alternative, but it does **not** satisfy this exercise's prescribed exact `ok` response.

## Recommended 60-minute prioritization

- **0–8 minutes:** inspect fixture, rephrase objective and fixed-time capacity constraints; identify count-first and end-exclusive semantics.
- **8–20:** implement a reliable single-subset feasibility check and test arrival/expiry and consumption order.
- **20–35:** implement bounded subset optimization, sorted stable tie-breaking, empty/infeasible cases.
- **35–48:** add counterexamples and independent small random oracle comparisons; run build/test/verify and full sample CLI.
- **48–60:** improve indexed inventory reuse/pruning where possible, quantify worst-case and hot-key latency, walk through design and tradeoffs.

## Walkthrough inspection checklist

Ask: How are inventory units accounted for across pickups? Why does chosen allocation preserve later feasibility? How is optimality proved given all-or-nothing orders? Where are tie rules enforced? What is the worst case with 500k lots for one SKU? Are zero-unit lots, duplicate deliveries and empty orders handled? Can rejected orders consume capacity accidentally? How did the candidate test AI-generated code independently? What constraints would invalidate their data structure if the customer later asked for arbitrary multi-time pickup windows or online reservation edits?
