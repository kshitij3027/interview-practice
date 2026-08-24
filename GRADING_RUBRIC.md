# GRADING_RUBRIC — RoutePolicy

**Evaluator-only. Total: 100 points.**

A happy-path implementation that linearly scans all rules and ignores production constraints should not score above roughly 55–60, even if it passes the visible fixture.

## 1. Problem decomposition and model — 15 points

- **13–15:** Clearly separates parsing/validation, static preprocessing, candidate discovery, exact eligibility checks, precedence, and output materialization. Correctly identifies the distinction between exact path segments, `*`, and `**`, including zero-segment `**` matches.
- **9–12:** Mostly sound model with minor coupling or an unclear boundary.
- **4–8:** Happy-path reasoning but misses important semantics or treats matching as ad hoc string logic.
- **0–3:** No coherent model of the problem.

## 2. Matching correctness — 20 points

Award for correct full-path matching semantics across literals, `*`, and one `**`, including `**` at the beginning, middle, or end and matching zero segments.

- **18–20:** Correct across all hidden cases with no duplicate-match bugs.
- **13–17:** Small edge-case defect but core semantics are correct.
- **6–12:** Works for literals and simple wildcards but mishandles `**` or full-path matching.
- **0–5:** Fundamentally incorrect matching.

## 3. Scope, time, and precedence correctness — 20 points

Must correctly enforce tenant, region, inclusive `valid_from`, exclusive `valid_to`, no-expiry rules, and the complete deterministic precedence chain:

1. priority descending;
2. literal count descending;
3. `**` count ascending;
4. `*` count ascending;
5. exact tenant over `*`;
6. exact region over `*`;
7. rule ID lexicographically ascending.

- **18–20:** Exact semantics and deterministic results.
- **13–17:** One localized precedence/time defect.
- **6–12:** Multiple omissions, input-order dependence, or incorrect tie-breaking.
- **0–5:** Winner selection is unreliable.

## 4. Algorithm/data-structure choice and scalability — 20 points

- **18–20:** Uses a credible static index that narrows candidate rules based on path structure and/or scope; avoids scanning 1.5M rules per request; explains query work in terms of request depth, wildcard states, and returned candidates; explicitly considers memory under 512 MB and pathological wildcard-heavy rules.
- **13–17:** Indexed approach is directionally strong but has avoidable memory/time overhead or a weak pathological-case story.
- **7–12:** Some coarse partitioning (for example tenant or first segment) but request-time work may still scan very large buckets.
- **0–6:** Full rule scan per request, transitive expansion of every possible concrete path, or another approach incompatible with the stated scale.

## 5. Validation and edge cases — 10 points

Covers conflicting duplicate IDs, exact duplicate rows, malformed/timezone-less timestamps, invalid validity windows, empty path segments, route/block destination rules, literal `visa*`, and maximum depth.

- **9–10:** Robust validation with useful failures.
- **6–8:** Most cases handled.
- **3–5:** Several important gaps.
- **0–2:** Little validation.

## 6. Verification/testing — 8 points

- **7–8:** Adds focused tests for zero-length `**`, middle `**`, precedence ties, time boundaries, wildcard/literal distinction, duplicates, no-match behavior, and at least one scale-oriented or adversarial case.
- **5–6:** Good correctness tests but limited scale/adversarial thinking.
- **2–4:** Mostly fixture smoke tests.
- **0–1:** Little or no verification.

## 7. Code quality and walkthrough — 7 points

- **6–7:** Clear code, intentional data representation, easy-to-follow naming, and a walkthrough that defends tradeoffs, complexity, and why an LLM/heuristic component is or is not appropriate.
- **4–5:** Generally clear but with some unexplained decisions.
- **2–3:** Working but hard to reason about.
- **0–1:** Fragile or unexplained.

## Score interpretation

- **90–100:** Excellent. Correct, scalable, well-tested, and convincingly defended.
- **75–89:** Strong. Production direction is credible with limited defects or omissions.
- **60–74:** Acceptable/partial. Core problem is understood, but correctness or scale gaps remain.
- **40–59:** Weak. Happy path may work, but major semantics or production constraints are ignored.
- **0–39:** Failing. The solution does not reliably solve the stated customer problem.
