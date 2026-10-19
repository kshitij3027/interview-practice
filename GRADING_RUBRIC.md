# QuoteScope Grading Rubric — POST-PRACTICE ONLY

Total: **100 points**.

| Criterion | Points |
|---|---:|
| Understand business semantics and decompose problem | 12 |
| Historical event replay and current quote-state correctness | 20 |
| Exact execution and multi-level arithmetic | 20 |
| Algorithm and data-structure scalability | 23 |
| Tricky input cases, deterministic results and failure recovery | 12 |
| Testing and verification | 7 |
| Code quality | 3 |
| Walkthrough, complexity analysis, tradeoff defense | 3 |
| **TOTAL** | **100** |

A correct fast approach must distinguish SET from delta updates, aggregate dealers at the same price, maintain distinct bid/ask sides, price moves and zero-lot cancellations, preserve historical as-of semantics and support partial execution at a price boundary. Verify stable tie behavior, timestamp inclusivity, idempotent replay, malformed requests, unknown markets and output order.

A brute-force approach that replays the entire event stream and scans/re-sorts all price levels per query is capped at **55/100**, even with happy-path outputs. Solutions that fail cancellation, arbitrary historical ordering or multi-level fills are normally capped at 50. Starter tests do not test the missing quote estimator.
