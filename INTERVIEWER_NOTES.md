# POST-PRACTICE ONLY — Interviewer Notes

**Do not read this file before attempting the exercise.**

## Intended solution outline

A strong solution usually introduces a small claim operation in the backend that performs three responsibilities in one synchronous critical section of this in-memory app:

1. validate dispatcher + idempotency key;
2. return a prior result if that idempotency key already succeeded;
3. otherwise deterministically choose the best queued job, mark it assigned, store the key-to-result mapping, and return it.

Because Node executes the mutation synchronously in one process here, a database lock is unnecessary and out of scope. The main conceptual point is to avoid splitting “find best job” and “assign job” into client-driven steps.

On the frontend, a strong implementation typically generates one key per user intent, disables the button while the request is active, updates local state from the server response, and reconciles with a fresh GET when the server says no work remains or the local view may be stale.

## Likely failure modes

- Generating a new idempotency key on every retry instead of every user intent.
- Returning the next job for a repeated idempotency key rather than the original result.
- Sorting priority ascending instead of descending.
- Forgetting deterministic `createdAt` tie-breaking.
- Performing GET-next then PATCH-assign as two separate client operations.
- Updating UI optimistically without rollback/reconciliation.
- Leaving the claim button enabled during the in-flight request.
- Mutating existing manual assignment semantics.
- Implementing only frontend or only backend.
- Adding a large dependency or infrastructure layer that consumes interview time.

## Hidden checks

1. Seed three queued jobs with priorities 2, 5, 5 and verify the earlier priority-5 job is claimed first.
2. Repeat the request with the same key and verify the same job is returned without consuming another job.
3. Use a new key and verify a different eligible job is claimed.
4. Exhaust queued jobs and verify the API returns a deliberate no-work response.
5. Submit whitespace-only dispatcher/key values.
6. Confirm manual assignment still rejects already-assigned jobs.
7. Simulate stale UI by loading, externally claiming the final job, then clicking claim in the original UI; look for reconciliation and a useful message.

## What to inspect after the hour

- Was the solution integrated end to end?
- Did the candidate understand idempotency semantics, or merely add a header/string?
- Is claim selection centralized on the server?
- Are state transitions deterministic and easy to reason about?
- Are tests focused on correctness rather than only superficial status checks?
- Did the candidate actually run the code/tests and inspect the final diff?
