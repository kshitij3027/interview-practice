# ReturnCredit — 100-point Grading Rubric

**POST-PRACTICE ONLY — Evaluator material. Do not open during the interview.**

Score observed behavior, correctness and candidate explanations rather than the AI assistant used.

| Category | Points | Evaluation criteria |
|---|---:|---|
| End-to-end feature and API behavior | 12 | Complete selected-order partial-refund request, meaningful response, usable interface and errors. |
| Server/domain validation | 15 | Delivered-only, existence, 1–50 unique items, safe positive quantities, remaining units, trimmed reason/key, delay bound and server authority. |
| Cent-exact monetary semantics | 20 | Final line charge includes discounts and tax exactly once, excludes shipping, distributes pennies to earliest units, respects existing refunds, and conserves money across partial sequences. |
| Atomic persistence and revision invariants | 14 | No partial writes on rejection, update counts/cents and audit exactly once, bump order/global revision exactly once, preserve unrelated data. |
| Idempotency, concurrency, retries and stale writes | 16 | Globally scoped normalized request identity, stable original response, collisions, delay-insensitive identity, revalidation after delay, safe concurrent same/distinct keys. |
| Frontend state, integration and recovery | 10 | Quantity/reason form, per-line breakdown, authoritative reconciliation, duplicate guard, stale recovery, preserving inputs, protection from obsolete responses. |
| New tests and high-risk verification | 8 | Odd-cent prior-refund cases, varied batch sizes, multiple lines, atomic invalid requests, stale/delayed races, same-key/different-key concurrency, regression tests. |
| Code quality | 3 | Clear domain boundaries, safe integer handling, no unnecessary global scans, readable errors and maintainable source. |
| Interview explanation and debugging | 2 | Can demonstrate commands and articulate money, scaling, consistency and retry tradeoffs. |
| **Total** | **100** | |

## Score ceilings
- A happy-path-only refund flow that ignores cent allocation, over-refund prevention, stale writes or retry safety is capped at **60/100** even with a polished UI.
- Any solution that allows ordinary retry double crediting or quantity over-refunding is capped at **60/100**.
- A client-only refund calculation with no authoritative backend mutation and validation is capped at **45/100**.
- Missing the browser interface entirely caps the score at **75/100**; missing backend mutation entirely caps the score at **35/100**.
- Award legitimate partial credit for demonstrably correct components. Do not credit scale/atomicity merely because a toy fixture passes.

## Grading walkthrough
First run ./scripts/test.sh, ./scripts/build.sh and ./scripts/verify.sh. Exercise ORD-201, check a historical partial refund and an additional two-unit refund, and verify both per-line and aggregate totals. Next test invalid multi-line input, key replay and conflict, delayed stale mutation racing a note edit, concurrent duplicate submissions, selecting another order while a slow response is pending, and the pre-existing note/list functionality.
