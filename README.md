# ReturnCredit — HARD 60-minute AI-assisted full-stack interview

## Context
A marketplace support team manages returns for orders containing multiple quantities of the same SKU. A customer may return just one unit now and the remaining units days later. Order-level discounts and tax make each returned unit's **actual credited amount** different from its catalog price. Shipping charges are not refunded. Support agents must not issue an accidental second credit when a request is retried or another agent edits the order.

## Existing behavior (already running)
The Node.js 20+ application is a standard-library HTTP service with a browser ES-module UI. Operators can browse orders sorted by newest `placedAt` instant, search order/customer, filter fulfillment status, inspect lines and historical refunds, and edit an operator note. Note edits require `expectedRevision`, trim whitespace, reject stale writes with HTTP 409, increment the order and dataset revisions once only when changed, and preserve unchanged revisions on no-ops. The browser ignores obsolete order-list/detail responses. Restart restores fixtures.

## Supplied data
`fixtures/orders.json` contains six orders, eight distinct line items, one prior refund, quantities, catalog unit prices, order-line discounts and tax, shipping, credited unit counts and money, notes and revisions. All money is **integer cents**. A line's customer-paid amount is `quantity * unitPriceCents - discountCents + taxCents`. The fixture contains lines where this amount is not evenly divisible by unit count. Historical refunded quantities and cents are already reflected in each line and are authoritative starting balances.

## Customer/business problem
The current console cannot issue additional partial-item refunds. Agents need one safe, explainable **Issue partial refund** operation for the selected delivered order. The backend owns refund eligibility, money calculations, available quantities, audit entries and concurrency. The browser supplies requested line quantities, not precomputed refund amounts.

## Primary feature request
Add a complete **partial item refund issuance** workflow across domain state, HTTP API, and browser. An operator selects positive quantities from one or more order lines, provides a reason, and submits once. The response explains the amounts per line and the overall credit. Repeated or delayed requests must not issue additional credits unexpectedly.

## Acceptance criteria
1. Implement `POST /api/orders/:orderId/refunds` accepting `{expectedRevision, requestKey, reason, items, delayMs?}`. Return the authoritative order, newly recorded refund (per-line amounts and total), and dataset revision. API errors should clearly describe invalid requests and stale revisions.
2. Only `delivered` orders may receive item refunds. `in_transit` and `cancelled` orders are ineligible. Reject unknown orders/line IDs, empty items, duplicate line IDs, zero/negative/fractional or unsafe integer quantities, and quantities exceeding unrefunded units. **No partial mutation on invalid input.**
3. `items` contains 1–50 distinct `{lineId, quantity}` entries. `reason` is trimmed and must have 4–120 characters. `requestKey` is trimmed and must have 8–64 characters. `expectedRevision` is a nonnegative safe integer. Optional `delayMs` is an integer from 0 to 1200 inclusive.
4. An order-line credit is based on its *customer-paid* total, including the line discount and tax, excluding shipping. Treat units as ordinal positions 1 through `quantity`: distribute the integer-cent line total as evenly as possible, with the earliest positions receiving any extra pennies. A refund consumes the **next** unrefunded ordinal positions. Thus returning 1 unit and later 2 units must credit the exact same sum as returning 3 at once; never recalculate a fresh proportional rounded share from only the remaining balance. Preserve prior refunded counts/cents.
5. Multiple selected lines are one atomic refund. Per-line refunded quantity and cents, `refunds` audit history, order revision and global dataset revision must reconcile. On one successful refund, increment **each revision exactly once** irrespective of line count. Do not mutate note, fulfillment status, shipping or other orders.
6. A normalized request identity consists of order ID, observed order revision, trimmed reason and `(lineId,quantity)` pairs sorted by line ID. Item input order is irrelevant. `delayMs` is not part of identity. A request key is globally unique across the process. Same key and same logical request returns the **original response** without another audit row or revision increase, even if the order has since changed. Reusing the key for a different logical request is a conflict, with no mutation.
7. A stale `expectedRevision` must fail with HTTP 409 and include the current order revision. Check again **after** optional delay, immediately before changing state. A note edit or another refund during the delay must make the older refund fail atomically. Concurrent requests with identical keys must never double-issue credits. Retry outcomes must remain stable.
8. The browser must offer an understandable per-line quantity form, reason field, credit results and outstanding quantities; reconcile current order, history and revisions after success without full reload. Disable accidental duplicate submissions of the same pending action while keeping normal browsing functional.
9. Changing the selected order or applying a new filter while a refund is in flight must not allow an old result to repaint the new context. A failed HTTP request preserves last-known-good order data and entered refund inputs where possible; a stale response should allow the agent to recover using refreshed state.
10. Preserve all existing order list/search/status behavior, note editing, revision/no-op semantics and starter tests. Add targeted tests for money conservation, prior-refund rounding, multiple lines, stale writes, same-key retries, idempotency collisions, concurrent requests and browser race behavior.

## Scale and constraints
Production resembles 80,000 orders, with up to 300 lines per order and many incremental refund requests per line. Avoid sweeping the entire order collection when refunding one selected order. Use integer-cent arithmetic and safe integers; no float-based currency calculations. Keep Node.js standard library, one process, fixture-backed in-memory store, and dependency-free ES modules. No npm install is needed.

## Scope and out-of-scope
Deliver runnable domain/API/UI behavior, regression-safe validation, and tests. Out of scope: payment-provider calls, real fund disbursement, authorization, persistence after restart, distributed locks, restocking, rest-of-order cancellation, shipping refunds, and cosmetic polish.

## Setup, run and verify
```bash
./scripts/test.sh
./scripts/build.sh
./scripts/verify.sh
./scripts/run.sh
```
Open `http://localhost:8080`. On another port use `PORT=8081 ./scripts/run.sh`. Starter tests establish existing behavior only; they are not comprehensive feature acceptance tests.

## 60-minute AI-assisted interview instruction
You have exactly **60 minutes**. Claude Code, Codex, ChatGPT and similar tools are permitted. Inspect `README.md`, fixtures, API contracts, the existing note mutation, browser state and tests before implementing. Choose your own implementation strategy; implement incrementally, verify the money/quantity edge cases and defend how retries, stale writes, and client reconciliation work. A one-shot happy-path change is insufficient.
