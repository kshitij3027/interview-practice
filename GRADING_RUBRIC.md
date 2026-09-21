# GRADING RUBRIC — 100 points

This rubric is for evaluator use after the practice session.

A solution that works only on the checked-in happy path, rescans the event corpus per query, or ignores repeated-credential/boundary semantics should not score above roughly **58/100**, even if its fixture output looks plausible.

## 1. Problem decomposition and model — 15 points

- 5: Correctly identifies that queries are independent historical snapshots but can share work within a region.
- 4: Models the rolling interval exactly as `(as_of - W, as_of]` and distinguishes event count from distinct credential count.
- 3: Separates dataset-level validation from query-level invalid results.
- 3: Preserves original query output order even if processing order changes internally.

## 2. Algorithm / data-structure choice — 20 points

- 8: Uses a credible reusable strategy across many queries rather than rescanning the corpus for each query.
- 5: Maintains per-client repeated-credential state correctly as events enter and leave the active window.
- 5: Uses a credible top-k structure or equivalent technique that avoids sorting every active client for every query.
- 2: Design remains deterministic under input-row reorderings.

## 3. Correctness under the contract — 25 points

- 5: Exact boundary handling: left exclusive, right inclusive.
- 4: Exact retry deduplication and conflicting `event_id` validation.
- 5: `request_count` and `distinct_credentials` remain correct for repeated credentials during both insertion and eviction.
- 4: Ranking precedence is exact: distinct desc, requests desc, client ID asc.
- 3: Unknown regions and invalid `k` values return per-query invalid results and do not stop later queries.
- 2: Timestamp offsets are normalized by instant.
- 2: Empty windows and `k` larger than the number of active clients behave correctly.

## 4. Complexity and scalability — 15 points

- 5: Explains preprocessing/sorting cost and why offline ordering of queries/events is useful.
- 4: Update and leaderboard extraction costs are appropriate for the stated production scale.
- 3: Addresses skewed clients / repeated credentials and active-window memory rather than assuming uniform traffic.
- 3: If using lazy heap invalidation, addresses stale-entry growth with a defensible compaction/rebuild strategy or equivalent bounded-memory design.

## 5. Edge cases and adversarial behavior — 10 points

- 2: Multiple occurrences of one credential where only the oldest expires.
- 2: Same-timestamp events and deterministic ranking.
- 2: Event exactly on either window boundary.
- 2: Shared credential IDs across different clients remain independent.
- 2: Out-of-order query times and shuffled event rows.

## 6. Verification / testing — 7 points

- 3: Adds focused tests for repeated-credential eviction and boundary semantics.
- 2: Adds tests for ranking ties / deterministic output.
- 2: Uses the supplied fixture plus at least one adversarial custom fixture or focused unit test.

## 7. Code quality — 4 points

- 2: State is factored clearly enough to reason about insertion, eviction, and ranking updates.
- 1: Error handling and output formatting are clean.
- 1: No unnecessary framework/infrastructure overhead for the one-hour task.

## 8. Explanation and tradeoff defense — 4 points

- 2: Can explain the chosen state transitions and why the result is correct.
- 1: Can explain the top-k tradeoff and memory behavior.
- 1: Can identify what would change for live streaming versus this immutable historical batch.

## Scoring caps

- **~58 max:** fixture-oriented or happy-path solution that materially ignores scale, exact boundaries, or repeated-credential eviction.
- **~45 max:** rescans all events independently for each query and sorts every client each time, even if outputs are otherwise correct.
- **~35 max:** distinct counting implemented with a plain set that removes a credential when any one occurrence expires.
- **~30 max:** incorrect query ordering or material timestamp-boundary errors.
