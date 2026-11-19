# OfferStream — Grading rubric (POST-PRACTICE ONLY)

**Total: 100 points.** Assess observable behavior plus the candidate's implementation choices and post-hour explanation. Do not award points for unsupported claims or UI mockups that bypass server logic.

| Category | Points | Evidence |
|---|---:|---|
| Problem decomposition and contracts | 8 | Clarifies capacity invariants, expiring holds, chronological evaluation, client/server ownership, clear API boundaries |
| End-to-end feature functionality | 15 | Availability view, issue offers, respond, authoritative receipts and refreshed browser |
| Domain semantics and state transitions | 20 | Confirmed/waiting/cancelled behavior; offer lifecycle; closed sessions; half-open expiry; immutable records; safe mutation |
| Deterministic selection and capacity protection | 14 | Exact available seats, sorted waitlist by instant and ID, no repeat offers, no overbooking, large batches |
| Concurrency, idempotency, stale state | 16 | Single-advance revision, note/offer conflicts, one-key replay after later changes, collision detection, uncertain network retries |
| Validation, isolation and failure behavior | 9 | Strict JSON/time validation, time-travel guard, hidden tenant resources, clean error responses, no partial mutation |
| Browser integration and stale-response recovery | 9 | Usable controls, pending/error/success UX, authoritative reloading, stable retries, late-response suppression |
| Focused tests and verification | 6 | New tests for expiry boundaries, tie breaks, no-overbook, replays, collisions, regressions; baseline commands run |
| Code clarity and design defense | 3 | Cohesive layering, comprehensible data flow, thoughtful complexity and implementation tradeoffs |
| **Total** | **100** | |

## Score calibration

- **90–100:** Solid system with thorough edge coverage, tested capacity/retry correctness and a clear tradeoff walkthrough.
- **75–89:** Strong end-to-end result with a few noncritical omissions.
- **60–74:** Works across layers but misses important robustness or edge semantics.
- **45–59:** Basic flows only, little defense against expiry, stale state, duplicate submissions or capacity races.
- **Below 45:** Primarily mockups, unconnected endpoints or incomplete baseline.

**Ceiling:** If only a happy-path button and a basic POST are implemented while expiry, ordering, capacity races, key replay, and stale state are ignored, cap total at **60**, even if the demonstration looks good. If it is only backend or only UI, cap at **55**. Failure to preserve existing organization isolation caps at **50**; repeated overbooking or double acceptance caps at **45**. A merely theoretical scalability story earns no points without an appropriate implementation tradeoff.

## Interview follow-up

Ask the candidate to walk through a tie, an expiring offer at exactly its deadline, two concurrent advances for the last seat, a retry after a successful request followed by note edit, and switching organizations while a response is pending. Require an explanation of which state is authoritative and how each operation remains atomic.
