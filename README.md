# Ledger Lens — HARD One-Hour Full-Stack Interview Exercise

## Context

Ledger Lens is an internal billing-operations tool for a SaaS company. Finance operators use it to inspect customer balances, open invoices, and record occasional manual credits.

The starter application is intentionally already functional. It has a Python/FastAPI backend with in-memory domain state and a dependency-free browser ES-module frontend with an explicit client-side store. Existing behavior spans account routes, domain services, invoice state, frontend API helpers, and detail views.

## Existing behavior

- The account list shows customer name, external customer reference, available credit, and a revision number.
- Selecting an account shows that account's invoices and current remaining balances.
- Operators can add a manual customer credit with a positive amount and non-empty reason.
- Manual credits increase the account credit balance and its revision.
- The backend is the source of truth; restarting it resets sample data.
- Existing tests cover current account, invoice, and manual-credit behavior.

## Customer/business problem

A payment partner sends Finance a settlement CSV several times per day. Operators currently reconcile those rows by hand against customer invoices. The export is not perfectly clean: customer references may have whitespace/casing differences, rows may be duplicated, malformed rows can appear, and an account may change between the time an operator previews an import and the time they apply it.

A representative file is provided at `fixtures/customer_settlement_aug14.csv`.

Finance wants a workflow that lets an operator inspect what the import would do before committing it, then safely apply the same reconciliation plan without silently using stale account state.

## Primary feature request

**Add a settlement-import workflow that previews a pasted/uploaded CSV, deterministically reconciles valid payments against open invoices, and then commits that exact preview safely with duplicate and stale-state protection.**

## Acceptance criteria

1. Add a UI flow where an operator can load/paste CSV content and request a **preview** without mutating server state.
2. Parse the columns `payment_id`, `customer_ref`, `amount`, `received_at`, and `note`. Header order may vary. Empty trailing lines must not create rows.
3. Resolve `customer_ref` after trimming surrounding whitespace and comparing case-insensitively to account `external_id`. Unknown customers must be reported as row-level errors, not abort the entire preview.
4. `amount` must represent a strictly positive dollar amount with at most two decimal places and must be converted without floating-point rounding drift. Malformed rows must be reported individually while other valid rows continue through preview.
5. Within one file, repeated `payment_id` values represent the same external payment. Exactly one occurrence may be considered for reconciliation; later duplicates must be identified deterministically and must not double-count money.
6. For each valid, non-duplicate payment, allocate money only to that customer's **open** invoices, ordered by earliest `due_date`, then lexicographically by invoice `id`. Partial invoice payment is allowed. Any remainder becomes account credit.
7. The preview response must contain enough information for the UI to show, per input row, whether it is valid/error/duplicate and, for applicable rows, the proposed invoice allocations and proposed remainder-to-credit. It must also expose the account revisions the plan was based on.
8. Previewing must not change invoice balances, invoice statuses, account credits, account revisions, or existing manual-credit behavior.
9. Add a **commit** action that applies the exact previewed plan. The server must reject the commit if any affected account revision no longer matches the revision used by that preview; it must not partially apply a stale plan.
10. A successful commit must update invoice `remaining_cents`, mark invoices `paid` when their remaining balance reaches zero, add any payment remainder to account credit, and increment each affected account revision exactly once for the whole committed import (not once per row or allocation).
11. Re-committing the same preview/import must be retry-safe: it must not apply payments twice. The client must be able to distinguish an already-committed retry from a genuinely invalid/stale request.
12. After commit success, refresh/reconcile the account list and currently selected account detail without requiring a browser reload.
13. If commit fails because the preview is stale, preserve the imported CSV in the UI, show a useful stale-state message, and make it straightforward for the operator to generate a fresh preview.
14. Existing manual-credit behavior must continue to work and must still participate in revision changes, so a manual credit created after preview can invalidate a settlement commit.

## Constraints

- Keep the backend in-memory; no database, Redis, queue, auth provider, or external API.
- You may add endpoints, service/domain modules, shared response types, and tests as needed.
- Treat a preview as server-owned state: do not trust the client to send arbitrary invoice allocations back and have the server apply them blindly.
- Keep the implementation interview-sized. You do not need production persistence across backend restarts.
- Use integer cents for persisted monetary values.

## Out of scope

- Authentication/authorization.
- Multi-process/distributed coordination.
- Persisting imports across process restarts.
- Supporting quoted CSV fields containing embedded newlines.
- Fancy drag-and-drop upload UI or visual design polish.
- Reconciliation reversals/refunds.

## Setup / run

Backend:

```bash
python -m uvicorn backend.app.main:app --reload --port 3001
```

Frontend (separate terminal):

```bash
python -m http.server 5173 -d frontend
```

Open `http://localhost:5173`.

## Existing tests and build

```bash
pytest -q
./scripts/verify_frontend.sh
```

## 60-minute interview instruction

You have **60 minutes**. Treat this as an AI-assisted product-engineering/FDE live build. Inspect the existing system and the fixture before coding. Decide what to make correct first, implement incrementally, and verify the most failure-prone behavior rather than trying to maximize code volume.

A complete happy path without careful handling of duplicates, deterministic allocation, stale previews, retries, and existing revision behavior is intentionally not a complete solution.

**Do not read `INTERVIEWER_NOTES.md` until after you finish the exercise.**
