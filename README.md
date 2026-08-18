# FulfillFlow — HARD One-Hour Full-Stack Interview Exercise

## Context
FulfillFlow is an internal fulfillment console for a commerce platform. Support and operations teams use it to inspect pending customer orders, check warehouse inventory, and make audited manual stock corrections when physical counts differ from the system.

The starter application already works. It uses a dependency-free Java 21 HTTP API, an in-memory domain store loaded from CSV/JSON fixtures, and a browser ES-module frontend with explicit client state. Existing tests cover inventory loading, availability, order lookup, and optimistic stock adjustment.

## Existing behavior
- The dashboard lists pending orders and their line items.
- Inventory is shown per SKU and warehouse with `on_hand`, `reserved`, and derived `available` quantities.
- Operators can filter inventory by SKU.
- Operators can apply a manual stock adjustment with a non-empty reason.
- Manual adjustments use the global inventory `revision`; stale writes are rejected.
- An adjustment may not reduce `on_hand` below the quantity already reserved.
- Successful adjustments increment the inventory revision exactly once.
- Restarting the server reloads fixture state.

## Customer/business problem
Checkout currently accepts orders before fulfillment capacity is secured. Agents need a short-lived reservation workflow so they can hold stock while confirming a customer's order, without letting two orders consume the same units or leaving inventory permanently reserved if a checkout is abandoned.

Orders may contain the same SKU on more than one line. Inventory is spread across multiple warehouses, and the business wants predictable allocation so support can explain why stock came from a particular location.

## Primary feature request
**Add an expiring order-reservation workflow that atomically holds all required inventory using deterministic warehouse allocation, then lets the operator confirm or release that hold with retry-safe and stale-state behavior.**

## Acceptance criteria
1. Add a reservation workflow to the existing order detail UI. An operator must be able to reserve a pending order, see the resulting hold/allocation, then confirm or release that hold without reloading the browser.
2. Before allocation, quantities for duplicate order lines with the same SKU must be aggregated. A SKU must not be planned independently twice just because it appears on two lines.
3. A reservation is all-or-nothing across the order. If the full aggregated quantity of any SKU cannot be held, create no hold and mutate no inventory. Return shortage details per unavailable SKU.
4. Availability is `on_hand - reserved` after ignoring/releasing expired holds. An active hold from another order must reduce what this reservation can use.
5. Warehouse choice must be deterministic. For each SKU, allocate from warehouses in this order: warehouses matching the order's `shipping_zone` first, then lower numeric `pick_rank`, then lexicographically smaller warehouse ID. Splitting a SKU across warehouses is allowed.
6. Reservation creation must include the inventory revision observed by the client. If that revision is stale, reject before creating a hold or changing any reserved quantity.
7. Reservation creation must include a client-generated request key. Retrying the same request key for the same order must return the same reservation result and must not reserve stock twice. Reusing that key for a different order must be rejected clearly.
8. A successful reservation creates a hold that expires exactly **10 minutes** after its server-side creation time, increments the inventory revision exactly once, and changes the order from `pending` to `held` with one order-revision increment.
9. At most one active hold may exist for an order. A second non-idempotent reserve attempt must not create another allocation for that order.
10. Confirming an active, unexpired hold must atomically consume its allocation: decrement both `on_hand` and `reserved` by the held quantities, mark the hold `confirmed`, change the order to `fulfilled`, and increment the inventory revision exactly once for the confirmation.
11. Confirm retry must be safe. Repeating confirmation of the same already-confirmed hold must return the prior successful outcome without consuming inventory or incrementing revisions again.
12. Releasing an active hold must return its reserved quantities to availability, mark the hold `released`, return the order to `pending`, and increment the inventory revision exactly once. A repeated release must not double-release stock.
13. Expiry is authoritative on the server. At `expires_at` or later, an active hold can no longer be confirmed. Expired reserved quantities must be released exactly once, and the client must reconcile the order/inventory state when it discovers expiry.
14. Existing manual stock adjustment must continue to work. While a hold is active, an adjustment that would make `on_hand < reserved` must still be rejected; after release/expiry, that same adjustment may become valid.
15. After reserve, confirm, release, stale-revision failure, or expiry failure, keep the currently selected order visible and reconcile the displayed order, inventory revision, and availability. A transient request error should not erase the last known-good order data.

## Constraints
- Keep the Java 21 + browser ES-module stack.
- Keep state in one process and in memory. No database, Redis, queue, auth system, or external service.
- The backend is authoritative for allocation, hold state, expiry, and retries.
- You may add domain/service classes, routes, frontend state/actions, and focused tests.
- Use integer quantities only; inventory units are indivisible.
- Do not replace the existing manual stock-adjustment workflow.

## Out of scope
- Payment processing.
- Shipping labels or carrier integrations.
- Backorders or partial-order reservations.
- Multi-process/distributed locking.
- Persistence across server restarts.
- Authentication/authorization.
- Styling polish beyond a clear usable workflow.

## Setup / run

```bash
./scripts/build.sh
./scripts/test.sh
./scripts/run.sh
```

In another terminal:

```bash
python3 -m http.server 5173 -d web
```

Open `http://localhost:5173`.

## Tests / build

```bash
./scripts/test.sh
./scripts/build.sh
```

Existing tests cover current behavior only. Add focused feature tests based on the requirements; there are intentionally no feature TODOs or starter tests that encode the reservation solution.

## 60-minute interview instruction
You have **60 minutes**. Treat this as a demanding AI-assisted live coding interview. Inspect the existing store, service boundaries, API contract, frontend state flow, and fixtures before changing code. Identify the highest-risk correctness semantics, implement incrementally, and verify both server behavior and the browser flow.

A polished reservation button with incorrect atomicity, allocation order, expiry, idempotency, revision handling, or inventory accounting should not be considered a strong solution. Prioritize correctness and observable verification over visual polish.
