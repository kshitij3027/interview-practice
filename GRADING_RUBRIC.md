# MergeGuard Grading Rubric — 100 points

Evaluator-only. Do not copy this file to the candidate branch.

## 1. Problem decomposition and invariants — 15 points

- **13–15:** Clearly models persistent customer groups, symmetric separation constraints, atomic rejection, deterministic canonical selection, and incremental event processing before coding. Distinguishes endpoint checks from group-level conflict checks.
- **9–12:** Mostly correct model with one minor gap or underspecified invariant.
- **5–8:** Happy-path grouping works but important invariants are discovered late or patched reactively.
- **0–4:** Treats links as isolated pairs or otherwise misunderstands transitivity/atomicity.

## 2. Core grouping/update correctness — 20 points

- **17–20:** Accepted links merge complete groups correctly; transitivity holds; same-group links are safe no-ops; later queries always observe the current group.
- **12–16:** Core behavior works with minor edge defects.
- **6–11:** Works for simple chains but breaks under repeated/large-group merges or inconsistent representative handling.
- **0–5:** Group membership is fundamentally incorrect.

## 3. Separation-conflict correctness and atomicity — 20 points

- **17–20:** Rejects any merge that would internalize any known separated pair, including non-endpoint conflicts; rejected links produce zero state mutation and do not affect later valid links.
- **12–16:** Correct on most conflicts but has a subtle atomicity or indirect-member defect.
- **6–11:** Checks only link endpoints or rescans broadly with correctness holes.
- **0–5:** Allows forbidden groups or corrupts state on rejection.

## 4. Complexity and production credibility — 15 points

- **13–15:** Uses incremental structures with near-constant/slow-growing representative lookup and moves or updates conflict metadata in proportion to the smaller relevant structure; does not rescan all records or all separation pairs per link. Provides a coherent memory argument for millions of records/pairs and identifies large-group pathological cases.
- **9–12:** Reasonable incremental approach but with avoidable repeated scans or weak memory accounting.
- **5–8:** Correct fixture solution whose per-link cost scales with all records/separations or repeatedly rebuilds groups.
- **0–4:** Brute-force approach with no credible production path.

**Cap:** A solution that ignores the production constraints and rescans the full dataset/separation list per link cannot score above **60/100 overall**, even if fixture outputs are correct.

## 5. Canonical record semantics and determinism — 10 points

- **9–10:** Correctly applies quality descending, creation time ascending, then record ID ascending; canonical choice remains stable across merge order and input ordering.
- **6–8:** Mostly correct with one tie-break or update issue.
- **3–5:** Canonical selection works only in simple cases or is recomputed inefficiently.
- **0–2:** Incorrect or nondeterministic canonical behavior.

## 6. Input validation and edge cases — 8 points

Award for handling self-separation, duplicate/reversed separation rows, unknown IDs, duplicate event IDs, repeated same-group links, singleton queries, long chains, and later valid links after rejection.

- **7–8:** Comprehensive.
- **5–6:** Good coverage with minor omissions.
- **2–4:** Several meaningful gaps.
- **0–1:** Minimal validation.

## 7. Verification and tests — 7 points

- **6–7:** Adds focused tests for at least one non-endpoint separation conflict, rejection atomicity, canonical tie-breaking/merge-order independence, repeated no-op links, and a later valid merge after rejection.
- **4–5:** Good tests but missing one major adversarial case.
- **2–3:** Mostly happy-path tests.
- **0–1:** Little/no meaningful verification.

## 8. Code quality and walkthrough — 5 points

- **5:** Clear code and data ownership; candidate can explain every major state structure, mutation sequence, complexity tradeoff, and why deterministic vs heuristic/LLM choices are appropriate.
- **3–4:** Understandable implementation and explanation with minor ambiguity.
- **1–2:** Code works but ownership/tradeoffs are unclear.
- **0:** Cannot explain the resulting solution.

## Performance bands

- **90–100 — Excellent:** Correct, incremental, deterministic, well-tested, and production-aware. Candidate explains invariants and tradeoffs crisply.
- **75–89 — Strong/acceptable:** Core semantics are correct with limited gaps or less-than-ideal scaling details.
- **60–74 — Partial:** Material progress and some correct design, but one significant correctness/scalability weakness remains.
- **<60 — Failing:** Happy-path/brute-force implementation, forbidden merges, non-atomic rejection, or incomplete core behavior.
