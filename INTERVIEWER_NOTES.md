# OfferStream — Interviewer notes

**POST-PRACTICE ONLY. DO NOT SHOW TO THE CANDIDATE BEFORE OR DURING THE HOUR.**

## Intended underlying structure

This is a bounded resource allocation/state-machine problem, NOT a text classification or UI-only exercise. Model confirmed registrations plus unexpired pending offers as the consumed seats at an instant. Issue time-limited seat holds to eligible waiting registrations in stable priority order. Offer creation and response are state transitions guarded by revision, logical time and idempotency. The current API is deliberately small and synchronous; in a single Node event loop, synchronous check-and-mutate can serve as a per-process critical section if no `await` separates validation and mutation. A database transaction/unique indexes would be necessary in a multi-process version.

## Strong solution outline

- Add a domain service for `availability(session, asOf)`, `advance(session, args)` and `respond(session, offerId, args)` or comparable clearly separated logic. Validate tenant ownership before exposing mutable details. Return cloned snapshots and immutable receipts.
- Parse RFC3339 with an explicit `Z` or `±HH:MM` timezone, reject normalization of invalid calendar dates (e.g. Feb 30), invalid timezone offsets, empty strings, garbage suffixes, JSON booleans and unsafe revisions. Convert all instants to integer epoch milliseconds for comparison and idempotency; canonical UTC ISO strings are acceptable output.
- Compute `held` for pending offers satisfying creation <= asOf < expiry; accepted offers have already changed participant status to confirmed and must not double count. Compute `free` as capacity minus confirmed minus held, floored at 0. Status `expired` is derived for reads, while stored `pending` may remain unchanged. If a stale offer is not accepted, its person remains waiting but permanently ineligible for another offer by the same session.
- Advance only open sessions, choose waiting people without any prior offer. Sort candidates by parsed `joinedAt` ascending, then `personId` ascending. Reserve at most `free`; create immutable unique offer IDs such as `offer-${sessionId}-${counter}`. Multiple offers in a successful batch cause one revision increment. Zero offers yields a receipt without revision change. `asOf` can be equal to last mutation time, not earlier.
- Respond only to still-live pending offers, make acceptance `confirmed` and decline `cancelled`. Never accept at exactly expiry. Both action types update last-successful-mutation instant atomically, and return snapshots. A no-op advance is still a successful recorded request and can move the latest action time forward; spec permits defining whether zero-offer action counts as a mutation timestamp so long as requests cannot go back in time and that behavior is documented.
- Idempotency map keyed by `(orgId,requestKey)` stores operation + full canonical intent and deep-frozen/cloned original receipt + session snapshot. After tenant validation and request schema validation, check exact-key replay before revision check; mismatched intent gets `KEY_CONFLICT`. Failed attempts must not create map entries. This handles responses lost after a successful mutation, including later note edits. Avoid relying solely on `expectedRevision` for dedupe.
- Use strict 404 across organizations; structured `400` for invalid body and timestamp; `409` for stale, expiry/invalid transitions, backwards clock and key collision. If promises/DB writes are introduced, lock or transactionally serialize authoritative checks + writes.
- Browser: make the selected session and evaluation time part of an interaction epoch; render authoritative availability, offers and counters. Do not generate a new request key for an uncertain delivery retry. Hold the exact submitted payload. After success, refresh list/detail/availability; after 409, show error and refresh authoritative snapshot without silently rewriting user intent. Existing note UI must keep working.

## Complexity and scale

Naive per-read rescans of 100k participants and 50k offers are O(P+O), and sorting all waiting people for each advance is O(P log P). That's acceptable for the tiny starter and a 60-minute vertical slice if explicitly acknowledged, but ideal scale uses an index of eligible waiting registrations ordered by `(joinedAt,personId)`, a map of offers by ID/person, and an expiry-ordered structure for fast live-hold counts. A maintained availability ledger can update in O(log P + log O) per offer plus O(k log P) for k offers; state read can be O(k) for returned offers (or paginated in production). Avoid trusting browser counts or rerunning the whole `people` array per row.

## Why naive implementations fail

- `capacity - confirmed` disregards still-live holds and leads to overbooking.
- Treating every stored `pending` offer as held disregards expiry and strands seats.
- Comparing timestamps as strings mishandles offset-equivalent instants; milliseconds parsed consistently are required.
- Sorting the fixture order or sorting joinedAt alone produces unstable tie choices; stable person ID tie-break is required.
- Bumping revision once per offer gives wrong revision and needless stale conflicts.
- Updating status before confirming all preconditions permits partial mutations on errors.
- Replaying only if the session revision matches rejects successful retries after unrelated edits.
- Using new keys for network retries can issue duplicate offers or double-submit a response.
- Saving browser state without selection/time guards displays another organization's data after late responses.

## Subtle hidden checks

1. `ws-101`: two confirmed, capacity three; with no holds, `c-3` (same joinedAt as `c-4`) must be first. At the same instant, exactly one offer is issued.
2. `ws-102`: one available seat, `c-7` beats `c-8`; two sequential `advance` calls must not oversell. A retry of the first command returns the original receipt even when its expected revision is now stale.
3. `ws-202`: full with one waiting, advance issues zero offers; revision stays unchanged and replay is stable.
4. `ws-103`: closed session cannot advance, even if it has capacity.
5. A pending offer at `expiresAt-1ms` is live; at exactly `expiresAt` it has expired. Read-only availability does not bump revision.
6. An expired offer stops holding capacity but its recipient cannot be offered again. The next eligible person advances; no starvation through endless repeat offers.
7. Two ISO timestamp strings with different offsets but identical instants must compare equally, including idempotency intent. Reject impossible dates and time zones.
8. `expectedRevision=true`, floating point, numeric string and negative number are rejected. `requestKey` too short or with whitespace is rejected, not silently trimmed.
9. Same org/key with a different action, different offer ID, changed choice, changed asOf instant or another session conflicts, without changes to state.
10. Same key in a different organization is independent; cross-organization session/offer attempts return 404 without leaking data.
11. A note edit between reading and advancing forces stale rejection; successful advance likewise makes an older note edit stale.
12. A response attempted after expiry, before creation or after prior accept/decline cannot change participant or revision. Two fast responses for the same offer cannot both succeed.
13. Backwards `asOf` is rejected after a prior successful mutation; test a same-instant valid action.
14. After a failed network delivery, the client must retain original payload and key and safely replay; switching sessions while pending must not flash an old receipt in the new detail panel.

## Alternative defensible designs

A session-local map plus sorted waitlist is completely reasonable for the 60-minute exercise. A heap of waiting registrants is also defensible if it prevents stale/pop duplicates and preserves tie order. A deterministic `offerId` derived from a persisted counter is fine within this single process. Using transactional SQLite or a lock is extra credit only when it does not sabotage the vertical slice. LLM-based classification provides no meaningful benefit for the deterministic seat allocation; the candidate should be able to explain that choice without being instructed to avoid LLMs.

## What to discover from fixtures

Three isolated organizations. `ws-101` is under capacity but has equal-priority waiters. `ws-102` has one free seat. `ws-202` is full. `ws-103` is closed. `ws-301` has a cancelled person mixed with waiting participants. Session revisions vary and make stale note actions observable. Existing offers begin empty so the candidate must create and inspect them via the new workflow rather than relying on data that makes it already work.

## Likely AI-agent failure modes

One-shot prompt may generate routes without any UI wiring; ignore holding seats across new requests; implement capacity arithmetic on the client; leak a mutable database array; forget `requestKey` replay storage; use time strings as sort keys; use `Date.parse` without strict RFC3339 validation; introduce async functions between check and commit; or rewrite the working note directory while adding offers. Check whether the candidate reviewed AI changes and wrote meaningful tests rather than trusting the generated code.

## Suggested prioritization (60 minutes)

0–8 min: Inspect fixture, working HTTP, UI and existing tests. State invariants, choose API shapes.
8–28 min: Implement strict validation, availability and deterministic advance with safe revisions.
28–40 min: Implement respond, expiry and idempotency replays, write focused domain tests.
40–53 min: Connect browser controls and authoritative refresh; cover stale/transport UX.
53–60 min: Run baseline and new tests, demonstrate, explain complexity and remaining gaps.

## Walkthrough inspection points

Ask to see live seat count after issuing an offer, then after its expiry; why a duplicate key returns the same immutable snapshot; how a duplicate after a note edit is handled; whether two racing POSTs can oversell; what happens at a tie in `joinedAt`; why a declined participant is not reconsidered; and how a slow response is ignored after changing organization. Inspect the full state transitions, not just the endpoint response.
