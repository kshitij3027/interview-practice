# OfferStream — HARD 60-minute AI-assisted full-stack interview

## Context

OfferStream is a training operations console for organizations that run small, capacity-limited workshops. Registrations can be confirmed, waiting, or cancelled. Staff need a dependable way to offer newly freed seats to people on a session's waitlist without overselling a workshop or repeatedly contacting the same person.

## Existing behavior (working before you start)

This starter is a Node.js 20+ standard-library HTTP server, in-memory fixture-backed workspace, and vanilla JavaScript staff console. You can choose an organization, search and filter sessions by phase, paginate with stable ID ordering, inspect a session's registrations, and edit staff notes. List totals are computed before pagination. Note saves trim whitespace, preserve revision on no-op, and return a 409 with current authoritative session state on stale writes. Cross-organization sessions are hidden with 404. The browser ignores late responses from previously selected sessions and organizations. **Do not regress existing behavior.** State resets when the server restarts.

## Supplied data

`fixtures/workspace.json` contains 3 organizations, 6 sessions and 17 registrations. A session has `id`, `orgId`, `title`, `phase` (`open` or `closed`), positive `capacity`, `revision`, `note`, `people`, and `offers`. Each registration has a stable ID, display name, status (`confirmed`, `waiting`, `cancelled`) and RFC3339 `joinedAt` instant. An offer, when present, has `id`, `personId`, `createdAt`, `expiresAt` and stored status (`pending`, `accepted`, `declined`). Inspect the existing fixtures and code. They intentionally include equal waitlist timestamps, full sessions, closed sessions, and cancelled registrations. Initial offers may be empty; the field is part of the data contract.

## Customer/business problem

A trainer cancels, freeing space in a session with many waiting registrations. Staff offer those places to the people waiting longest. An outstanding offer temporarily reserves a place and expires after 20 minutes. Another staff member may modify a session or advance the waitlist at the same time, while the recipient's response may arrive after expiry. If a successful request loses its HTTP response, retries must return the **original result**, not generate another offer or accept twice. The console must display authoritative capacity and recover when an operator is looking at old data.

## Primary feature request

**Build one end-to-end waitlist seat-offer workflow.** A staff operator should see availability at a chosen evaluation time, issue offers to eligible waiting registrants, and accept or decline an outstanding offer. Implement the HTTP contract, server-owned business state, browser interactions, and targeted tests. This feature is deliberately **not implemented** in the starter.

## Acceptance criteria — observable behavior

1. Add `GET /api/sessions/:id/availability?orgId=...&asOf=...`, returning `{sessionId,revision,asOf,capacity,confirmed,held,free,offerableWaiting,offers}`. `asOf` is a valid RFC3339 instant. `offers` must include every offer with an `effectiveStatus` of `pending`, `expired`, `accepted`, or `declined`, as assessed **at the supplied instant**; retain the stored original creation/expiry timestamps. `confirmed` counts confirmed registrations, `held` counts pending offers only when `createdAt <= asOf < expiresAt`, and `free = max(0, capacity-confirmed-held)`. The response must be read-only and deterministic for the same data and instant.
2. Add `POST /api/sessions/:id/advance?orgId=...` accepting `{expectedRevision,asOf,requestKey}`. A successful call issues as many offers as available seats, up to the number of eligible waiting registrants. Each new offer lasts exactly **20 minutes** starting at `asOf`, has a unique stable ID, and reserves one seat. Return `{receipt:{requestKey,sessionId,revision,createdOffers},session:<authoritative session>}`. When no offers can be issued, return an empty `createdOffers` with no revision increment. For a nonempty advance, increment the session revision exactly once, regardless of how many offers were issued.
3. Eligible people are `waiting` in an `open` session and have **never previously received an offer in that session**, regardless of whether that earlier offer is pending, expired or declined. Choose candidates in ascending `(joinedAt instant, personId)` order, not the order of the fixture array; identical timestamps must have a reproducible winner. Do not issue offers to confirmed/cancelled people or re-offer the same person. A closed session cannot advance. For an already full session, issue no offers, not an over-capacity batch.
4. Add `POST /api/sessions/:id/offers/:offerId/respond?orgId=...` accepting `{expectedRevision,asOf,choice,requestKey}` with `choice` exactly `accept` or `decline`. Only an offer in `pending` state, at a time satisfying `createdAt <= asOf < expiresAt`, can be acted upon. Acceptance changes the registration status to `confirmed` and the offer to `accepted`; decline changes the registration to `cancelled` and the offer to `declined`. A successful first response increments the session revision once and returns `{receipt:{requestKey,sessionId,offerId,choice,revision},session:<authoritative session>}`. A late response at exactly `expiresAt` must fail without modifying state. An expired offer has released its seat even if its stored status still says `pending`.
5. For both POST operations, validate that `expectedRevision` is a nonnegative safe JSON integer (not a Boolean), `requestKey` is 8–64 ASCII letters/digits/hyphens/underscores, and `asOf` is a valid RFC3339 timestamp including a timezone offset. Treat different textual offsets representing the same instant identically for time comparisons. Disallow requests with `asOf` **earlier than** the session's last successful mutation time (maintain this value server-side, initially unset); prevent time-travel changes. Return structured `{error:{code,message,...}}` with HTTP 400 for invalid inputs, 404 for missing/hidden resources, and 409 for stale revisions or conflicting/rejected transitions. Failed attempts may not partially mutate the session.
6. Successful `requestKey`s are unique within an organization across both operations. A retry with the same key and identical logical intent `(operation,sessionId,offerId or null,expectedRevision,asOf instant,choice or null)` must return the **original receipt and session snapshot** unchanged, even if subsequent edits occurred. Reusing a key with different intent returns 409 `KEY_CONFLICT`. A failed request does not reserve a key. Check successful replays before rejecting a stale revision; do not allow two concurrent actions to overbook or double-accept.
7. The browser must show authoritative capacity/held/free and offer statuses for the selected session, a control to advance the waitlist, and controls to accept/decline pending offers. Display pending, success and failure states clearly. Refresh the selected session, availability and list data after success **without a page reload**. Show server errors and stale-revision conflicts; on conflict refresh authoritative data before allowing a new intent. A transport failure may mean success: allow retry with the **same requestKey and identical payload**, not a fresh mutation. Ignore late responses when the organization, session, or evaluation time changes.
8. Preserve current organization isolation, search, phase filtering, pagination, notes, revision protection, and late-response handling. Notes and offer actions must invalidate each other's stale revisions. Add focused tests covering capacity, ordering, expiry boundaries, replay after later changes, key collision, invalid input, concurrent-looking operations, and read-only availability. Repeated observation at the same instant should never consume seats or change revisions.

## Constraints

- One Node.js 20+ process, no external packages or persistence service. Use the supplied in-memory workspace and browser. Do not use an external ticketing, booking, LLM or messaging platform.
- Capacity is hard: confirmed people plus live holds **must never exceed capacity** after a successful operation. Expired holds do not occupy seats. Offer IDs must be unique within a session and immutable once issued.
- The API decides eligibility and capacity; never trust client-submitted candidate lists, free-seat counts, or locally invented receipts.
- Dates are instants, not local calendar days. Use consistent half-open offer lifetimes and unambiguous ISO output.
- Production can have 100,000 registrations in a session, 50,000 historical offers, and bursts of repeated submissions. Explain what you would index or cache rather than repeatedly recomputing everything per displayed row.
- Keep the requested change one coherent feature. Prefer a correct vertical slice, focused regression tests and defensible tradeoffs over a broad rewrite.

## Out of scope

Sending emails/SMS, cancellation of an already confirmed registration, changing workshop capacity, re-offering a declined or expired person, undoing accepted offers, external authentication, multiple server processes, durable storage, scheduling background timers, and visual polish.

## Setup, run and verify

Use Node.js 20 or newer. No dependency installation is needed.

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
bash scripts/run.sh
```

Open `http://127.0.0.1:8080`. Example existing endpoint:

```bash
curl 'http://127.0.0.1:8080/api/sessions?orgId=org-cedar&limit=5'
```

## 60-minute AI-assisted interview instruction

You have **exactly 60 minutes**, and AI coding assistants such as Claude Code, Codex or ChatGPT are allowed. Explore the app, data and tests first; choose and implement a defensible design across domain, API and browser. Test against meaningful edge cases and demonstrate an end-to-end workflow. Be ready to discuss correctness, time-bound semantics, concurrency, retry behavior, cost at scale, what you deliberately left out, and how you used and reviewed AI output. The intended implementation is not supplied.
