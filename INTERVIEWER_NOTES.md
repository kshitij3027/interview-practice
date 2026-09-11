# POST-PRACTICE ONLY — Interviewer Notes

## Intended underlying structure
This is a repeated stabbing-query / best-active-rule problem over a catalog hierarchy. Each product has a short ancestor chain, while each applicable product/category scope can own many promotion intervals. The candidate must combine hierarchy preprocessing with efficient temporal lookup and a single explicit precedence comparator.

A strong exact design precomputes category ancestry/depth once, indexes promotions by target scope and region class, and gives each scope an interval-aware structure capable of returning the best active candidate at a timestamp without scanning the entire history. Several structures are defensible: interval trees augmented with the best-ranked candidate, segment trees over compressed endpoints for an immutable snapshot, balanced trees plus prefix/suffix summaries when interval assumptions are exploited, or an offline sweep if all queries are known and batch semantics are acceptable. Direct-product scopes and category ancestor scopes are then compared with one contract-ordered comparator.

## Strong solution approaches
- Immutable per-scope interval indexes with query-time lookup across the product scope plus O(depth) category scopes.
- Endpoint compression / segment-tree style preprocessing where memory remains acceptable for the observed rule distribution.
- Offline event sweep over sorted query timestamps, maintaining active promotions for each relevant scope, if the candidate explicitly discusses why batch-only processing differs from the stated online p95 shape.
- A simpler sorted-interval structure may be acceptable for the hour if the candidate proves correctness and clearly identifies hot-root worst cases plus a production upgrade path.

## Complexity expectations
A strong target is roughly O(total input preprocessing + indexed promotion build) startup, O(depth × lookup_cost) per query, and memory linear or near-linear in catalog/promotions rather than in every product × ancestor × promotion combination. Copying inherited promotions down to every descendant product is not viable at the stated scale.

## Why naive approaches fail
- Scanning 1.5M promotions per request is immediately disqualifying for the target throughput.
- Scanning every historical promotion on a hot root category can still violate p95 even if rules are grouped by category.
- Materializing all inherited rules per product can explode memory.
- Sorting candidates by discount or by specificity before priority violates the business contract.
- Treating RFC3339 strings lexically rather than timestamps breaks offset-equivalent instants.

## Subtle traps / hidden checks
- `as_of == starts_at` is active; `as_of == ends_at` is inactive.
- A high-priority root promotion beats a lower-priority direct-product promotion.
- At equal priority, direct product beats every category regardless of category depth.
- Among equal-priority category rules, deepest applicable category wins before region specificity.
- Exact region wins over `*` only after priority and target specificity/depth are tied.
- Later start wins before lexical promotion ID.
- Two timestamps with different offsets but the same instant must behave identically.
- Exact duplicate promotion rows are deduped; conflicting same-ID definitions fail validation.
- Category cycle, missing parent, unknown product/category target, and invalid discount/window fail validation.
- Reordered category/product/promotion rows must not change results.
- Deep hierarchy should not recurse unsafely in production; iterative or controlled traversal is preferable if depth could grow beyond fixture norms.

## What the fixture is designed to reveal
- `p-100` has competing root/electronics/computing/laptops/gaming/product rules, including exact-region and wildcard product rules.
- One laptop query lands exactly on a promotion end boundary.
- Coffee has two same-priority, same-depth, same-region overlapping windows with different starts.
- Running shoes exercise depth versus exact-region ordering.
- The exact duplicate root promotion tests replay deduplication.

## Likely AI-agent failure modes
- Implementing a global linear scan because the fixture is tiny.
- Writing precedence as an ad hoc sequence of conditionals with one criterion swapped.
- Assuming direct product always wins regardless of priority.
- Comparing timestamps as strings.
- Building a huge product-to-promotions inheritance map.
- Adding a cache keyed only by product and region while forgetting `as_of`.
- Over-engineering a complex interval structure before locking down semantic tests.

## Recommended 60-minute prioritization
1. Restate applicability + precedence and write focused comparator/boundary tests.
2. Ensure catalog validation and ancestry/depth semantics are understood.
3. Implement a correct resolver with clean scope separation.
4. Improve/index the temporal lookup enough to demonstrate a credible production direction.
5. Add targeted adversarial tests and explain complexity/skew tradeoffs.

## Alternative defensible designs
A candidate may explicitly choose a simpler exact implementation for the interview fixture, then describe a production interval index. That can score well if semantics are correct and the production upgrade is concrete. An offline sweep is also defensible when framed as a batch-mode variant. Approximate or LLM-based candidate generation is hard to justify in the critical path because the contract is exact, the data is structured, and latency is tight, but a candidate can discuss such tools for campaign authoring or diagnostics outside resolution.

## Walkthrough inspection points
- Ask the candidate to state the precedence tuple in order without reading code.
- Ask what happens on a hot root category with 100k intervals.
- Ask why the chosen temporal index returns the best active rule, not merely any overlapping rule.
- Ask whether exact-region/wildcard indexes are merged before or after target specificity and why.
- Ask how memory scales if category depth doubles.
- Ask for the behavior at an exact `ends_at` boundary.
- Inspect whether tests cover one case where the intuitively "more specific" rule correctly loses because priority is higher elsewhere.
