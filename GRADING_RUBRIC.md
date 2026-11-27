# POST-PRACTICE ONLY — ReviewDesk grading rubric (100 points)

| Dimension | Points | Evidence |
|---|---:|---|
| Problem decomposition | 10 | Distinguishes eligibility, capacity, maximum coverage, ordered coverage preference, and reviewer assignment; identifies queue independence. |
| Algorithm / data structure choice | 20 | Uses a justified exact global assignment strategy that can rearrange earlier assignments; prioritization is mathematically sound (not priority sum). |
| Functional correctness | 25 | Maximum coverage (12), preferred covered set (8), valid capacity/eligibility witness and complete output (5). |
| Complexity and scalability | 15 | Bounded per-queue work (7), avoids quota expansion or exhaustive search when wasteful (4), representative measurement and credible bounds (4). |
| Edge cases | 12 | Zero capacity/empty options/empty input (3), duplicate declarations and normalization (2), deterministic ASCII ordering and input permutation (3), failed search integrity and no cross-call mutation (4). |
| Verification | 8 | Adds targeted tests (4), compares small random instances with a trusted exhaustive oracle or equivalent (2), runs baseline and documents results (2). |
| Code quality | 5 | Clear ownership of state, readable functions and minimal dependencies. |
| Walkthrough and tradeoffs | 5 | Explains correctness and failure modes, complexity and any compromises. |
| **Total** | **100** | |

Score partial credit within each row. A happy-path first-fit or priority-sorted greedy implementation without reassignment is capped at 55; exhaustive search with no credible production path or an implementation that knowingly misses key optimality/scale requirements is capped at 60. Invalid assignments are not rescued by a high covered count. Award equivalent credit for independently justified alternative approaches. No credit for hard-coded fixture answers.
