# POST-PRACTICE ONLY — CacheFlow Grading Rubric

**Total: 100 points.** Score only candidate work completed within the 60-minute interview and explanations in the walkthrough. Do not read this before the practice run.

| Category | Points | Full-credit signals |
| --- | ---: | --- |
| Customer problem decomposition | 12 | Separates chronological replay from physical-line output; distinguishes expiration, tenant/global capacity, invalidation, hit, admission, and bypass; states invariants. |
| Algorithm and data-structure selection | 18 | Efficient per-object residency and recency operations, tenant and global eviction access, and expiration lookup; justifies data structures under skew, repeated hits, and stale metadata. |
| Functional correctness | 26 | Exact output contracts and counters; correct temporal handling; tenant-first then global eviction; correct recency on hit/miss, bypass, invalidation, and retry; correct replay under out-of-order input. |
| Complexity and scalability | 16 | Credible asymptotic bounds for 2M events/200k residents, no full resident scan per ordinary hit/miss, bounded or actively compacted auxiliary state, realistic memory/work estimates. |
| Edge cases and adversarial behavior | 12 | Covers exact expiry, TTL=0, zero quotas, oversize bypass, global-versus-tenant pressure, replay IDs, same-ms ordering, expired versus capacity-evicted, and post-invalidation reads. |
| Verification and tests | 9 | Adds focused tests including failing-before/fixed-after cases, asserts exact outputs, compares small cases to a simple reference model, runs scripts, includes meaningful stress check. |
| Code quality and maintenance | 4 | Clear state ownership, invariants, readable methods, no excess dependencies, keeps supplied parser/CLI behavior intact. |
| Walkthrough and tradeoff defense | 3 | Explains why the approach is exact, its worst cases, memory cleanup, AI usage, and a realistic improvement path. |
| **Total** | **100** | |

**Caps:** An ordinary happy-path replay with repeated full scans, incorrect expiration, or no realistic scaling argument must score **at most 55/100**, regardless of polish. A brute-force implementation with all simple outputs correct but no credible scaling earns **at most 60/100**. A result that never produces a meaningful successful replay earns at most 30. Passing only the starter tests is not evidence of feature correctness. Never award full correctness to a solution that evicts from the wrong tenant, extends TTL on hits, or counts a duplicate replay twice.

**Suggested review:** Run candidate tests and one end-to-end replay; use small independently computed counterexamples for capacity sequencing and expiry; inspect state representation and growth under repeated hits; have candidate trace one invalidation/re-admission and a same-time ordered pair. Allocate points proportionally rather than on self-reported confidence.
