# Grading Rubric — 100 points

## 1. Functional correctness — 20 points

- Claim action works end to end.
- Exactly one eligible queued job is claimed per new request.
- Correct selection ordering is respected.

## 2. Backend behavior — 15 points

- Validates dispatcher name and idempotency key.
- Uses clear status codes / response contracts.
- No queued job can be claimed twice through separate requests.

## 3. Frontend behavior — 15 points

- User can trigger claim from the UI.
- In-flight state prevents accidental duplicate actions.
- Success and failure states are visible and understandable.

## 4. Integration — 10 points

- Frontend and backend contracts match.
- Dashboard state updates correctly after claiming.
- Existing manual assignment still works.

## 5. Edge cases — 15 points

- Same idempotency key is retry-safe.
- No jobs remaining is handled deliberately.
- Tie-breaking by `createdAt` is correct.
- Stale frontend state is reconciled after a conflict/no-job response.

## 6. Tests — 10 points

- Adds focused tests for important new backend behavior.
- Tests include at least one non-happy-path case.
- Existing tests remain green.

## 7. Code quality — 10 points

- Logic is readable and appropriately factored.
- Types are used well.
- No unnecessary infrastructure or large-scale rewrite.

## 8. Verification / debugging discipline — 5 points

- Candidate runs tests and/or build.
- Candidate performs at least one realistic end-to-end verification.
- Candidate checks the final diff for obvious mistakes.

## Performance bands

### Excellent: 85–100
Feature is correct across the stack, idempotency semantics are sound, ordering is deterministic, conflict/no-work behavior is deliberate, and verification is strong.

### Acceptable: 70–84
Core feature works with only minor correctness or UX gaps. Most important edge cases are handled and existing behavior remains stable.

### Partial: 45–69
A meaningful portion works, but one or more important requirements such as retry safety, deterministic selection, frontend reconciliation, or tests are incomplete.

### Failing: below 45
Feature is mostly non-functional, breaks existing behavior, or relies on unsafe assumptions that cause duplicate claims or inconsistent state.

## Hidden-evaluator-style checks

The evaluator may probe cases such as:

- retrying the exact same request after the client times out;
- two different idempotency keys arriving back-to-back;
- multiple queued jobs with identical priority;
- the frontend showing a queued job that another client has just claimed;
- whitespace-only dispatcher names or idempotency keys;
- manual assignment still functioning after the feature is added.

These are intentionally described at a high level; implementation details are up to the candidate.
