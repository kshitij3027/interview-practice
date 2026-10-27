# PermitLens — Grading Rubric (POST-PRACTICE ONLY)

Score **100 points total**. Judge observable behavior and defended reasoning, not tool choice, aesthetics, or generated-code volume.

| Criterion | Points | Full-credit expectations |
| --- | ---: | --- |
| Problem decomposition and prioritization | 8 | Identifies tenant/visit invariants, credential evidence, temporal capacity, preview/commit separation, retry, and time budget. |
| Domain/eligibility correctness | 22 | Correct visit/vendor constraints, UTC access windows, event replay and precedence, credential expiry, complete interval occupancy, deterministic findings. |
| API, concurrency and idempotency | 19 | Server-held reviews, precise 400/404/409 failures, validation after delay, atomic issuance, immutable retry receipts, one audit and version update. |
| Frontend behavior | 17 | Usable evidence review and issuance, authoritative receipt, stale async response protection, preserved retry intent, conflict recovery, existing navigation. |
| Edge cases and safety | 16 | Cross-vendor event ID collision, replay ties, malformed evidence, expiry/window boundaries, occupancy at a later time, tenant isolation, concurrent capacity. |
| Verification and regression tests | 10 | Targeted domain/API/adversarial tests and preservation of existing search, filters, note-edit semantics, concurrency and retries. |
| Code quality and scalability | 5 | Clear contracts, maintainable modules, useful errors, suitable indexing, bounded work under skew. |
| Debugging and technical walkthrough | 3 | Green checks, demonstrations, defended complexity and explicit incompleteness. |
| **TOTAL** | **100** | |

## Calibration
90–100: convincing end-to-end behavior including concurrency and adverse evidence; 75–89: coherent implementation with few narrow misses; 60–74: substantial vertical slice but important edge/recovery gaps; 40–59: mostly happy-path; below 40: fragile, unfinished or broken baseline.

**Hard caps:** A purely happy-path implementation or an unindexed global scan of all evidence and all passes for each review without a credible scale argument scores no more than **60**. If stale concurrent operations or retries can issue twice, cap **55**. If a tenant can issue another tenant's pass, if the browser determines eligibility, or if an error leaves partially changed state, cap **50**. If the starter application no longer runs and baseline behavior is broken, cap **40**. Apply the tightest cap and then score the table.
