# POST-PRACTICE ONLY — ScanLedger Grading Rubric (100 points)

This file is for the interviewer after practice. Do not read or copy into the candidate branch. Grade the observable customer contract rather than adherence to one particular programming language, data structure, or AI platform.

## 1. Decomposition and data contracts — 10 points
- **4**: Understands complete planned/observed tape consumption, repair types, original offsets.
- **3**: Understands repeated checkpoints, request independence, inclusive repair budgets.
- **3**: Differentiates fatal catalog errors from per-query invalid results, preserving order and IDs.

## 2. Global optimality and reconstruction — 30 points
- **10**: Calculates the exact **minimum repair count** for complete tapes, not a greedy local score.
- **6**: Correctly minimizes the number of `incorrect` substitutions among minimum-repair solutions.
- **6**: Implements lexicographic tie-breaking across the entire step-type sequence, **including matches**.
- **5**: Returns correct operation-specific fields and original `observed_offset`/`expected_offset` in traversal order.
- **3**: Handles budget equality and returns `None` without a partial plan when impossible.

## 3. Adversarial and boundary correctness — 20 points
- **5**: Repeated labels, ambiguous routes, globally worse local choices.
- **4**: Empty scan tape, trailing missing/unexpected, exact equality, zero budget and length difference.
- **4**: Correct matching/substitution legality and arbitrary unfamiliar observed codes.
- **4**: Independent requests, duplicate IDs, unknown routes, malformed JSON.
- **3**: Wrong types including booleans, conflicting catalog definitions versus legitimate replay.

## 4. Scalability / engineering choices — 15 points
- **7**: Running time uses the small correction budget and avoids a full product-size comparison.
- **4**: Explains/profiles memory use including traceback at 200k tokens and budget 16.
- **2**: Quickly rejects impossible long tapes; no uncontrolled recursion or invented truncation.
- **2**: Honest measured/estimated performance claims, with relevant benchmarks.

## 5. Verification and debugging — 15 points
- **6**: Adds tests targeting repeats, tie rules, wrong scans, endpoints and malformed inputs.
- **4**: Confirms applying returned operations reconstructs the planned sequence; preferably uses a small exhaustive oracle.
- **3**: Runs starter plus new tests, CLI smoke, verifies continued processing.
- **2**: Provides a meaningful large synthetic workload/benchmark.

## 6. Code quality and explanation — 10 points
- **4**: Focused, maintainable implementation with appropriate boundaries.
- **3**: Explains the state model, global choice, canonical script construction and complexity.
- **3**: Defends deterministic, LLM, heuristic or hybrid choices and the reliability consequences of AI use.

## Grade bands and caps
**85–100 excellent:** exact semantics, scalable method, strong adversarial tests and convincing walkthrough. **70–84 acceptable:** strong core with limited identified gaps. **45–69 partial:** incomplete ties, edge behavior, or resource use. **<45 failing:** no trustworthy working core or fundamentally local/incorrect logic.

**Hard ceiling:** a happy-path greedy script or a full O(n*m) matrix that cannot handle the stated long-tape constraint receives **at most 55–60**, regardless of polish. Weight exact global correctness more than formatting. A deterministic method is not mandatory if the chosen alternative demonstrably provides the exact same outputs.
