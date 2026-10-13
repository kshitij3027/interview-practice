# POST-PRACTICE ONLY — FindFix Grading Rubric

Total **100 points**. Grade the running implementation and reasoning.

| Dimension | Points | Expected evidence |
| --- | ---: | --- |
| Problem decomposition | 10 | Understands query and tenant scope, preview binding and revisions. |
| Deterministic search behavior | 23 | Pin, hide, boost, category eligibility, score-zero pin, limit, total and tie-breaks. |
| Input validation and tenant isolation | 13 | Rejects malformed, duplicate, unknown, archived and cross-tenant references. |
| Preview, publish and versioning | 17 | Nonmutating preview, exact-intent publication, staleness, atomicity, semantic no-op, revision accounting. |
| Retry safety and failure recovery | 12 | Scoped trimmed keys, safe lost-response retry, collision rejection, no key retention for failures. |
| Frontend and integration | 12 | Draft editing, comparison, publish, conflict recovery, asynchronous response guards and search refresh. |
| Tests and verification | 8 | Probes negative cases, correctness invariants and existing note/search regressions. |
| Code quality and walkthrough | 5 | Design clarity, scalable search strategy, tradeoff explanation and disciplined AI use. |
| **TOTAL** | **100** | |

## Score ceilings
- Happy path without concurrency, idempotency or substantial edge-case handling: **60/100 max**.
- Client-computed ranks trusted for publication: **45/100 max**.
- Cross-tenant or archived-article disclosure: **50/100 max**.
- No functioning end-to-end publication/search: **40/100 max**.
- Unnecessary repeated quadratic work at 100,000 articles: **65/100 max**.

## Interviewer demonstrations
Try a zero-score pin, then a category excluding it. Check Unicode-equivalent queries and a one-result limit. Preview, edit an unrelated note, and publish stale. Retry a prior successful publication after a later edit. Reuse a request key with different intent. Reorder only boosts/hides (no-op); reverse pins (change). Examine test evidence and candidate explanation.
