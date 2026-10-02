# GRADING RUBRIC — 100 points

## 1. Problem decomposition and contract modeling — 12 points

- 5: Correctly separates normalization, searchable surfaces, per-surface prefix matching, per-term deduplication, and final ranking.
- 4: Represents the ordered tie-break rules explicitly rather than relying on incidental iteration order.
- 3: Identifies immutable preprocessing versus per-query work and the difference between fixture correctness and production credibility.

## 2. Search/index strategy — 20 points

- 8: Uses a reusable structure that narrows work to plausible matching prefixes instead of scanning every surface in the locale.
- 6: Handles `max_edits <= 2` with bounded state/work and supports pruning of impossible search states.
- 4: Has a credible way to obtain only a small number of best descendants/candidates for hot prefixes instead of materializing every completion.
- 2: Accounts for locale partitioning and highly skewed locale/prefix distributions.

Full credit does not require one specific implementation. An exact alternative with comparable asymptotic behavior is acceptable.

## 3. Matching and ranking correctness — 20 points

- 5: Correct insert/delete/substitute semantics against non-empty prefixes.
- 4: Chooses the best qualifying prefix for a surface correctly, including completion length.
- 4: Reconciles canonical plus alias surfaces so each term appears once with its best evidence.
- 4: Applies final term ranking exactly: edits, popularity, completion, canonical normalized text, term ID.
- 3: Returns the original display strings and exact output shape/order.

## 4. Complexity and scalability — 15 points

- 5: Gives honest startup, memory, and per-query complexity in terms of query length, edit budget, branching, visited search states, and requested limit.
- 4: Avoids full-locale scans and full sorting of all qualifying terms.
- 3: Discusses hot one/two-character prefixes and the larger frontier produced by edit budget 2.
- 3: Discusses memory tradeoffs for 37M searchable surfaces and the 1.25 GB budget.

## 5. Edge cases and validation — 12 points

- 2: Inactive terms and exact locale scoping.
- 2: Duplicate/conflicting alias IDs and duplicate term IDs.
- 2: Multiple aliases / identical normalized surfaces / cross-term collisions.
- 2: Unicode code-point length versus UTF-16 code units, shared normalization.
- 2: Boundary mistakes near the start/end of typed text and deeper-prefix tie resolution.
- 2: Empty/invalid query handling and deterministic row-order independence.

## 6. Verification and tests — 8 points

- 4: Adds focused tests for typo boundaries, alias dedupe, ranking ties, inactive terms, and locale isolation.
- 2: Includes at least one adversarial case that a naive prefix-only or first-match implementation gets wrong.
- 2: Runs the supplied baseline checks and verifies JSONL behavior without corrupting stdout.

## 7. Code quality — 5 points

- 2: Clear responsibilities and readable data structures.
- 1: No accidental quadratic work hidden in convenience code on the hot path.
- 1: Deterministic comparators/keys are centralized and auditable.
- 1: Changes preserve the supplied loader/normalization contract unless there is a justified bug fix.

## 8. Explanation and tradeoff defense — 8 points

- 3: Can explain why the approach is correct for all three ranking layers: prefix, surface/term, final top results.
- 2: Can explain the most likely pathological workload.
- 2: Can distinguish a correct interview implementation from the additional engineering needed for the stated production throughput.
- 1: Gives a defensible answer on whether an LLM/heuristic belongs in the critical lookup path.

## Score caps

- A correct fixture-only implementation that scans every canonical/alias surface for every query scores at most **58/100**.
- A solution that is fast but gets alias reconciliation, prefix boundaries, or deterministic ranking wrong scores at most **60/100**.
- A happy-path implementation that handles only exact prefix matching or substitutions scores at most **50/100**.
- A one-shot AI-generated solution with weak verification and no credible scale argument should not exceed **55/100** even if the checked-in examples happen to pass.
