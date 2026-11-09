# POST-PRACTICE ONLY — TransitShield Interviewer Notes

**Do not show this document or anything under `evaluator/` to the candidate until after practice.**

## Underlying structure

There are exactly **3 × 4 × 3 = 36** possible global level combinations. Each induces an equivalence relation on the original queried trips. For each plan, count frequencies of triples (generalized station/route/sector, slot/hour/day/week, fare/family/all), suppress every group with count below k, reject if nothing remains or suppression exceeds the budget, and compute the lexicographically comparable exact key `(loss,suppressed,geo_level,time_level,fare_level)`. This is a **multidimensional data-cube / group-count optimization with range-selection queries**, not a classification problem. The production challenge is answering many arbitrary original-time subranges with repeated scopes and varying k, weights, and budget.

## Strong approaches and complexity

1. **Reference algorithm:** deduplicate trip IDs on input, use station and fare mappings, filter original trips by sector and half-open time range, iterate all 36 plans, create counters of generalized triples, sum the frequencies of cells with count < k, check feasibility and choose the exact best tuple. For n selected trips and g distinct groups, straightforward per-query time O(36(n+g)), memory O(n+g) on top of the snapshot. Correct and useful to validate the specification, but far too slow if used for every production query.
2. **Reusable range indexes:** per sector, for each of 36 views, key by generalized group and retain original sorted slots (or compressed per-slot prefix frequencies). For each query, count matching rides per group in [L,R) via two bisections or prefix lookups. Counts are exact despite partial generalized buckets. A per-sector prefix count of rides by original slot quickly identifies empty windows. Query cost remains O(36 · number_of_groups_visited · log S) for sorted-slot lists (S <= 672) and worst-case heavy sectors may be costly. Discuss memory bounds; dense 672-entry prefix arrays for every group may be excessive.
3. **Offline batch optimization:** group queries by sector, reorder windows to incrementally update group frequencies for each view, and maintain count-of-count summaries that answer arbitrary k suppression totals efficiently. Then restore original query order. This is more sophisticated and not expected to be production-finished in 60 minutes; candidates should defend update costs and skew.
4. Memoize plan statistics for identical (sector,L,R,k) independently of weights/budgets; recompute only final loss comparisons. Bound cache size. If choosing heuristic or LLM-assisted plan generation, a proof of safe pruning or exact verification is still needed for optimum/privacy correctness.

## Why naive approaches fail

- Full scan of 1.2M rides × 36 plans × 70k queries requires trillions of visits; even just scanning all rides for every query is untenable.
- Optimizing information loss greedily or assuming loss is monotonic when increasing generalization is unsound: a coarser view retains more groups and may increase the release term while decreasing suppression.
- Grouping by generalized time before filtering **leaks trips outside the original report window**.
- Using different generalization levels per group violates the globally uniform policy. Small-group individual deletion is forbidden.

## Hidden checks and subtle traps

- k-1 group is entirely suppressed; k group is fully kept. All-suppressed is invalid even if suppressed count <= budget.
- Different hours: slots 3 and 4. Different days: slots 95 and 96. Arbitrary from_slot/until_slot can cut through the middle of one generalized hour/day.
- Duplicate trip T108 in fixture counts once; a conflicting T108 is snapshot-invalid regardless of query sector or time. File order must not matter.
- A 0-trip window => empty, a 1-trip window with k >= 2 => no_release. Do not confuse those states.
- With four zero weights and penalty 0, tie-breaking prioritizes **suppressed count** before level tuple. Worst tie occurs across all 36 plans.
- Repeated request IDs are unrelated queries; JSON booleans and floats are not integers, unknown sectors use a different reason from malformed request.
- Input ID values up to length 128 for request_id, up to 48 in CSV; no non-ASCII identifiers.
- Response exact fields include records; failed release uses null levels/loss and zero released/suppressed, not a fabricated selection.
- No grouping across sectors, even with a coarse geographical level; original filtering happens first.

## What the supplied data should teach

BAY has many time-adjacent trips and three routes, sparse Coast has four rides far apart, VAL has shared fare-family and route patterns; T108 repeats exactly. Slots 95/96 are an exact day boundary, slot 500 is distant; request IDs repeat with distinct windows. Example oracle results (not candidate-visible): `release-bay-morning` first query selects records=21, released=17, suppressed=4, levels (0,2,2), loss=324; `release-bay-strict` records=21, levels (2,2,1), released=21, loss=462; `release-val` levels (1,2,2), zero loss; `release-quiet` empty; `release-few` no_release.

## Recommended 60-minute prioritization

- 0–10 min: inspect records and acceptance; formalize original window, grouping and exact objective.
- 10–22 min: one-plan grouping reference, k boundary, suppression and retained checks.
- 22–38 min: all 36 options, exact tie, empty/no_release, formatted results.
- 38–48 min: write and run adversarial tests including partial time bucket and zero-weight cases.
- 48–60 min: demonstrate indexing/memoization or provide credible production design with complexity, and explain what AI-generated code was verified.

## Walkthrough

Ask candidate to prove no small group is exposed, show why filtering precedes generalization, demonstrate a tie, and explain source deduplication. Probe proposed production indexing/memory costs for dense sectors, variable k, and arbitrary narrow windows. Ask what was verified independently versus accepted from AI output, and what remains incomplete.
