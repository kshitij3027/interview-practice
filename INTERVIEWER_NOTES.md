# POST-PRACTICE ONLY — Interviewer Notes

**Do not read this file before completing the 60-minute exercise.**

## Intended solution outline
A strong solution introduces a small reservation/hold domain model and keeps the mutation boundary inside one synchronized store/service operation. Order lines are first aggregated by SKU. Before planning, expired active holds are reaped once, returning their reserved quantities and updating order state/revisions consistently. The planner then reads current availability and, for each SKU, walks warehouses in deterministic business order: shipping-zone match first, then `pick_rank`, then warehouse ID. It creates an in-memory allocation plan without mutating live inventory. Only after every SKU is fully satisfiable does it apply all reserved increments atomically.

Reservation creation should associate the request key with the order and resulting hold outcome. The same key/order returns the same result; the same key/different order conflicts. The hold should record creation time, expiry time, allocations, lifecycle state, and enough prior result data for retry-safe confirm/release behavior.

Confirm and release should be state-machine transitions guarded by the same mutation boundary. Confirmation consumes both `on_hand` and `reserved` for each allocation; release only reduces `reserved`. Each successful logical transition increments inventory revision once, not once per allocation. Order revisions should follow the required state transitions. The client should refresh/reconcile selected order and inventory after every server outcome without discarding last known-good detail on transient errors.

## Subtle traps / hidden checks
- `ord-1002` contains `SKU-GRN` twice. Treating lines independently can produce incorrect shortage/allocation behavior.
- Reservation must be planned before mutation. A shortage discovered on the final SKU must leave earlier SKUs untouched.
- Existing `reserved` values must reduce availability, and newly created holds must affect subsequent reservation attempts.
- Zone preference is a primary sort key; `pick_rank` does not globally outrank a zone match.
- Determinism must survive reordering the inventory fixture/list.
- Same-key retry should not create a second hold or increment revisions.
- Same key on another order should not silently return the first order's hold.
- A second fresh key for an already-held order should not reserve again.
- `now >= expires_at` means expired. Off-by-one-time comparisons are a likely failure mode.
- Expiry cleanup must be idempotent. Repeated reads after expiry must not keep incrementing revisions or releasing inventory.
- Confirming an expired hold must not consume stock.
- Confirm retry after success must not double-decrement `on_hand`.
- Release retry must not make `reserved` negative.
- A manual stock adjustment that would violate `on_hand >= reserved` must still fail while a hold is active.
- Stale reserve requests must fail before any reservation state is created.

## Expected prioritization
1. Model aggregate order requirements and deterministic allocation as a pure/testable helper.
2. Implement atomic reservation creation with stale revision and idempotency handling.
3. Add confirm/release lifecycle transitions and expiry handling.
4. Add focused domain tests for atomic shortage, allocation order, retries, and expiry.
5. Wire a minimal frontend flow and reconciliation.
6. Polish UI only after lifecycle correctness is verified.

## Likely failure modes
- Mutating `reserved` while still discovering whether later SKUs are available.
- Using inventory/file order directly instead of explicit warehouse sorting.
- Forgetting to aggregate duplicate SKU lines.
- Generating a new hold on request-key retry.
- Incrementing inventory revision per warehouse allocation.
- Expiring a hold in multiple read paths and decrementing `reserved` repeatedly.
- Treating confirmation as `on_hand -= qty` but forgetting `reserved -= qty`.
- Clearing selected order or UI data after a recoverable 409/expired response.
- Implementing the authoritative allocation in the browser and sending selected warehouse rows to the server.
- Breaking the existing stock-adjustment stale-write behavior while refactoring the store.

## What to inspect after the hour
Inspect whether the candidate found and preserved the existing stock-adjustment invariants, isolated deterministic allocation from mutation, used one atomic mutation boundary for each lifecycle transition, modeled retries explicitly, tested expiry without relying on real ten-minute waits, and verified both server state and browser reconciliation. A strong candidate should be able to explain which requirements they intentionally prioritized if they did not finish every UI detail.
