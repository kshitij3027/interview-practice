# CycleLedger — HARD 60-minute AI-assisted full-stack interview

## Context

CycleLedger is a contract-operations console for a B2B SaaS vendor. Account managers oversee subscription contracts for several organizations. A contract has a plan, paid seats, a billing period, and a revision history. Seat changes during an active period create one-time prorated debits or credits for the next invoice.

## Existing behavior — already working

This is a Python 3.11+ SQLite-backed HTTP service with a dependency-free browser JavaScript application. You can switch organizations, search by customer or contract ID, filter by status, paginate, inspect contract details and prior seat-change history, and edit notes. Results sort by customer name then contract ID; total counts before pagination; notes are trimmed; no-op notes do not bump revisions; stale note edits return HTTP 409. Cross-organization contract lookups return 404, and late list/detail requests are ignored by the browser. **Preserve these behaviors.** Data persists in data/cycleledger.sqlite and is reset by deleting that file before restarting.

## Supplied data

fixtures/catalog.json contains **3 organizations, 3 plans, and 12 contracts**. Plans specify integer USD seat prices in cents and inclusive minimum/maximum seat limits. Each contract has a half-open billing period [periodStart, periodEnd), a seat count, revision, status and previously applied changes. These are historical records, not a working amendment system. Read them before starting. app/store.py, app/http.py, public/, and tests/ contain the functioning starter.

## Customer/business problem

A customer expands or reduces seats during a billing period. Finance needs the exact prorated one-time charge or credit for the remaining days. Operators must preview the adjustment, then safely commit it. Another operator may edit the contract during review; an HTTP response may be lost after a successful change. Retrying must not charge twice, and displaying a stale result for the wrong selected customer is unacceptable.

## Primary feature request

**Build ONE end-to-end subscription seat-amendment preview-and-apply workflow.** Let an operator choose a new seat count and effective calendar date, preview the server-authoritative adjustment and then apply the reviewed change with concurrency and retry protection. Coordinate domain logic, persistent storage, HTTP endpoints, browser behavior and focused tests. The requested feature is **not implemented**.

## Acceptance criteria — observable behavior

1. Add POST /api/contracts/:id/amendment/preview with JSON containing orgId, effectiveOn (YYYY-MM-DD), newSeats. Return contract ID, current revision, effective date, old/new seats, periodDays, remainingDays, signed amountCents, currency USD. Positive amounts are charges; negative amounts are credits. Preview must not modify any state.
2. An amendment is valid only when contract status is active, newSeats is a JSON integer (booleans do not qualify) within the plan's inclusive min/max, and effectiveOn is a real ISO calendar date within [periodStart,periodEnd). An existing change prohibits another effective date **on or before** its latest effectiveOn. Return 400 for invalid proposals, 404 for missing or cross-organization contracts.
3. Proration uses calendar days, including the effective date and ending immediately before periodEnd. signed amountCents = round_half_away_from_zero((newSeats-oldSeats)*seatPriceCents*remainingDays/periodDays). Use **exact integer arithmetic**, rounding once per amendment. Do not use floating-point money, implicit time-zone conversion or a fixed 30-day month. Use current authoritative seats.
4. Add POST /api/contracts/:id/amendment/apply with JSON {orgId,expectedRevision,effectiveOn,newSeats,requestKey}. On a successful change, atomically update seats, increment revision once, append an immutable change containing a unique change ID, effectiveOn, old/new seats and signed cents, and return a receipt. A valid same-seat proposal is a no-op: no revision increase or history append, but still returns a retry-safe receipt.
5. Stale expectedRevision returns HTTP 409 with useful current-contract information, even if the concurrent edit was a note. Concurrent requests may not double-apply. Rejecting a request must leave the contract unchanged.
6. requestKey is unique within each contract, matching 1–100 ASCII letters, digits, hyphen or underscore. An **identical logical replay** returns the original receipt after later unrelated edits. Reusing a key for different request fields returns 409 without mutation. Validate ownership before exposing details.
7. Add UI controls for new seats and effective date, preview a labeled charge/credit or no-op, apply the currently previewed request and display authoritative receipt plus updated seats/history. Invalidate previews on changed inputs, contract, organization or revision. Recover from 400/409/failed-network outcomes; a retry after an uncertain response must reuse the same key and payload. Late responses must not update a different selected contract.
8. Preserve the existing directory, pagination, note editing, isolation and stale-response protections; write focused tests for domain, API and retry/failure behavior.

## Constraints

Single server process with SQLite, but concurrent HTTP threads and out-of-order responses. Up to 100,000 contracts across organizations and 100 amendments per contract; avoid global scans for one contract update. Integer USD cents, real ISO dates, half-open periods, immutable historical billed amounts. Atomic receipt and change persistence must survive server restarts. No external services required.

## Scope / out of scope

In scope: one contract amendment preview/apply, persistent history/receipts, associated browser workflow and focused tests. Out of scope: payment collection, taxes, currencies beyond USD, renewal pricing, invoice delivery and authentication infrastructure.

## Setup, run and verify

Python 3.11+ required; Node.js is optional for JS syntax checking. No pip installation is needed.

    bash scripts/build.sh
    bash scripts/test.sh
    bash scripts/verify.sh
    bash scripts/run.sh

Open http://127.0.0.1:8080. To reset fixtures, stop the server and delete data/cycleledger.sqlite before running again. Starter tests verify only existing features, not the new capability.

## Your 60-minute AI-assisted interview

Use Claude Code, Codex, ChatGPT or similar tools if useful. Inspect code/data, choose a defensible approach, implement incrementally, verify outputs and explain tradeoffs. A one-shot AI patch is not sufficient without review. Be prepared to defend date arithmetic, chronology, atomic writes, idempotency, stale client state, and any remaining gaps.
