# POST-PRACTICE ONLY — CycleLedger grading rubric

**Total: 100 points.** Assess actual behavior, tests and walkthrough. Do not award points for code that an AI agent suggested but the candidate did not inspect or validate.

| Category | Points | Expected evidence |
|---|---:|---|
| End-to-end functional workflow | 20 | Preview, apply, receipt, no-op, visible UI workflow, existing directory still usable |
| Backend/domain semantics and persistence | 27 | Exact signed integer-cent proration (10), validation, chronology and statuses (7), atomic persisted history/revisions (10) |
| Frontend behavior | 14 | Authoritative preview and receipt, editable controls, preview invalidation, failure and retry UX, navigation safety |
| Integration across layers | 11 | Accurate HTTP contracts/errors, tenant isolation, consistency between list/detail/notes/amendments |
| Correctness traps and failures | 18 | Durable key replay and payload mismatch (5), stale revision and concurrent writers (5), date and rounding edge cases (4), uncertain network outcome and UI races (4) |
| Tests and verification | 7 | Focused domain/API tests, evidence of normal, negative, replay and conflict cases |
| Code quality and tradeoff walkthrough | 3 | Clear decomposition, focused changes, reasonable scale and consistency explanation |
| **TOTAL** | **100** | |

### Score caps

A basic happy-path amendment implementation, even with a polished UI, **cannot score above 60/100** if it ignores exact arithmetic, concurrency, retries or date boundaries. Nontransactional write logic without a credible invariant protecting revision/history/receipt consistency is capped at **60**. A preview-only backend without end-to-end apply is capped at **55**. Breaking existing note editing or tenant isolation caps the score at **60**. The goal is to reward the reasoning and correctness rather than the quantity of generated code.

### Complexity expectations

Indexed contract identity lookups and an O(H) update to a single contract's bounded history (H ≤ 100) are reasonable. Unindexed global scans on every amendment and volatile-only idempotency storage are not. Database schema changes are optional if behavior is correct; compare tradeoffs, not preferred library syntax.

### Suggested live probes

Demonstrate a negative credit with nontrivial fractional cents, a replay after a separate note edit, a conflicting concurrent request, persistence across server restart, and switching selected contracts while a preview/apply is pending.
