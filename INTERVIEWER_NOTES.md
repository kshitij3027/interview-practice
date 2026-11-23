# POST-PRACTICE ONLY — ProofSpan interviewer notes

**EVALUATOR-ONLY. Never publish this file, grading content, intended data structures or tests in candidate history.**

## Underlying problem structure

This is **versioned interval selection plus union-by-vendor, sweep-line event aggregation, and fast range-summary queries** on a sparse time axis. The business distinction is *distinct vendors* (not probes/observations). There is one immutable timestamp-coverage function per scope. Each query selects a threshold `k` in 1..4 and summarizes `[from_ms,until_ms)` in exact duration units, earliest unsafe instant, longest contiguous unsafe run and number of unsafe runs.

## Strong approach A: event sweep + range-summary index

1. Validate all CSV input, select highest revision per observation ID, ignore retracted rows. Latest upserts may refer to a changed probe. Map each live observation through probe -> (scope,vendor).
2. For each scope, sort boundary events `(start,+1,vendor)`, `(end,-1,vendor)`; ensure events at the same millisecond are applied together. Maintain an active **reference count for each vendor**, and adjust distinct active-vendor total only for 0-to-1 and 1-to-0 transitions. This prevents multiple probes and overlapping intervals from overcounting. Add implicit 0 and 1e12 domain boundaries or an equivalent gap treatment.
3. Produce sorted, disjoint elementary spans where distinct-active-vendor count is constant. For each threshold k = 1..4, store a summary for each elementary span: length, covered length, earliest uncovered offset, longest uncovered run, uncovered prefix length, uncovered suffix length, gap count, and whether fully uncovered. Combine adjacent summaries associatively; when both adjacent edges are uncovered, their border gaps are **one**, not two. Longest uncovered may cross the combine boundary, so take `max(left.longest,right.longest,left.suffix+right.prefix)`. Earliest uncovered is from left if available, otherwise after left's duration plus right's offset.
4. Build an efficient summary range index over the elementary spans (e.g. segment tree, other associative range structure). Binary-search for the query endpoints, clip the first/last elementary spans and combine the interior summaries. Since each elementary segment is wholly safe or unsafe for a fixed k, clipped summaries are simple. Queries then cost O(log M) per threshold, independent of raw observation count. Correctly handle windows that begin before the first event or finish long after the last event.

Let N be latest live observation count, M <= 2N + 2 unique boundaries, Q audit count and K=4. Sorting/sweeping costs O(N log N) time across scopes; building K indexes O(KM) time/space for segment trees (excluding Python representation overhead); queries O(log M) after choosing k. Memory budget requires compact records and caution with Python object overhead at multi-million scale.

## Strong approach B: offline batched queries or compressed gap-run summaries

A legitimate alternative groups audits by `(scope,k)`, builds sorted safe/unsafe run boundaries and cumulative safe time, and uses binary searches plus a range-max index of *complete unsafe runs* to find the worst gap; first/last partial runs are clipped. Prefix sums and run counts answer covered time and gap count. Another approach sorts queries and maintains sweep state offline, with separate range machinery for longest-gap answers. Design must explain how clipped runs merge and why query time is sublinear in raw evidence volume. A small-scope exhaustive oracle is appropriate for verification, **not** as the production algorithm.

A deterministic algorithm is a natural fit because the customer semantics are exact and structured. A model may help inspect noisy metadata or generate tests, but using an LLM to guess coverage durations is not defensible. A hybrid is acceptable if the exact range computation remains authoritative.

## Why naive approaches fail

- Testing every upsert interval against every audit costs O(NQ), potentially hundreds of billions of comparisons.
- Sorting all probes' intervals then counting overlapping rows overstates vendor redundancy.
- Summing covered segments without merging adjacent *uncovered* pieces overcounts gaps and undercounts longest gaps.
- A dense array indexed by millisecond is impossible for a 1e12 range.
- A precomputed global safe/unsafe flag is wrong: thresholds vary from 1 to 4, and coverage varies by scope.
- "Latest row in file" and deduplication by probe rather than observation ID are incorrect revision and identity rules.

## Subtle traps / hidden checks

1. Two probes from vendor ORION concurrently cover `[5,10)` but contribute only one independent witness; multiple observations from one probe also contribute one.
2. Half-open edges: an observation ending at t does not contribute at t; another starting at t does. Simultaneous ends/starts should not create phantom gaps or extra duration.
3. In `fixtures/observations.csv`, `E001` revision 2 shortens its window despite revision 1 appearing later; `E011` is retracted; `C004` revision 2 moves the observation to a different probe/vendor; `W005` is retracted.
4. Scopes `LEGACY` (no probes), unused probe `EA5`, and `k=4` at a scope with at most three distinct witnessing vendors.
5. Entirely uncovered windows outside evidence, including near 1e12; a window clipping an uncovered segment at both ends should report exactly **one** gap of its window's length.
6. If vendor membership remains below k during a handoff or evidence record boundary, the unsafe period stays a *single* gap even though elementary spans change.
7. A query clipped exactly at a boundary can have zero-length exterior segment; don't create empty gap runs.
8. Cross-scope reuse of a vendor ID is not transferable evidence; counts are per scope.
9. Exact duplicate observation revision rows are retries; conflicting same revision and malformed superseded upserts fail the *whole* snapshot, before any stdout.
10. A valid audit ID survives a request error; repeated audit IDs never deduplicate independent queries. JSON `true` is not integer 1.

## What to discover by inspecting fixtures

One vendor has multiple probes at EAST, and several intervals overlap. A few records are deliberately out of order or withdrawn. The `site_name` column is display metadata, not a grouping key; scope/probe/vendor IDs define attribution. Coverage changes sparsely and the same audit scope occurs in several overlapping windows. Some physically separate probes share one vendor and should not increase the redundancy count. The fixture contains long uncovered periods and a scope with no probes.

## Recommended 60-minute prioritization

- **0–8 minutes:** Read README and inspect fixtures; articulate exact vendor-witness, revision and gap semantics; identify scope and k as query dimensions.
- **8–18 minutes:** Resolve latest live observations; create small manual cases and design a sparse representation.
- **18–38 minutes:** Implement correct coverage computation; favor working exactness on representative data before acceleration.
- **38–51 minutes:** Add efficient query indexing or offline batch summaries; check window clipping and adjacent gap merging.
- **51–60 minutes:** Test retractions, cross-probe duplicates, exact boundaries, full-domain sparse query, invalid inputs and explain complexity/tradeoffs.

## Walkthrough inspection points

Ask the candidate to show why two probes from the same vendor never count twice, why the latest record rather than row order wins, and how threshold-specific safety is represented. Inspect a query spanning a very long idle period and one starting inside a gap. Request a complexity argument for 2 million revisions and 300,000 audits; verify no raw-evidence scan per audit is required. Ask which invariants are tested and how the candidate checked an AI-generated implementation for correctness. Inspect whether the CLI still preserves one line per physical audit, atomic catalog failure and correct error precedence.
