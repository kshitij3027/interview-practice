# POST-PRACTICE ONLY — CaptionGate Grading Rubric (100 points)

**Interviewer use after the 60-minute exercise.** Apply this to observable implemented behavior and the candidate's demonstrated reasoning, not merely stated intentions. A happy-path-only WebVTT upload/publish attempt that ignores stale data, retries, and input edge cases should earn **no more than 60–65/100**, regardless of UI polish.

| Dimension | Points | Evaluation |
| --- | ---: | --- |
| End-to-end functional delivery | 17 | Working preview, clear browser review, publish, authoritative updated captions, per-locale replacement and receipt; sensible scope management. |
| WebVTT parsing and domain semantics | 22 | BOM/CRLF/header/NOTE, optional ID, both timing formats, integer timing, canonical text/order, de-duplication, overlapping boundaries, video duration, counts. |
| Backend safety and state transitions | 17 | Server-owned preview, eligibility/tenant checks, revision gating, no-op and single increments, atomic mutation, consistent errors and immutable receipts. |
| Retry, conflict and concurrency handling | 15 | Idempotency binding/replay, delay-after-check safety, consumed/expired preview, concurrent requests, failed-key reuse. |
| Frontend usability and reconciliation | 11 | Draft preservation, preview invalidation on edits/navigation, stale async response handling, clear conflicts, retry same key after uncertainty, post-publish refresh. |
| Verification, diagnostics and regression safety | 10 | Meaningful tests of tricky input and state transitions; running baseline/test/build; preserve note editing/listing. |
| Architecture, complexity and code quality | 5 | Cohesive ownership of parsing/state/API/frontend, bounded resource use, understandable names, no huge dependency rewrite. |
| Walkthrough and tradeoff defense | 3 | Explains semantically identical files, optimistic concurrency, failure semantics, performance and unfinished risks honestly. |
| **Total** | **100** | |

### Score boundaries
- **90–100:** unusually strong near-complete product slice, repeatability/concurrency verified and nuanced semantics defended.
- **75–89:** robust working workflow with isolated omissions in lower-risk cases.
- **60–74:** integrated workflow, several major edge cases still exposed.
- **45–59:** happy-path implementation with important missing correctness or state safety; most brute-force/unchecked one-shot implementations fall here.
- **0–44:** incomplete core workflow or unsafe publication.

**Hard caps:** No working publish path: 50. Unsafe cross-studio mutation: 55. No stale protection or retry safety: 60. Happy-path-only parser missing timing/order/boundary semantics: 60. Existing note behavior broken: 70. These are maximums, not automatic scores. Do not double-subtract in a way that obscures achieved work.
