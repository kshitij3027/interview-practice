# POST-PRACTICE ONLY — CostCanopy Grading Rubric

**Total: 100 points.** Judge implementation and explanation, not fixture output alone. A happy-path approach that scans descendants or updates every ancestor on each charge change **cannot score above 58/100**, even with polished code.

| Dimension | Points | Evidence expected |
|---|---:|---|
| Problem decomposition and contract understanding | 12 | Charge identity vs event identity vs request identity; active/inactive lifecycle; local budget threshold, stream order and query timing. |
| Algorithm/data-structure selection | 18 | Efficient descendant rollups and active charge counts; very deep trees; cross-branch moves; avoids full scans and ancestor propagation; justified choices. |
| Domain/state correctness | 24 | Posts, revisions, voids, exact cents, zero-valued charges, cross-root moves, unchanged revisions, group totals/counts, output shapes, strict budget rule. |
| Complexity and scalability | 14 | Clear O() preprocessing, event/query time, memory for N centers, C charges, E events; 250k depth, skewed trees, query bursts, memory tradeoffs. |
| Adversarial cases and failure semantics | 13 | Replay after later changes, event conflicts, failed events not reserved, duplicate charges, unknown/inactive charges, boolean amount, malformed JSON, unknown center, request ID preservation. |
| Verification and tests | 9 | Original commands; exact response assertions, property tests against a slow small oracle, benchmark and regression tests. |
| Code quality | 5 | Parsing/state/output separation, maintainability, no stray stdout logging, preserves working snapshot validation. |
| Walkthrough and tradeoffs | 5 | Explains update/query invariants, replay precedence, alternative approaches, risks, and timebox decisions. |
| **TOTAL** | **100** | |

Scores: 90–100 excellent and robust; 75–89 strong with narrow gaps; 59–74 substantive partial with scaling or correctness gaps; 0–58 happy-path/naive. If no processing capability was delivered, credit only demonstrated decomposition and baseline preservation. Exact numeric subtotals above are authoritative.
