# GRADING RUBRIC — POST-PRACTICE ONLY

Score the observable result and walkthrough, not the amount of code. Partial credit within each category is allowed.

| Category | Points | Full-credit evidence |
|---|---:|---|
| Functional correctness | 18 | Read-only preview (5), upgrade to highest same-template version (5), correct atomic mutation/revision and archive preservation (8). |
| Backend/domain behavior | 20 | Stable-ID identity and unchanged type (7), exact target validation (7), missing-required semantics without invented defaults or blocking (6). |
| Frontend behavior | 16 | Eligible affordance and understandable preview (6), confirm/cancel/pending (4), refreshed form, archive and missing fields (6). |
| API/integration | 12 | Both routes integrated with persistence (5), consistent error contract and input validation (4), correct post-upgrade answer editing and directory (3). |
| Edge cases / failure | 20 | Reject stale revision/target without mutation (6), false/zero/blank vs absent (4), correct discard reason/order (4), historical archive and no duplicates on retry (3), late response isolation and recovery (3). |
| Tests | 7 | Focused domain tests (3), API or persistence conflict tests (3), existing tests green (1). |
| Code quality | 4 | Clear responsibilities, readable changes, no redundant inconsistent rules. |
| Verification/debugging | 3 | Demonstrates real flow, identifies failures and explains limitations. |
| **Total** | **100** | |

Cap at 60 if happy path works but stale requests can corrupt state, valid false/zero answers are lost, or archived values can be resurrected. Cap at 65 for a happy-path-only solution that misses multiple important edge cases even if the demo looks polished. Backend-only or frontend-only work earns points only for demonstrated categories; do not double award the same evidence. A serious partial solution with explicit tradeoffs may earn credit without a polished UI.
