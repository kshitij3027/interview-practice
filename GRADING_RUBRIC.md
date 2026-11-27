# RackFit — evaluator rubric (100 points)

Score observable evidence, not preferred technology. The candidate may use AI freely. A justified alternative architecture earns full credit if it meets the contract.

| Dimension | Points | Evidence |
|---|---:|---|
| Problem decomposition | 12 | Separates permanent occupancy, mutable reservations, operation identity, selection order and validation; identifies sparse address space and skew. |
| Technical strategy | 18 | Represents occupied/free space without capacity-sized arrays (6); supports efficient ordered selection accounting for all alignment classes (8); coherent update invariants (4). |
| Functional correctness | 22 | Exact allocation and lexicographic volume/start choice (9); correct split/release/reuse without overlap (7); correct statuses and per-line output (6). |
| Edge cases and failure semantics | 16 | Union of permanent spans (3); alignment and capacity boundaries (3); replay of success and failure and conflicts (6); global active IDs and malformed input isolation (4). |
| Complexity and scalability | 15 | Explains initialization and per-event time/space with realistic bounds (6); handles hot fragmented pools and repeated misses (6); credible measurement or memory accounting (3). |
| Verification | 8 | Focused assertions for stateful sequences and invariants (4); independent oracle, randomized or representative performance tests (4). |
| Code quality | 5 | Readable boundaries, no unrelated complexity, maintainable state. |
| Walkthrough and tradeoffs | 4 | Explains decisions, alternatives, AI-generated code verification, limitations and next steps. |
| **Total** | **100** | |

Calibration: a happy-path implementation that misses replay, fragmentation, alignment or release invariants, or whose design repeatedly scans all free extents in a hot pool, is capped at 58 even if simple examples pass. Capacity-sized arrays are not viable. Give partial credit for a correct small-input baseline plus a well-explained scale plan, but not full implementation points for an unbuilt design. A candidate who demonstrates a credible efficient approach but runs out of time should receive earned partial credit. Do not penalize deterministic vs heuristic vs hybrid choice by itself; approximate answers are not acceptable under the customer contract.
