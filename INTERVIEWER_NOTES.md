# POST-PRACTICE ONLY — Interviewer Notes

Candidate: do not read before completing the exercise.

## Intended solution outline
A strong solution adds a replay service beneath the HTTP layer and gives the in-memory store two additional responsibilities: a request-key ledger for completed replay requests and an efficient way to obtain deliveries for one endpoint (optionally one stream). Exact module boundaries are flexible.

Normalize and validate the replay request before delay. Record the normalized identity as endpoint ID + expected endpoint revision + trimmed optional stream key + maxEvents; explicitly exclude delayMs. After any requested delay, enter the store mutation boundary, resolve the current endpoint, and perform the stale/enabled checks before touching deliveries.

Build the eligible candidate set from current failed/quarantined rows for the endpoint and optional exact stream. Sort deterministically by streamKey, sequence, receivedAt instant, then delivery ID; then cap to maxEvents. Track blocked stream keys while walking selected candidates. If a stream is blocked, emit a blocked result without mutation. Otherwise apply the simulation rule using the delivery's pre-attempt replayAttempts, increment an attempted row exactly once, and update status/error. A retryable or permanent failure adds only that stream to the blocked set.

If any delivery was attempted, increment endpoint revision and dataset revision once after the batch. If no candidate is selected, return an explicit no-op and do not increment anything. Store the exact result under the request key so the same-key/same-payload retry returns it byte-for-byte without another attempt; same-key/different-payload is a conflict.

On the browser, use an operation token/context tuple so an old replay response can finish server-side but cannot repaint a different endpoint or filter state. After an accepted replay result, refresh/reconcile list counts and selected detail while preserving controls and the result panel.

## Why naive approaches fail
- Replaying deliveries in JSONL order can violate stream sequencing and fixture-order independence.
- Globally stopping after one failure prevents unrelated streams from progressing.
- Looking only at HTTP retries without a server request-key ledger can double-attempt deliveries and advance retry_once incorrectly.
- Sleeping while holding a lock blocks unrelated requests; sleeping before the final stale check allows a concurrent pause/resume to invalidate the replay safely.
- Incrementing endpoint revision per delivery makes later rows in the same batch appear stale and breaks exact accounting.
- Treating quarantined as permanently ineligible contradicts the requested semantics; it is a candidate whose simulation may fail permanently again.
- Reusing client-supplied candidate IDs makes maxEvents/order semantics tamperable and stale.

## Complexity / scalability target
For a production-quality in-memory design, index deliveries by endpoint and optionally by endpoint+stream so a request does not scan every tenant's historical deliveries. With k eligible rows for the scoped endpoint/stream, straightforward sorting is O(k log k) time and O(k) temporary memory. If the candidate explains a maintained ordered index or bounded top-k structure, that is defensible but not required for the hour.

## Subtle traps
1. Apply maxEvents after deterministic ordering, not before.
2. streamKey request input is trimmed but compared case-sensitively.
3. retry_once checks replayAttempts before the current attempt increments it.
4. A blocked row does not increment replayAttempts and does not change error/status.
5. A permanent failure still counts as an attempted mutation even if the row was already quarantined, because replayAttempts increments and errorCode normalizes.
6. A retryable failure can be retried only by a fresh logical request/key; same-key replay returns the original result.
7. Same key + same normalized payload must be resolved before interpreting current eligibility, otherwise later state changes can alter the retry result.
8. Same key + different expected revision is a different payload and must conflict rather than becoming a fresh request.
9. Zero candidates is a no-op: no endpoint or dataset revision increment.
10. Stale/paused checks occur after delay and before any delivery attempt.
11. Endpoint revision changes once for the entire mutated replay request, not per stream or per delivery.
12. receivedAt should be compared as an instant for the final tie-break; equivalent offsets should not change ordering.

## Hidden checks
- Shuffle deliveries.jsonl; selected candidates and outcomes stay identical.
- maxEvents=2 with multiple streams; verify the cap happens after sort.
- Filter streamKey=" acct_17 "; trim succeeds, ACCT_17 does not match.
- First fresh replay of del_002 is retryable; del_003 is blocked; unrelated acct_91 rows still run.
- Second fresh request can succeed del_002 and then reach del_003.
- Same-key retry of the first request does not create a second attempt and returns the first result.
- Same key with changed maxEvents or revision returns an idempotency conflict.
- Permanent failure blocks only its stream and increments its attempt count once.
- Endpoint with no eligible rows returns no-op and keeps both revisions unchanged.
- Paused endpoint returns an error with zero mutation.
- Start delayed replay at revision N, pause/resume endpoint while sleeping, verify replay returns stale and no delivery changes.
- A successful replay with several attempted rows increments endpoint and dataset revisions once each.
- Switch UI selection before delayed replay responds; new endpoint remains rendered.
- Existing pause/resume stale and no-op tests remain green.

## Alternative defensible designs
- A dedicated ReplayService plus store methods, or cohesive store/domain methods, are both acceptable if mutation boundaries are clear.
- Pre-indexing deliveries by endpoint/stream is preferable at scale; filtering a scoped endpoint list is acceptable for the exercise if the candidate explains production tradeoffs.
- Returning a refreshed endpoint/detail snapshot directly from replay or doing follow-up GETs are both acceptable if the browser cannot paint stale context.

## Likely AI-agent failure modes
- Implements replay directly in the route and misses request-key normalization.
- Uses fixture row order or receivedAt alone instead of the specified precedence.
- Applies maxEvents before sorting.
- Blocks the whole batch after the first failure.
- Increments revision once per mutated delivery.
- Performs stale check before delay only.
- Treats a same-key retry as a new retry_once attempt.
- Clears the whole browser view on any replay error.
- Refreshes detail without guarding against endpoint switches.
- Rewrites existing pause/resume behavior and breaks its no-op/stale semantics.

## Recommended 60-minute prioritization
1. Preserve and rerun the starter baseline.
2. Implement request validation, normalized idempotency identity, stale/enabled preflight, deterministic candidate selection, and replay domain behavior with tests.
3. Wire one replay endpoint and structured results.
4. Add minimal controls/result UI and context guards.
5. Verify retry_once progression, same-key retry, a delayed stale conflict, and stream-local blocking.
6. Spend remaining time on index/scalability cleanup and UX polish.

## Walkthrough inspection points
Ask the candidate to show where the final stale check occurs, how request-key identity is normalized, why same-key retry cannot increment attempts, how blocked streams are represented, how revisions change for a mixed-result batch, and how the browser prevents an old replay response from replacing newer context.
