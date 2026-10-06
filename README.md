# PulseReplay — HARD One-Hour Full-Stack Interview Exercise

## Context
PulseReplay is an internal webhook-operations console used by a platform team supporting customer integrations. The starter application is already functional: a Python 3.11 standard-library HTTP API, in-memory fixture-backed state, and a dependency-free browser ES-module frontend.

## Existing behavior
- Endpoints are ordered by tenant, name, then endpoint ID and can be filtered by tenant and enabled/paused state.
- Endpoint detail shows current configuration revision, global dataset revision, and recent deliveries.
- Operators can pause or resume an endpoint.
- Status changes require the endpoint revision observed by the browser. Stale writes do not mutate.
- A real status change increments endpoint revision and dataset revision exactly once; setting the current status is a no-op.
- The browser protects list/detail views from slower obsolete responses while the operator changes filters or endpoints.
- Restarting restores the checked-in fixtures.

`fixtures/deliveries.jsonl` contains representative webhook outcomes. The `simulation` field exists only so this interview app can deterministically emulate a downstream receiver without calling the network.

## Customer / business problem
A customer endpoint can fail for minutes and accumulate a backlog. Today operators manually inspect failed rows and ask engineering to replay them. That is risky: some events share an ordered stream, retries can be repeated by the browser or operator, an endpoint can be paused or changed while a replay request is in flight, and one bad event must not prevent unrelated streams from making progress.

## Primary feature request
**Add a server-authoritative failed-delivery replay workflow for the selected endpoint, with deterministic candidate selection, per-stream ordering, partial outcomes, safe retry behavior, stale-state protection, and correct browser reconciliation.**

## Replay semantics
A replay request supplies the selected endpoint ID, the endpoint revision observed by the browser, an optional exact `streamKey` filter, `maxEvents` from 1 through 100, a client-generated request key, and optional `delayMs` from 0 through 2000 for race testing.

Only deliveries whose current status is `failed` or `quarantined` are replay candidates. The endpoint must currently be enabled.

Candidate selection must be deterministic and independent of fixture row order. Within a stream, lower `sequence` must be attempted before higher `sequence`. Across streams, use lexicographically smaller `streamKey` first; then sequence; then `receivedAt` instant; then delivery ID. Apply `maxEvents` after ordering/filtering.

For this exercise, downstream behavior is deterministic:
- `simulation = success`: the replay attempt succeeds;
- `simulation = retry_once`: it returns a retryable failure until that delivery has at least one replay attempt recorded, then succeeds on a later replay request;
- `simulation = permanent_error`: it returns a permanent failure.

Within one replay request, a retryable or permanent failure blocks later selected deliveries from the **same stream** for that request. Other streams continue. A blocked delivery is not attempted and its replay-attempt count does not change.

A successful attempt changes status to `delivered` and clears `errorCode`. A retryable failure remains `failed` with `errorCode = replay_retryable`. A permanent failure becomes/remains `quarantined` with `errorCode = replay_permanent`. Every attempted delivery increments its `replayAttempts` exactly once.

## Acceptance criteria
1. Add replay controls and a readable per-delivery result view for the selected endpoint without breaking existing filtering, detail, pause/resume, ordering, revision, and no-op behavior.
2. The backend owns candidate selection and all replay semantics. The client must not send a precomputed list of delivery IDs as the authoritative plan.
3. Reject replay when the endpoint is paused, the submitted endpoint revision is stale, `maxEvents` is outside `1..100`, `streamKey` is blank after normalization when supplied, or `delayMs` is outside `0..2000`. Invalid/stale requests cause zero replay attempts and zero delivery mutations.
4. `streamKey` matching is exact after trimming the submitted filter. Do not case-fold stored stream keys.
5. Candidate ordering and `maxEvents` behavior must follow the deterministic rules above and must not depend on JSONL row order.
6. Process selected candidates so one stream's failure blocks only later selected deliveries from that same stream; unrelated streams continue.
7. Return a structured result for every selected candidate with an observable outcome such as succeeded, retryable failure, permanent failure, or blocked-by-earlier-stream-failure.
8. Attempted deliveries update status/error/attempt count exactly as specified. Blocked deliveries do not mutate.
9. One replay request increments the endpoint revision and global dataset revision **exactly once** if at least one delivery mutates. A request with zero eligible candidates is an explicit no-op with no revision change.
10. A client request key identifies the normalized logical request: endpoint ID, observed endpoint revision, normalized stream filter, and `maxEvents`. `delayMs` is excluded from identity.
11. Same key + same logical request must return the original replay result without making additional attempts or revision changes. Reusing the key with a different logical request must fail clearly.
12. Staleness is checked immediately before applying replay work. A delayed replay started with revision N must fail with zero replay mutation if the endpoint is paused/resumed in the meantime and its revision becomes N+1.
13. A fresh replay request after a retryable failure may try that delivery again. A same-key retry must **not** constitute a fresh attempt.
14. After replay success or partial failure, reconcile endpoint detail, delivery rows, endpoint revision, global dataset revision, and failed counts without requiring a full browser reload.
15. If the operator switches endpoint or filters while replay is in flight, the older response must not overwrite the newly selected context. The server operation may still complete.
16. A transient replay HTTP failure should preserve last-known-good endpoint/delivery data and replay controls when possible.
17. Prevent accidental duplicate submission of the same in-flight replay while leaving normal endpoint browsing usable.
18. Existing starter tests must remain green; add focused tests for the feature's highest-risk semantics.

## Constraints
Keep the Python 3.11 + browser ES-module stack, one-process in-memory state, and checked-in fixtures. Do not add a database, message broker, websocket, external API, or real webhook call. Production endpoints may have hundreds of thousands of historical deliveries and thousands of failed events, so avoid obviously wasteful repeated global work when a request is scoped to one endpoint/stream.

## Out of scope
Authentication/authorization, persistence across restart, distributed workers, exponential backoff scheduling, editing payload bodies, signing secrets, actual network delivery, and visual polish.

## Setup / run / verify
```bash
./scripts/test.sh
./scripts/build.sh
./scripts/verify.sh
./scripts/run.sh
```

Open `http://localhost:8080`.

## 60-minute AI-assisted interview instruction
You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or similar tools. Inspect the store, mutation/revision boundary, browser request guards, fixtures, and existing tests before coding. Implement incrementally and verify ordering, stream blocking, retry-on-next-request behavior, same-key idempotency, stale delayed requests, no-op accounting, and browser race handling.

A polished happy path that can double-attempt on retry, reorders a stream, mutates after a stale revision, blocks unrelated streams, or lets an old response repaint newer context is not a complete solution.
