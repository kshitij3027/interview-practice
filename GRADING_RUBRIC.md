# POST-PRACTICE ONLY — SignalGate grading rubric (100 points)

Use **only after** the candidate has finished the 60-minute exercise. The customer-facing README remains the contract. Do not score by whether a candidate uses a predetermined SDK, language feature, LLM, or data structure; score correctness, defensibility, and stated tradeoffs. The evaluator branch must never be merged into a candidate branch.

| Dimension | Points | Evidence |
| --- | ---: | --- |
| Customer problem decomposition | **10** | Distinguishes catalog preprocessing from per-request scanning, recognizes raw bytes vs. base64/Unicode, immutable catalog, eligibility gates, per-line recovery, and exact top-K requirement. |
| Indexing/algorithm choice and explanation | **22** | Designs a search strategy whose ordinary per-request work does not scale linearly with all 200k signature IDs; explains how shared prefixes/suffixes and duplicate pattern bytes affect representation; preserves chunk continuity. Alternative deterministic/hybrid designs can earn full credit if equally rigorous. |
| End-to-end semantic correctness | **24** | Exact contiguous byte matching across chunks (7), eligibility by region/enabled/time (5), earliest byte offsets and unique-ID counting (5), strict priority/offset/ID ordering and top-K vs. total (5), output shape and determinism (2). |
| Runtime and memory scalability | **16** | Clear construction/query complexity and realistic memory estimates (7); bounds expensive match fan-out, short repeated patterns, and high-overlap inputs (5); discusses production p95/memory benchmarking, tradeoffs, and mitigations (4). |
| Robust validation and failure behavior | **10** | Snapshot-level duplicate/conflicting ID and schema errors (4); malformed vs. unknown-region query handling and canonical base64/size/type checks (4); reliable per-line continuation and stdout cleanliness (2). |
| Verification and adversarial testing | **10** | Adds boundary, overlap, time-window, repeated-ID, empty/binary chunk, tie-order, and shuffled-order checks (6); runs actual checks and verifies expected outputs rather than trusting generated code (4). |
| Code quality and walkthrough | **8** | Cohesive, maintainable implementation and narrow changes (3); accurate walkthrough of invariants, algorithm or hybrid rationale, failure modes, and AI-assisted choices (5). |
| **Total** | **100** | |

## Calibration / scoring constraints

- A solution that separately searches every signature for every request cannot receive more than **5/22** in indexing and **3/16** in scalability even if its small outputs are correct. With shallow tests and partial edge handling, the **practical cap is 55–60**. Award higher than 60 only if the candidate presents and convincingly validates a credible index/production alternative.
- Code that only changes the starter's `not_implemented` marker to an `ok` result without actual matching earns at most **10/100**.
- A solution that stops at the first `limit` matches and reports that count as total is not correct. Nor is one that ignores chunk-spanning matches, duplicated signature patterns, or time boundaries.
- A solution that performs well but can miss valid signatures cannot earn the correctness points it violates. Distinguish measured latency from unsupported claims.
- An LLM/heuristic/hybrid approach can earn full points **only if it demonstrably preserves the exact requirements**, or explains which guarantee it gives up and accepts the associated correctness penalty.
- Do not require one fixed internal architecture. Full credit is possible with a byte-oriented multi-pattern index, a carefully reasoned region-specific scheme, or an alternative approach with comparable guarantees.
- At least one real execution of verification and a reasoned walkthrough are needed for scores above 85.
