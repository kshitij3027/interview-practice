# POST-PRACTICE ONLY — GridPulse 100-point grading rubric

Use only after the candidate's 60-minute exercise. Weight exactness, strategy, and scale well above superficial CLI success.

| Dimension | Points | Strong evidence |
| --- | ---: | --- |
| Customer decomposition and precise contract | 13 | Resolves latest revision semantics, interval boundaries, peak timing, exact area, query independence, and validation boundaries. |
| Algorithm / data-structure selection | 21 | Chooses indexed reusable site representation; supports arbitrary-window maxima and area queries; motivates alternatives and limits. |
| Functional correctness | 24 | Handles overlapping sessions, session moves/cancels, partial clipping, all-zero windows, earliest peak, exact integer area and tie-breaking. |
| Complexity / scalability | 16 | Meaningful preprocessing and query bounds; handles a highly skewed site, large timestamps, memory, and large query counts without per-query full scans. |
| Edge cases / adversarial robustness | 12 | Simultaneous boundaries, zero draw, replay/conflicts, shuffled revisions, site isolation, no-activity sites, malformed input, large totals. |
| Verification and testing | 8 | Runs all starter checks; adds adversarial assertions and a small independent oracle or randomized differential comparison. |
| Code quality | 3 | Clear invariants, limited accidental complexity, readable division of parsing/indexing/query behavior. |
| Walkthrough and tradeoffs | 3 | Correctly explains why solution works and where it fails; can justify kept AI code. |
| **TOTAL** | **100** | |

## Score calibration

- 90–100: exact, indexed, well-tested, production-aware, clearly defended.
- 75–89: strong correct core with a few edge or scale gaps.
- 60–74: substantial working portion but gaps in precision, validation, or scalability.
- 40–59: some working behavior, often only happy path or query-by-query scans.
- 0–39: little functional behavior or fundamentally incorrect semantics.

**Hard cap:** A solution that rescans all active sessions for every query, uses a millisecond-by-millisecond loop, ignores cancellations/revisions, or handles only happy paths must not receive more than **58/100**, even if the supplied fixture looks plausible. A correct small-data implementation with a coherent documented index upgrade may reach the 60s but cannot score highly under the scalability dimension without a demonstrated credible design. Failure to separate malformed-query errors from catalog-fatal errors loses corresponding points regardless of algorithm.

## Evaluation protocol

Run the candidate's original and new tests; inspect exact JSON keys/types; review at least one hand-computed non-event-aligned window; challenge the time/space complexity for 400,000 sessions at one site; request a counterexample to the candidate's own approach. Do not evaluate solely from the sample fixture or the assistant's prose.
