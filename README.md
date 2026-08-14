# Dispatch Desk — One-Hour Full-Stack Interview Exercise

## Context

Dispatch Desk is a small internal operations tool used by a local delivery company. Dispatchers use it to see queued delivery jobs and assign drivers manually.

The starter app is intentionally modest but realistic: there is an Express/TypeScript API, a React/TypeScript frontend, shared behavior across several files, in-memory persistence, and existing backend tests.

## Existing behavior

- The dashboard loads all delivery jobs from the backend.
- Jobs have a status of `queued` or `assigned`.
- A dispatcher can manually assign a queued job to a driver by entering a driver name.
- The backend rejects an empty driver name and rejects attempts to reassign an already-assigned job.
- Jobs are kept in memory; restarting the server resets the sample data.

## Feature request

**Add a “Claim next job” workflow that safely assigns the highest-priority available queued job to the current dispatcher, including retry-safe request handling and UI conflict recovery.**

### Acceptance criteria

1. Add a backend endpoint that claims exactly one queued job for a dispatcher.
2. The claimed job must be selected by:
   - highest numeric `priority` first;
   - when priorities tie, earliest `createdAt` first.
3. The request must include a non-empty dispatcher name.
4. The request must include an idempotency key supplied by the client.
5. Repeating the same claim request with the same idempotency key must return the same claimed job and must not claim another job.
6. Two different idempotency keys must never result in the same queued job being claimed twice.
7. If no queued jobs remain, return a clear non-2xx response that the frontend can distinguish from a generic server failure.
8. Add a “Claim next job” control to the React UI.
9. While the claim is in flight, prevent accidental duplicate submissions.
10. After success, the dashboard must reflect the claimed job without requiring a manual page refresh.
11. If the server reports that there is no job left to claim, refresh/reconcile the dashboard and show a useful message rather than leaving stale optimistic state.
12. Existing manual assignment behavior must continue to work.

## Constraints

- Keep the existing stack and in-memory data store.
- Do not add a database, Redis, message queue, auth provider, or external service.
- You may change API shapes if needed, but keep the implementation small enough for an interview.
- You may introduce a helper/service abstraction if it improves correctness or testability.
- Treat the backend as the source of truth.

## Out of scope

- Authentication or authorization.
- Persistence across server restarts.
- Multi-process or distributed locking.
- Styling polish beyond basic usability.
- Production-grade observability.

## Setup

```bash
npm install
npm run dev
```

Frontend: `http://localhost:5173`

Backend: `http://localhost:3001`

## Tests

```bash
npm test
```

Existing tests cover current behavior only. Add whatever tests you think are appropriate for the new feature.

## 60-minute interview instruction

You have **60 minutes**. Work as you would in a real AI-assisted coding interview: inspect the repository, form a plan, implement incrementally, run tests, verify behavior end to end, and leave the code in the strongest state you can.

The goal is not maximum code volume. The evaluator cares about correctness, judgment, verification, and how well you handle edge cases under time pressure.

**Do not read `INTERVIEWER_NOTES.md` until after you finish the exercise.**
