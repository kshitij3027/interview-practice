# POST-PRACTICE ONLY — Interviewer Notes

**Do not read this file before completing the 60-minute exercise.**

## Intended solution outline

A strong solution adds server-owned swap-request state beside the existing schedule state rather than treating the workflow as two client-driven reassignment calls. Creation normalizes the two shift IDs into an unordered logical pair, validates the proposed post-swap schedules, captures both shift revisions plus the global schedule revision, allocates a permanent request ID, records `created_at` / `expires_at`, and stores the create idempotency result.

The key domain operation should reason about a hypothetical schedule. For each employee, remove both participating shifts from the schedule they currently own, add the destination shift, then validate qualification, overlap, and the 8-hour rest window against remaining adjacent shifts. This prevents the common bug where current ownership of the two swap shifts is counted as a conflict with the proposed assignment.

Acceptance should enter one store/domain mutation boundary, check the request is still pending and not expired, validate captured revisions/global schedule revision before writes, and either reject with zero shift mutation or change both assignees as one logical operation. Each changed shift revision increments once; the global schedule revision increments once. The request transition should be recorded with the result. An acceptance idempotency map keyed by client request key prevents a retry from executing the swap a second time.

Rejection changes only request state. Expiration does not require a worker: derive effective expiry when reading/acting on a pending request, or transition it lazily under the same mutation boundary.

On the frontend, keep swap controls/request state separate from shift browsing state. After success, refresh/reconcile schedule and request data while preserving the site filter and valid selection. Conflict responses should refresh current shifts/revisions without discarding the visible request context.

## Subtle traps / hidden checks

- A/B and B/A are the same logical create payload for a reused create idempotency key.
- A second active request involving either shift must fail even if the pair differs.
- Both destination qualifications must be checked.
- Resulting-schedule overlap checks must exclude both participating old assignments before adding each destination.
- Rest is based on the destination shift and the employee's remaining adjacent shifts; exactly 8 hours is valid.
- Time comparisons use ISO timestamps/UTC instants, not browser-local strings.
- A manual reassignment of either involved shift after request creation makes acceptance stale.
- Under the stated contract, any global schedule revision change since creation also makes acceptance stale, even if the edited shift seems unrelated. This is intentionally conservative and simple to reason about during the interview.
- Stale acceptance must not update one shift before discovering the conflict on the other.
- Successful acceptance increments each shift revision once and the global schedule revision once, not twice.
- Retrying the same successful acceptance key must return the prior result; blindly executing "swap" again would reverse the assignments.
- Reusing an acceptance key for a different swap request must fail.
- Expired pending requests cannot be accepted even when their captured revisions still match.
- Reject must not change schedule revision.
- Existing single reassignment must still reject overlap/stale writes after feature work.

## Likely failure modes

- Implementing accept as two calls to the existing public reassignment method, causing partial success or two schedule-revision increments.
- Validating each employee against the current schedule rather than the hypothetical post-swap schedule.
- Checking only qualification and overlap, omitting the 8-hour rest rule.
- Treating the create pair as ordered for idempotency.
- Storing only shift IDs client-side and trusting the browser to send authoritative assignees on accept.
- Checking staleness after the first mutation.
- Using a toggle-like swap operation on retry, which swaps back.
- Treating expiration as purely cosmetic UI state.
- Refreshing the whole app on conflict and losing the current filter/selection.
- Breaking existing reassignment because new request-state code is mixed directly into unrelated paths.

## Expected prioritization

1. Model request state and a pure resulting-schedule validator; add focused tests for qualification/overlap/rest.
2. Implement create + server-owned captured revisions/idempotency.
3. Implement atomic accept with stale checks and exact revision accounting.
4. Add reject/expiry semantics.
5. Build the minimum usable frontend workflow.
6. Add stale/retry UI recovery and targeted verification if time remains.

Correct backend semantics with a rough usable UI is stronger than polished request cards backed by two unsafe reassignment calls.

## What the interviewer should inspect after the hour

- Is there a clear atomic mutation boundary for acceptance?
- Can either half of the shift exchange become visible alone?
- Does validation model the *resulting* schedule correctly?
- Are 8-hour boundary conditions explicit and testable?
- Are create and accept idempotency semantics materially correct?
- Are stale revision checks performed before all schedule writes?
- Is revision accounting exactly once per logical mutation?
- Does the frontend preserve useful state on conflicts/errors?
- Did the candidate keep the existing manual reassignment invariant intact?
- Can the candidate explain which requirements they prioritized and what they would harden next?
