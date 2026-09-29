# Grading Rubric — EvalBoard Regression Gate

POST-PRACTICE ONLY

Total: 100 points

## 1. Functional end-to-end workflow — 18 points
- 5: Candidate selector and Compare work in the existing selected-suite UI.
- 5: Comparison results clearly show summary metrics and gate pass/fail state.
- 5: Approve works end to end and updates approved run/revisions without full reload.
- 3: Existing browse/filter/detail/note workflow remains usable.

## 2. Backend/domain correctness — 26 points
- 6: Correct effective-observation selection by numeric attempt, timestamp instant, then observation ID.
- 5: Correct weighted coverage and weighted quality, including missing/error cases.
- 4: Correct nearest-rank p95 latency and average-cost calculation.
- 6: All five gate checks are correct, including exact boundary behavior and critical-case rule.
- 5: Server remains authoritative and approval recomputes against current baseline/data.

## 3. Concurrency, mutation, and idempotency — 18 points
- 6: Approval checks observed suite revision/current status/current dataset; stale approval mutates nothing.
- 5: Successful approval changes only approved run and increments suite/global revisions exactly once.
- 5: Same request key and logical payload returns original outcome; key reuse with different payload fails.
- 2: Bounded delay behavior is implemented in a testable way.

## 4. Frontend async/state correctness — 12 points
- 5: Older comparison responses cannot repaint a newer suite/candidate request.
- 3: Delayed approval response cannot corrupt a newer navigated workspace.
- 2: Last-known-good state is preserved on transient failure where reasonable.
- 2: In-flight duplicate actions are prevented without freezing unrelated browsing.

## 5. Edge cases and validation — 12 points
- 4: Dataset mismatch, baseline-vs-itself, inactive suite, zero coverage, missing/error cases handled safely.
- 3: Exact gate boundaries behave correctly.
- 3: Required invalid fixture relationships/types/timestamps fail clearly rather than being guessed.
- 2: Deterministic ordering and row-order independence are maintained.

## 6. Tests and verification — 8 points
- 5: Focused tests cover several dangerous semantics such as attempt selection, gate boundaries, stale/idempotent approval, or races.
- 3: Candidate actually runs starter plus added tests/build checks.

## 7. Code quality and integration discipline — 4 points
- 2: Reasonable separation among parsing/domain/store/API/frontend state.
- 2: Changes are scoped, readable, and preserve the starter architecture.

## 8. Explanation and tradeoff defense — 2 points
- 2: Candidate can explain metric representation, complexity, concurrency boundary, and what they would harden next.

## Score caps
- Happy-path UI plus naive metrics but incorrect stale/retry/critical semantics: max about 60–65.
- Comparison only with no safe approval mutation: max about 65.
- Obvious quadratic case-to-observation matching at stated scale: max about 70.
- Client-authoritative approval or trusting client-provided pass/fail: max 55.
- Double-applying retries or approving stale suite state: max 55.
