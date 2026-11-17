# CaseFold — Grading Rubric (POST-PRACTICE ONLY)

**HARD AI-assisted 60-minute full-stack interview. 100 points total.** This document is evaluator-only; never provide it before candidate completion.

| Category | Points | Evidence |
|---|---:|---|
| Problem decomposition and contract | 8 | Identifies invariants across source/target, tenant/customer, revisions, merge identity, visible results; plans an achievable vertical slice |
| Domain consolidation semantics | 19 | Correct status transitions, priority max, unique sorted tags, immutable source activity/note, target fields preserved, both revisions exactly once, directory excludes merged |
| Timeline integrity and determinism | 16 | Deduplicates exact canonical records by ID, rejects contradictory shared IDs atomically, parses RFC3339 offsets, sorts by true instant then ID, counts unique and discarded occurrences correctly |
| API validation and integration | 12 | Strong JSON validation, codes 400/404/409, response shape, scope checks, server-owned computations, existing endpoints unchanged |
| Concurrency and atomicity | 14 | Checks source and target revisions in same transaction/critical section as mutation; stale notes invalidate merge; concurrent merge conflicts; no partial writes |
| Retry and idempotency | 12 | Request-key scope, exact payload fingerprint, stored immutable receipt and target snapshot, original response on identical replay despite later updates, collision 409, correct validation order |
| Frontend interactions and recovery | 11 | Usable target selection, customer/status/revision context, authoritative refresh and selection, 409/400 handling, late response guard, uncertain network retry with same key/payload |
| Testing and debugging | 5 | Adds focused domain and HTTP tests for race-like behavior, duplicates/conflict, retries, scoping, existing regressions; runs full baseline and demonstrates fixes |
| Code quality and walkthrough | 3 | Clear separation, maintainable code, no hidden mutation, complexity discussion and explicit limitations |
| **Total** | **100** | |

## Score calibration

- **90–100:** Correct end-to-end implementation; robust against independent adversarial cases; clear tradeoffs.
- **75–89:** Most end-to-end paths correct, modest gaps in one hard class (e.g. offset ordering or response race).
- **60–74:** Useful working vertical slice, significant integrity or retry gaps.
- **≤65 hard cap:** Happy-path UI and merge work but conflict/retry/edge cases are largely unaddressed.
- **≤60 hard cap:** No atomic revision protection or missing strict activity deduplication, even if the feature works for clean data.
- **≤55 hard cap:** Brute-force customer-wide scans or mutating independently without rollback; no robust privacy or repeatability.
- **≤45:** No working integration, or cannot preserve existing app behavior.

Do not double-count one bug across categories excessively; caps constrain the maximum. Verify the final code, not only the walkthrough. If AI produced unexamined code the candidate cannot explain, reduce decomposition, quality and testing scores accordingly.
