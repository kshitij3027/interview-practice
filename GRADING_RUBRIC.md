# GRADING RUBRIC — 100 points

## 1. Problem decomposition and contract understanding — 15 points
- 13–15: Separates static snapshot validation/preprocessing from query evaluation; states exact half-open time semantics, eligibility, deterministic tie-breaking, and independent-query behavior; identifies the main scale bottlenecks before coding.
- 8–12: Mostly correct decomposition with one material omission.
- 0–7: Treats the task as fixture-only brute force or misses central semantics.

## 2. Algorithm / data-structure choice — 20 points
- 17–20: Builds reusable per-pool availability state and an indexed strategy that can skip irrelevant time ranges; narrows eligible pools before temporal work; design is exact or clearly states any approximation.
- 11–16: Reusable preprocessing exists but important work is still repeated per start or per query.
- 0–10: Rescans all reservations/events/pools or brute-forces every 5-minute start with full-window rescans.

## 3. Functional correctness — 20 points
- 18–20: Correct earliest-window resolution, capacity arithmetic, eligibility, output ordering, and winner selection across all tested boundaries.
- 12–17: Core behavior works with limited edge-case defects.
- 0–11: Happy path only, incorrect capacity semantics, or nondeterministic winner selection.

## 4. Complexity and scalability reasoning — 15 points
- 13–15: Gives credible preprocessing/query/memory complexity, discusses hot-pool skew and long windows, and avoids dense full-horizon expansion.
- 8–12: Generally scalable but one important production constraint is hand-waved.
- 0–7: Complexity is incompatible with stated scale or not understood.

## 5. Edge cases and invariants — 10 points
Covers exact-time boundaries, same-instant capacity events, duplicate IDs, back-to-back reservations, offset-equivalent timestamps, empty tags, no eligible pools, long windows, and non-mutation of baseline state.

## 6. Verification and testing — 8 points
Adds focused tests that exercise at least several hidden-risk areas and actually runs them; distinguishes baseline validation failures from query-level invalid results.

## 7. Code quality — 5 points
Clear separation of loading/preprocessing/query logic, meaningful names, limited accidental complexity, useful errors, deterministic iteration where necessary.

## 8. Explanation and tradeoff defense — 7 points
Explains the chosen representation, why candidate starts can be skipped safely, worst cases, and why a deterministic/heuristic/LLM-assisted approach is or is not appropriate.

## Score caps
A solution that is correct only on the visible fixture but linearly scans every pool and every 5-minute candidate/window should not score above **58/100**. A happy-path solution that ignores boundary, duplicate, or determinism requirements should not score above **55/100** even if its sample output looks plausible.
