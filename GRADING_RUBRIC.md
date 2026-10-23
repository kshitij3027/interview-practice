# POST-PRACTICE ONLY — MirrorTrace 100-point grading rubric

**Evaluator-only. Do not open before completing the 60-minute candidate exercise.**

## Scorecard (100 points total)

| Dimension | Points | What to inspect |
|---|---:|---|
| Customer problem decomposition | 10 | Identifies exactly what a fingerprint match means, correct filters and global ranking, why the naive per-query scan cannot satisfy scale, and separates image review from automatic enforcement. |
| Filtering correctness | 18 | Correct market isolation, other-seller exclusion, half-open lifetime, minimum risk score, valid and absent markets, duplicate replay semantics, and empty results. |
| Fingerprint distance and result ordering | 18 | Exact 128-bit differing-bit count, inclusive radius 0–3, no false negatives, unique listings, exact top-`limit` globally, correct risk/time/ID tie-breaking, and stable output independent of source order. |
| Index design and complexity | 20 | Goes substantially beyond scan-all; candidate explains completeness of candidate generation, bounds cost relative to corpus/query count, and builds/reuses an immutable index. Full points require a correctness argument, not only a clever-looking code path. |
| Large-scale skew and memory awareness | 10 | Handles/mitigates identical or near-identical fingerprints appearing hundreds of thousands of times; avoids excessive per-query materialization where feasible; accounts for index overhead, query selectivity, and 2.5 GB memory. |
| Defensive behavior and edge cases | 8 | Distinct error treatment for bad snapshots vs malformed requests, integer/hex validity, upper/lowercase hex, boundary times, extremes of `limit` and radius, repeated request IDs, and safe absence of results. |
| Verification and tests | 10 | Independently tests a small brute-force oracle versus optimized output, adversarial examples, correctness invariants, input order variations, and at least basic timing/memory instrumentation. |
| Walkthrough and design tradeoffs | 6 | Explains why deterministic/heuristic/LLM/hybrid choice fits exactness; gives expected complexities, limitations, measurements, and justified next improvements. |

**Total = 10 + 18 + 18 + 20 + 10 + 8 + 10 + 6 = 100.**

## Calibration

- **Excellent (90–100):** exact output on varied adversarial fixtures; provably complete nontrivial index; sound filtering and ties; measured/scoped skew and memory costs; tests and lucid walkthrough.
- **Strong (75–89):** correct and efficient mainstream cases with robust retrieval, perhaps an unoptimized worst-case skew or incomplete performance evidence.
- **Acceptable (60–74):** mostly correct and reasoned strategy but noticeable edge-case or scalability gaps. Does not achieve full intended production assurance.
- **Partial (35–59):** simple working matcher with important missing guarantees or a full-scan strategy that does not meet scale. Happy-path-only or brute-force solutions must not exceed **55**, even with clean code; a correctness-complete scan-all with exceptional tests but no scalable design must not exceed **58**.
- **Failing (0–34):** nonfunctional output; invalid distance calculations; silent false negatives/incorrect precedence; no credible validation.

## Hidden-evaluator check themes

1. Gold-standard randomized exhaustive matcher on tiny snapshots, compared exactly for many queries.
2. One-, two-, and three-bit differences placed across different parts of a 128-bit signature; check that valid candidates are not lost by shortlist generation.
3. Many indistinguishable fingerprints spanning markets, sellers, risk scores, and active intervals; request `limit=1` still requires the globally best eligible row.
4. Identical listing replay rows vs conflicting reuse, case-sensitive listing IDs, and uppercase hexadecimal fingerprint representations.
5. `as_of_ms` equal to a listing's first or last timestamp; exclude the requesting seller from all of its rows.
6. Rank ties: distance first, then risk descending, then first_seen descending, then listing_id ascending (ASCII case-sensitive).
7. `max_bit_errors` 0 and 3; `limit` 1 and 20; unknown market; all candidates below min-risk; fewer than requested matches.
8. Input row reordering, repeated query IDs, independent malformed requests followed by valid requests.
9. Performance thought experiment or benchmark: millions of rows, millions of queries, dominant common signatures, heavy memory pressure. Ask for p95 and peak RSS, not speculative universal timing claims.

## Alternative designs and scoring fairness

A reliable deterministic index, a verified heuristic that provably cannot miss candidates, or a hybrid with an exact deterministic final verification path can all earn full credit. Do **not** award correctness credit to an approximate semantic/embedding search simply because its outputs look convincing. An LLM is not required.

A small brute-force reference implementation may be valuable for tests, but cannot be the production retrieval path. Ignore cosmetic UI/polish; judge correctness, efficient indexing, verification, and the candidate's explanation. Do not leak this document, expected approach, or hidden checks to the candidate branch.
