# POST-PRACTICE ONLY — ReturnCredit Interviewer Notes

**Evaluator-only material. Never reveal during a 60-minute candidate attempt.**

## Intended underlying challenge
One full-stack partial-refund feature combining an order-local accounting invariant with safe state mutation and asynchronous UI reconciliation. This is not a prescribed architecture or an LLM requirement. The primary conceptual trap is that line discount and tax must be allocated across individual ordinal units in *integer cents* consistently over successive partial refunds. The second challenge is exactly-once logical issuance despite retries, stale revisions and network races. A one-shot happy path normally misses at least one.

## What the candidate should discover in the supplied data
ORD-201 / LN-A has customer-paid line total 3 * 1599 - 200 + 93 = 4690 cents. The exact ordinal unit values are 1564, 1563, 1563. The first unit has already been refunded for 1564 cents; refunding the remaining two must credit 3126 cents, not 3127. LN-B has line total 2 * 4200 - 500 + 302 = 8202 cents, or 4101 each. A multi-line request refunding remaining LN-A x2 plus LN-B x1 totals 7227 cents. Shipping is never part of the credit.

ORD-205 / LN-G has paid amount 3 * 1299 + 235 = 4132 cents, partitioned 1378, 1377, 1377. ORD-206 / LN-H has 2 * 299 - 100 + 25 = 523 cents, partitioned 262 and 261. Different refund chunkings must sum to the same original paid line total.

The existing note path is a model of how order revision and global dataset revision interact. Current order status, notes, revisions, existing refund history and the original shipped charge must remain consistent throughout the feature.

## Strong implementation outline
1. Define one normalized request contract: order ID, expectedRevision, trimmed reason, sorted unique pairs (lineId, quantity), globally unique trimmed requestKey, and bounded optional delayMs excluded from identity. Reject malformed requests before mutations.
2. Keep the immutable line pricing facts distinct from credited quantity/cents and recorded refund history. Validate eligibility only for delivered orders and bound quantities by remaining units. The server must not accept a client-computed total.
3. For line paid total A and quantity Q, define base=floor(A/Q) and extra=A mod Q. A zero-based ordinal i has price base + 1 when i < extra. For R units previously refunded and n newly returned, the exact credit is n*base + max(0, min(R+n,extra)-min(R,extra)). Equivalent prefix differences are fine. Validate safe integers, staged sum overflow and conservation against historical refundedCents.
4. Stage all per-line changes and audit entries. After any simulated delay, re-check the revision and idempotency record, then apply all lines and one audit entry in one synchronous critical section with exactly one order and dataset revision bump. Do not await between state writes. Rejected requests mutate absolutely nothing.
5. Maintain a process-global key registry mapping requestKey to normalized fingerprint and the original final successful response. The matching prior key must replay its original outcome before rejecting an otherwise stale revision. A conflicting fingerprint never applies. Re-check registry after delay to avoid two same-key requests both committing. Tracking in-flight promises is an alternative defensible design.
6. Return structured item amounts and authoritative new detail. The browser owns only requested quantities and reason. Refresh current order/list state after success, show the breakdown, and preserve entered values on request/network failure. Scope old async responses by selected order and generation counter to prevent overwriting newly selected context.

## Runtime complexity and tradeoffs
With an order-by-ID map, lookup is O(1) average, validating its L line items and K selected items costs O(L+K log K) if the K item pairs are sorted, and staging is O(K) extra memory. An indexed per-order line map can make item lookup O(K) plus sorting. Never sweep 80,000 global orders to refund one order. Mathematical penny allocation requires O(1) per requested line regardless of its quantity. A naive per-unit array wastes memory when quantities are huge.

In this single-process Node starter, checking and mutating without an await after the simulated delay is a defensible atomic boundary. In a real service, durable database transactions and payment-processor idempotency are required. A forever-growing in-memory key registry is adequate only for this exercise; a production TTL/durability design requires explicit requirements. Alternative integer-safe prefix accounting is equivalent. External integrations are out of scope.

## Hidden / manual checks
- ORD-201 LN-A x2 from seeded state returns exactly 3126 cents and finishes with refundedQuantity=3 and refundedCents=4690; one order revision bump from 3 to 4 and one dataset bump from 1 to 2.
- ORD-205 LN-G x1 then x2 returns 1378 then 2754; ORD-206 LN-H x1 then x1 returns 262 then 261. The batch/chunking sum must conserve original cents.
- ORD-201 combined LN-A x2 and LN-B x1 returns exactly 7227 cents; one audit entry and one pair of revision increases, not per-line increases. Note and shipping remain unchanged.
- A request for LN-A x3 when one unit is already refunded is invalid. When the first line is valid and a later line invalid, no line, refund history or revision may mutate.
- Reject unknown order or line, duplicate item ID even when quantities agree, noninteger/negative/zero/unsafe quantities, empty list, blank reason/key after trim, non-delivered order, invalid expectedRevision and delay outside 0..1200.
- Item order permutations and whitespace-normalized reason/key are logically identical. Different reason, line or quantity under the same key conflicts globally, including another order. Optional delayMs does not enter fingerprint.
- After successful same-key request, an intervening operator note edit must not make replay fail stale or issue a second refund. Return the *original* recorded response, not newly fabricated current values.
- Two same-key requests started concurrently with delays must produce one refund. Two distinct keys with identical observed revision must not both succeed after a race; one stale request mutates nothing.
- Delay refund, then edit the order note while it waits: revision must be rechecked after delay and old request must reject without changing credits.
- After a successful refund the history item totals equal the refund total; line refunded cents never exceeds paid cents; order shipping/status and all other orders stay unchanged.
- Change selected order or filters during in-flight refund. An old response may finish its server mutation but must not repaint a new selection. Test network failure preserving last-known-good detail and entered quantities/reason. Existing note no-op and stale behaviors must still pass.

## Why naive approaches fail and likely AI-agent mistakes
Catalog price multiplied by quantity ignores line discounts and tax. Floating-point rounding per request leaks or invents pennies when returns are split. Reaveraging the *remaining* line total can move extra pennies to the wrong ordinals. Using the browser as the money authority creates stale and tamperable credits. Applying line mutations while still validating later lines allows partial credits. Incrementing revisions per line violates the request boundary.

An idempotency check only before await is insufficient if two same-key requests enter concurrently. Checking staleness before replay lookup wrongly rejects legitimate retry of already committed request. A delayed stale request that checks freshness only before its delay can double-refund. Older browser responses that blindly draw after await overwrite newly selected order, filter or newer detail. AI agents frequently implement a single happy-path endpoint and generic success UI but omit these checks.

## Recommended interview prioritization and inspection points
Minutes 0–8: inspect fixtures and existing note/list/API/browser boundaries; articulate exact cent and quantity invariants.
Minutes 8–25: implement and unit-test money semantics for the seeded uneven cases and prior refunds; normalize input and stage changes.
Minutes 25–39: wire HTTP, revisions, global key replay/collision and post-delay stale checks; demonstrate races.
Minutes 39–52: add refund quantities/reason controls, result breakdown, client reconciliation and stale response protection.
Minutes 52–60: run baseline commands, add edge tests, inspect an actual refund audit and explain remaining tradeoffs.

Ask the candidate to walk through ORD-201's historical refund math, show where validations finish before mutations, explain exactly why a same-key replay is safe after a newer order revision, identify the single revision-bump boundary, prove concurrency with overlapping delay requests, and show why navigation during a slow call does not corrupt the browser's visible order.
