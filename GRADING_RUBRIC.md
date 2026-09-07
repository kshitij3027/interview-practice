# Grading Rubric — 100 points

## 1. Problem decomposition and model — 15 points
- **13–15 Excellent:** Correctly identifies that planning must preserve multiple non-equivalent partial states per schema because latency/quality/hop budgets interact with the cost objective; separates static catalog preprocessing from per-request state.
- **9–12 Acceptable:** Mostly sound model, with a minor gap in state definition or preprocessing.
- **5–8 Partial:** Understands path search but collapses important tradeoffs or handles constraints as after-the-fact filters.
- **0–4 Failing:** Treats adapters independently, uses greedy local choices, or lacks a coherent model.

## 2. Algorithm / data-structure choice — 20 points
- **17–20 Excellent:** Uses a production-credible constrained-search strategy with safe pruning/dominance and deterministic expansion/tie behavior.
- **12–16 Acceptable:** Correct search with weaker pruning or somewhat higher but defensible cost.
- **6–11 Partial:** Works on the fixture but has exponential/simple-path enumeration behavior or an unsafe one-label-per-schema shortcut.
- **0–5 Failing:** Brute force or incorrect greedy search.

## 3. Functional correctness — 20 points
Covers region eligibility, disabled adapters, inclusive budgets, max-adapter bound, empty-chain case, unknown schemas, cycles, totals, and ordered winner objectives.

- **18–20:** Correct across all evaluator cases.
- **13–17:** Core planner correct with one meaningful omission.
- **7–12:** Happy path works but several constraints/ties are wrong.
- **0–6:** Planner is substantially incorrect or incomplete.

## 4. Complexity and scalability — 15 points
Evaluate preprocessing, adjacency/index reuse, per-request search scope, memory growth, and explanation of worst-case frontier growth.

- **13–15:** Explicitly reasons about non-dominated state growth and production limits; avoids catalog copies/rescans and all-simple-path enumeration.
- **9–12:** Credible typical-case complexity with minor gaps.
- **5–8:** Correct-ish fixture solution but poor production scaling.
- **0–4:** No credible scale story.

## 5. Edge cases and determinism — 12 points
High-value evaluator checks include competing partial paths to the same schema, exact budget boundaries, zero-cost/zero-loss cycles, duplicate catalog replay, conflicting duplicate IDs, request-level disable duplicates, unknown disable IDs, 0-hop requests, row-order shuffling, and tie-breaking by adapter sequence.

## 6. Verification / tests — 8 points
- **7–8:** Focused tests target at least three dangerous semantics, including a case that defeats a naive one-best-state-per-schema solution.
- **5–6:** Good feature tests with some edge coverage.
- **2–4:** Mostly happy-path tests.
- **0–1:** Little or no useful verification.

## 7. Code quality — 5 points
Clear state representation, naming, decomposition, deterministic output construction, and minimal accidental complexity.

## 8. Explanation and tradeoffs — 5 points
Can explain why the chosen state is sufficient, why pruning is safe, expected time/space behavior, and what would change for much larger budgets or live catalog mutation.

## Calibration
- **90–100:** Excellent interview performance; robust, scalable, well-defended.
- **75–89:** Strong/acceptable; core solution is correct with limited gaps.
- **60–74:** Partial; useful implementation but meaningful correctness or scalability risks remain.
- **Below 60:** Incomplete, brute-force, or unsafe under stated constraints.

A solution that passes only straightforward fixture paths while enumerating chains or keeping a single cheapest state per schema should **not score above 55–60**, even if its output looks correct on the visible examples.
