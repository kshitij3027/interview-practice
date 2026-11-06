# PulseRank evaluator rubric — POST-PRACTICE ONLY

**Total: 100 points.** Assess the candidate's actual implementation and 60-minute explanation, not superficial code length. Accept any defensible architecture that satisfies the contract.

| Area | Points | What earns full credit |
|---|---:|---|
| Problem decomposition and invariants | 14 | Correctly distinguishes physical rows, revision identities, latest logical calls, scope partitioning, snapshot errors, and independent queries; states nearest-rank and half-open semantics precisely. |
| Algorithmic and data-structure choices | 23 | Prepares reusable per-scope data for exact time-range order statistics and tie-aware slowest selection; avoids per-query full scans/sorts; explains indexing vs batch offline options. |
| Exact query correctness | 27 | Correct latest-live-revision population and scope/window membership (8), nearest-rank p50/p95 with ties and no interpolation (9), strict budget breaches (4), deterministic slowest ID (6). |
| Scale and complexity | 12 | Credible preprocessing/query time bounds, memory estimates, skew and large-value handling, realistic optimizations, and awareness of Python object overhead. |
| Edge cases and error semantics | 9 | Cancellation without upsert, out-of-order revisions, duplicate/conflicting replay, zero-length and boundary queries, invalid CSV/JSON types, empty subsets, and snapshot atomicity. |
| Verification and testing | 9 | Adds focused adversarial automated tests, compares randomized small cases with a straightforward oracle, verifies CLI line ordering and error isolation, runs baseline commands. |
| Code quality and safety | 3 | Clear interfaces, deterministic output, no unnecessary external dependency, maintainable code and error handling. |
| Walkthrough and tradeoff defense | 3 | Can explain why the approach is correct, where it may break, and how AI-generated code was validated. |
| **Total** | **100** | |

**Scoring caps:** A happy-path solution that scans/sorts every eligible observation for each query is capped at **58/100**, regardless of polished tests or UI, because the customer has 250,000 investigations and severe scope skew. A solution with only correct counting/thresholds but missing percentile or revision semantics is capped at 55. A solution that returns approximate percentiles without explicit justification or violates observed exact outputs is capped at 50. Incomplete production-scale optimization may still score strongly if the design, exactness, and tradeoffs are sound and candidly explained.

**Interviewer prompts:** Ask for a single-service skew stress estimate, complexity of two arbitrary time-window percentiles, how an edited request moving regions is counted once, the behavior at a time boundary, and a deterministic tie test. Inspect source and test results; do not assume green starter tests validate feature behavior.
