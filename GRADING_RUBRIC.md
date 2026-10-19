# SatLink evaluator scorecard

POST-PRACTICE ONLY. Total score: 100 points.

| Dimension | Points |
| --- | ---: |
| Customer problem decomposition | 12 |
| Input and request semantics | 12 |
| Coverage and overlap correctness | 20 |
| Completeness and digest verification | 12 |
| Read behavior and result contracts | 14 |
| Complexity and memory | 12 |
| Testing and verification | 10 |
| Explanation and tradeoffs | 8 |
| **Total** | **100** |

Customer decomposition includes recognizing sparse export lengths, replays versus distinct captures, and immutable batch queries. Input semantics includes strict base64 and ID validation, snapshot-level errors, and line-by-line request recovery. Coverage correctness includes byte-for-byte comparison, non-duplicated positions and global smallest disagreement offset. Completeness includes empty assets, first hole, SHA-256 and checksum mismatch. Read behavior includes partial-asset covered intervals, gaps and canonical base64 output. Performance includes work proportional to captured content and indexed repeated queries, not declared size or full rescans. Tests cover reordered and overlapping fragments, malformed records, binary content and large sparse assets. Explanation includes complexity and defensible deterministic, heuristic or LLM/hybrid choices.

Excellent: 85–100. Acceptable: 70–84. Partial: 40–69. Failing: 0–39.

Calibration: ordered non-overlap happy path <=45; omitted conflicting overlaps, integrity, or sparse correctness <=55; per-request full scan even if otherwise correct <=60. A model call without exact verification brings no extra points.

Evaluator probes: duplicate capture IDs, conflicting capture reuse, earliest contradiction despite unordered input, one-byte holes, checksum mismatch and blocked reads, 0-byte assets, empty reads, huge declared sizes with tiny payloads, bad input followed by good queries, binary captures, and heavy repeated queries.