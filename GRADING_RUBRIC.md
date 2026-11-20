# SignalWatch — Grading Rubric (100 points)

**POST-PRACTICE ONLY — never show before the 60-minute interview.**

| Dimension | Points | What earns full credit |
|---|---:|---|
| Customer framing and decomposition | 12 | Separates catalog correctness, normalization, per-tenant retrieval, match semantics, ranking, output guarantees and tradeoffs; identifies scale bottleneck before coding. |
| Algorithm and data-structure selection | 22 | Selects a multi-pattern search strategy with query work related to message length and matches rather than all signatures; discusses build, memory and tenant indexing; correctly supports shared prefixes and duplicates. |
| Matching and result correctness | 24 | Exact contiguous normalized token matching; overlap, earliest token offset, per-signature distinctness, tenant/revision semantics, priority/offset/ID sorting, full total before limit. |
| Scaling and complexity defense | 14 | Useful complexity bounds in terms of catalog size, token count and occurrence/output cardinality; handles pathological common signatures/repeats without repeated quadratic work; considers memory and caching. |
| Edge-case robustness | 10 | Covers empty inputs, punctuation, retractions, duplicate phrases, bound checks, invalid lines, tenant isolation and malformed catalogs. |
| Testing and verification | 10 | Meaningful targeted unit/integration tests, independent oracle on tiny catalogs, fixture runs, negative tests, checks actual outputs and documents tradeoffs. |
| Code quality and explanation | 8 | Readable, maintainable changes and coherent walkthrough of AI-generated code; can describe alternative designs and failure boundaries. |
| **Total** | **100** | |

**Caps:** brute-force/per-signature scan that ignores scale: max **55/100** regardless of correct small fixture results. Happy-path-only matching with missing validation, overlap or ranking: max **58/100**. A nonworking or hallucinated integration cannot receive correctness points. A solution using AI is judged by verified behavior, not prompting fluency. Partial correct implementations receive proportional points; do not reward hidden assumptions.
