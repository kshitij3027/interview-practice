# Grading Rubric — 100 points

## Functional correctness — 20
End-to-end calculation and apply workflow, including UI integration.

## Backend/domain behavior — 22
Cohort parsing/matching, stable percentage bucketing, override precedence, authoritative server calculation, revision semantics, and retry-safe apply.

## Frontend behavior — 12
Usable controls/results, preserved inputs on conflict, loading/error states, and post-apply reconciliation.

## Integration — 10
Clear API contracts and correct use of server-owned rollout state rather than client-authored selected IDs.

## Edge cases & safety — 22
High-value checks: blank cohort fields, boundary employee counts, 0%/100%, unknown exclusions, duplicate exclusion IDs, overlapping override/exclusion membership, deterministic results after account order shuffle, monotonic 30→40%, stale revision with no partial mutation, repeat apply, and manual override regression.

## Tests — 8
Focused tests for deterministic bucketing plus at least two high-risk conflict/idempotency/precedence cases.

## Code quality — 3
Reasonable decomposition and consistency with the starter.

## Verification/debugging — 3
Evidence of baseline checks and end-to-end failure-path verification.

## Calibration
- 90–100: excellent, robust under hidden checks.
- 75–89: strong/acceptable with a few gaps.
- 60–74: partial; important correctness holes remain.
- Below 60: incomplete/brittle.

A happy-path implementation that merely filters a cohort and writes selected IDs should not exceed **60–65**, even with polished UI.
