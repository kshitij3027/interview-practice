# SignalMesh Grading Rubric — 100 Points

This rubric is evaluator-only. Score the candidate's final state after the 60-minute exercise, including code, tests, verification, and walkthrough.

## 1. Problem decomposition and model — 12 points

- **10–12:** Correctly separates account metadata, per-evidence temporal state, pair-level relationship semantics, historical query answering, and cohort aggregation. Identifies that event order in the file is irrelevant and that removals/expiry make a forward-only connectivity structure insufficient by itself.
- **7–9:** Model is mostly correct but one subtle semantic area is underdeveloped.
- **3–6:** Understands the graph/cohort goal but treats time or duplicate evidence simplistically.
- **0–2:** Mis-models the problem or cannot explain the state transitions.

## 2. Temporal evidence correctness — 22 points

Award for correct handling of ASSERT, RETRACT, TTL expiry, repeated ASSERT refresh, same-instant query boundaries, out-of-order file rows, exact duplicate event retries, and inactive RETRACT no-ops.

- **18–22:** Semantics are correct across adversarial cases.
- **12–17:** Core behavior works with one or two boundary/refresh mistakes.
- **6–11:** Happy-path temporal logic works but refresh/expiry/retraction ordering is unreliable.
- **0–5:** Evidence state is materially incorrect.

## 3. Connectivity and cohort aggregates — 18 points

Award for exact connected-component semantics, transitivity, cycles, overlapping evidence IDs on the same pair, component size, high-risk count, risk-point sum, and lexicographically smallest representative.

- **15–18:** Exact and robust.
- **10–14:** Mostly correct with limited edge-case gaps.
- **5–9:** Simple components work but duplicate-pair/cycle behavior or aggregates are wrong.
- **0–4:** Connectivity result is not trustworthy.

## 4. Algorithm / data-structure choice and scalability — 20 points

Evaluate whether the approach shares work across 250k historical queries and accounts for both edge additions and removals.

- **17–20:** Production-credible exact or carefully justified design; candidate can explain preprocessing, query-time complexity, memory, skew, and why the chosen representation avoids per-query world rebuilds.
- **12–16:** Reasonable reusable preprocessing and much better than per-query replay, but some production bottleneck remains.
- **6–11:** Fixture-correct approach with meaningful reuse, but still scans/rebuilds too much for stated scale.
- **0–5:** Replays all events or rebuilds the full graph independently for each query, or uses an approach that cannot handle removals correctly.

## 5. Edge cases and determinism — 12 points

Cover unknown query accounts, unordered pairs, multiple evidence IDs per pair, offset-equivalent timestamps, event/query order independence, isolated accounts, cycles, same-instant boundaries, and deterministic output.

- **10–12:** Thorough and deliberate.
- **7–9:** Good coverage with minor omissions.
- **3–6:** Some edge handling but several listed traps remain.
- **0–2:** Primarily happy-path behavior.

## 6. Verification and tests — 8 points

- **7–8:** Adds focused tests for the highest-risk semantics and runs them; verification is targeted rather than superficial.
- **5–6:** Adds useful tests but misses one major risk area.
- **2–4:** Minimal tests or only fixture smoke checks.
- **0–1:** Little or no meaningful verification.

## 7. Code quality — 4 points

- **4:** Clear decomposition, sensible naming, minimal duplication, and no needless framework/infrastructure work.
- **2–3:** Generally readable with some rushed structure.
- **1:** Hard to follow or overly coupled.
- **0:** Unmaintainable or substantially broken.

## 8. Explanation and tradeoff defense — 4 points

- **4:** Clearly explains invariants, complexity, failure modes, and tradeoffs; can distinguish fixture shortcut from production design.
- **2–3:** Explanation is mostly sound but incomplete.
- **1:** Limited reasoning beyond code description.
- **0:** Cannot defend the approach.

## Score calibration

### Excellent: 85–100
Correct under temporal/connectivity edge cases, production-credible, well verified, and clearly explained.

### Acceptable: 70–84
Strong implementation with a few edge-case or scaling gaps, but demonstrates solid systems reasoning.

### Partial: 50–69
Meaningful progress and likely fixture success, but important correctness or scalability issues remain.

### Failing: below 50
Core semantics, connectivity, or implementation are incomplete or unreliable.

## Happy-path / brute-force cap

A solution that gets obvious fixture cases working but rebuilds the active graph separately for every query, ignores scale, or mishandles expiration/retraction must not score above **55–60**, even if several visible outputs are correct.
