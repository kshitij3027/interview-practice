# ChronoCheck — Grading Rubric (100 points)

**EVALUATOR ONLY — POST-PRACTICE ONLY.** Never distribute this document with the candidate branch.

| Dimension | Points | What to inspect |
| --- | ---: | --- |
| Problem interpretation and decomposition | 12 | Expresses signed equations clearly; separates revision reconciliation, consistency, query semantics and errors; inspects fixtures before choosing approach. |
| Algorithm / data representation | 20 | Chooses and justifies a scalable structure for related clocks, relative offsets and contradictions; weighted-component or graph-potential solutions and equivalent alternatives earn full credit. |
| Core correctness | 20 | Signed orientation, multihop inference, contradictions, component-level conflict, stable self-queries, status and output contracts. |
| Complexity and scalability | 14 | Preprocessing, repeated queries, worst cases, memory and production limits; no full scan/solve per request. Discusses high-scale Python memory costs and large signed sums. |
| Edge cases and validation | 10 | Out-of-order corrections/retractions, replay/conflicting revisions, atomic catalog failures, disconnected groups, tenant isolation, invalid JSON and ID recovery. |
| Verification and AI-tool discipline | 10 | Independent adversarial tests, reversals, contradictions, fixture checks, code review of AI outputs; understands baseline is not full feature acceptance. |
| Code quality and integration | 6 | Readable, minimal changes to contracts, robust error handling, deterministic JSONL output. |
| Walkthrough and tradeoff defense | 8 | Explains invariants, complexity, deterministic vs heuristic/LLM/hybrid tradeoffs, alternatives, bottlenecks, failure modes. |
| **Total** | **100** | |

## Scoring calibration

- Direct-edge-only or contradiction-ignoring happy paths: **cap at 45/100**.
- Correct per-query whole-network traversal/solve that ignores scale, with weak verification: **cap at 58/100**.
- Keeping not_implemented and merely passing starter smoke tests: usually **0–15/100**.
- A correct scalable design with a well-defended partial implementation can score for decomposition and design even if some coding details are incomplete.
- Do not bias toward an LLM, hybrid, heuristic or deterministic implementation. Judge correctness guarantees, cost/latency, explainability and failure modes, including why an approach is or is not justified.
- Do not award benchmark credit for unmeasured numbers. Evaluate the 60-minute work sample and reasoning, not ability to produce code volume.
