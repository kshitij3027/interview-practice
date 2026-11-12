# POST-PRACTICE ONLY — CycleLedger interviewer notes

**Do not open or reveal this document until after the timed interview.**

## Intended underlying problem and solution outline

This is a small transaction-processing and temporal billing problem, not merely a form with POST requests. The candidate must discover that correct billing depends on interpreting a half-open calendar period, a versioned current seat count, append-only historical changes and a durable command receipt. The important hidden structure is the relationship between a *pure quote projection*, *optimistic version checking*, *atomic persistence*, *exact rounding*, and *at-most-once effects with replayable receipts*.

Strong solutions separate: (a) contract and plan lookup with organization scoping; (b) strict date/count/status/chronology validation; (c) pure exact-cent proration; (d) read-only preview; (e) a single serialized atomic transaction for apply and receipt persistence; (f) UI request identity and stale selection handling. This can be deterministic with SQLite and need not use an LLM; an LLM used to draft code/tests is fine if the candidate explains and verifies the business invariants.

An appropriate schema extension is an indexed table keyed by (contract_id, request_key), storing a canonical logical-request fingerprint and the original serialized receipt. The existing contracts table stores its history as changes_json. This is acceptable with a bounded 100 records/contract; a normalized amendments table can be justified for longer history and reporting. An idempotency record for a valid same-seat no-op is necessary even though it does not increment revision. Another defensible implementation uses a unique amendment table, a receipt table and compare-and-swap UPDATE; all writes still belong in one transaction.

Under SQLite, BEGIN IMMEDIATE before the idempotency lookup and fresh current-row read is a straightforward choice. A compare-and-swap condition on revision plus unique receipt key and rollback on failure is also defensible. No network payment processing is within scope. A process-global dictionary lock or in-memory set of request keys does not meet restart durability; relying on read-then-write outside a transaction allows double applications.

### Correct monetary/date calculation

D = (periodEnd - periodStart).days, R = (periodEnd - effectiveOn).days, numerator = (newSeats - oldSeats) * seatPriceCents * R. Using integer values only, let (whole, rem) = divmod(abs(numerator), D). Rounded magnitude = whole + (1 if 2*rem >= D else 0). Signed amount is that magnitude times the sign of numerator (zero remains zero). This implements half-away-from-zero consistently for debits and credits. No floating-point price, JavaScript Math.round, or Python bankers' round. Date validation should accept only canonical YYYY-MM-DD text representing a real calendar date, and use periodEnd as exclusive. A proposal on the period's final day has one remaining day, not zero. The effective date may be before today's wall-clock date if the documented period and change history permit it; the contract fixture, not the wall clock, controls validity.

Old history amounts are immutable: they are not recomputed or corrected by a new request. The existing current seats already reflect earlier amendments.

## Data observations the candidate should discover

- ctr-101 is at **17 seats**, not the earlier 12. Its existing change became effective 2026-11-05; an additional effective date on or before that date is invalid.
- ctr-106 has two historical changes; the latest effective date is **2026-11-09**, and current seats are 43. Testing chronology against only the first array element is wrong.
- ctr-104 has a billing period from 2026-10-20 to 2026-11-20 (31 calendar days). It is not a fixed 30-day billing month.
- ctr-103 is paused and ctr-107 ended. Neither should accept an amendment, even if the incoming JSON looks otherwise valid.
- ctr-112 begins a future billing period on 2026-11-15; this is not grounds to reject all dates in its period automatically.
- Note editing increments the **same contract revision** that amendment applies must verify, making an apparent harmless note edit a genuine stale-preview event.
- Starter tests intentionally validate only directory, isolation, pagination and note behavior. New feature-specific correctness must be developed and verified by the candidate.

## Hidden checks and subtle traps

1. Preview ctr-102 from eight to nine seats effective 2026-11-16: 15 of 30 days remain at 2900 cents/month, so **+1450 cents**. Eight to seven yields **-1450 cents**. Preview must leave revision/seats/history unchanged.
2. ctr-101 from 17 to 20 effective 2026-11-12 has 19 days of 30 remaining; 3*7400*19/30 = **14060 cents**.
3. Choose a small negative prorated fraction producing an exact half-cent remainder using an isolated synthetic contract. Python round and JS Math.round differ from the required negative half-away-from-zero behavior.
4. Effective date equal to periodEnd is invalid; effective date on a latest historical change is also invalid, even when the requested new seats differ. Reject impossible YYYY-MM-DD and timestamps with timezone suffixes.
5. JSON true is an integer subclass in Python; use type(value) is int to reject booleans. Also reject numeric strings, floats, null, invalid seat counts and requestKey exceeding 100 ASCII-safe characters.
6. A no-op must not update revision/history but must create a persisted replayable receipt. An identical requestKey submitted again later returns exactly the original receipt; a reused key with any different logical field must return 409.
7. The same key after a later note edit must still replay the original successful receipt: check exact idempotency match **before** rejecting an obsolete expectedRevision. The first apply should also be protected against a note edit before it commits.
8. Different request keys racing with the same expectedRevision must produce at most one changed contract. No orphan receipt entry, duplicate change ID, partial revision increment or lost note.
9. An apply for ctr-105 under org-cedar returns 404 and cannot reveal that org-maple owns the contract. Key scope is by **contract**; the same key may validly be used on a different contract.
10. Retry after server process restart must still find the original receipt. An in-memory map fails.
11. Backend must recompute pricing from current seats and catalog plan, not accept a client-supplied oldSeats/price/amount. Preview must not be treated as a committed authorization when revision changes.
12. A stale browser response after switching organization/contract or changing effectiveOn/newSeats cannot update the new selection's preview or receipt. Note edits should invalidate the preview.
13. Old list search, customer ordering, counts before pagination, note trim/no-op rules, stale notes and organization isolation must still work.

## Why naive approaches fail

A happy-path POST that simply does (newSeats-oldSeats)*monthlyPrice*remainingDays/30 silently fails on 31-day terms, credits, half-cent rounding, period boundaries and backdated history. A read-modify-write without transactional revision checking allows two operators to race, both charging or overwriting each other. A retry that always creates a fresh request key causes duplicate financial adjustments after response loss. Catching every HTTP 409 and blindly resubmitting on current revision hides genuine customer changes. Keeping receipts in browser storage or process memory does not survive restart. Replacing the entire app with generated code often breaks established note and navigation behavior.

## Alternative defensible designs and complexity

For C total contracts, H history records for one contract, K retained keys: indexed contract lookup O(log C), calculation O(1), history read/write O(H) if JSON is used (H ≤ 100), receipt lookup O(log K) for indexed table, and transient O(H) memory. Normalized history can make new event insertion O(log H) but makes more queries complex. SQLite serializes writes with BEGIN IMMEDIATE; discuss this throughput tradeoff versus optimistic UPDATE WHERE revision=? and unique key constraints. A distributed database requires stronger consistency arrangements but is out of scope. Pure immutable pricing projection plus a command handler is a clean separation but not mandatory.

## Likely AI-assisted implementation failure modes

- Generating superficially complete routes and React-style UI without testing a single end-to-end retry.
- Floating-point monetary arithmetic and negative rounding inconsistency.
- Blind faith in unique UUID keys but no durable duplicate receipt lookup.
- Failing to validate the *same* key against a changed payload.
- Comparing only effectiveOn to the billing start instead of latest change.
- Racing on a SELECT outside the transaction.
- Returning a new receipt on retries rather than the recorded original.
- Dropping a network-error request key while retrying.
- Rendering stale preview data after an organization switch.
- Recomputing historical changes and damaging prior invoices.
- Removing existing note revision behavior to make new amendments easier.

## Recommended interview prioritization

**0–8 min:** Inspect fixture, live app, note revision path and baseline tests. **8–20 min:** Pure date/count validation and exact proration with focused tests. **20–38 min:** Atomic apply, durable key/receipt handling, conflict and no-op tests. **38–50 min:** HTTP endpoints and usable frontend preview/apply. **50–60 min:** Run build/tests, exercise replay/conflict manually and describe known gaps. Partial work with excellent invariants may outscore a flashy but nontransactional screen under the rubric.

## Walkthrough inspection points

Ask the candidate to show transaction boundaries and unique constraints, how a no-op receipt is retained, and why an exact replay works after an unrelated note edit. Inspect the exact integer rounding code and leap/month boundary tests. Trace frontend selection epoch and pending request state. Verify that existing note editing and tenant isolation remain intact. Reward explanations backed by executable checks; do not reward long unexamined AI diffs.
