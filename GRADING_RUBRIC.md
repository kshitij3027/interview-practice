# Grading Rubric — 100 points

## Functional correctness — 22 points
- 20–22: End-to-end funnel works for all segments, both variants, and exclusion changes; report is usable and internally consistent.
- 15–19: Core report works with minor defects.
- 9–14: Happy path exists but meaningful semantics or integration are incomplete.
- 0–8: Feature is largely non-functional.

## Backend/domain semantics — 23 points
Evaluates eligibility, assignment-time gating, event-ID dedupe, chronological ordered progression, repeated-step handling, 24-hour window, deterministic results, percentages, and revision propagation.

## Frontend behavior — 14 points
Evaluates report controls/rendering, segment integration, loading/error feedback, preservation of last known-good data, and refresh after exclusion/include actions.

## Integration & stale-response correctness — 14 points
Evaluates revision awareness, protection against slower older requests, segment-switch races, and coherent reconciliation after mutations.

## Edge cases — 15 points
High-value hidden-evaluator themes include duplicate IDs, out-of-order fixture rows, events before assignment, unassigned users, repeated funnel steps, zero denominators, completions just inside/outside 24 hours, exclusion while a delayed request is pending, and stale segment responses.

## Tests — 6 points
Focused tests should demonstrate the candidate identified the highest-risk semantics rather than only snapshotting the happy path.

## Code quality — 3 points
Changes fit existing boundaries, avoid unnecessary rewrites, and keep domain logic understandable.

## Verification/debugging — 3 points
Candidate runs relevant tests/build and demonstrates or explains an end-to-end check, including at least one race/stale-state scenario.

## Calibration
- **90–100 (Excellent):** Strong correctness across semantics and races; focused verification; minimal regressions.
- **75–89 (Good/acceptable):** Core feature is solid with a few edge-case or polish gaps.
- **60–74 (Partial):** Useful implementation but at least one major correctness dimension remains weak.
- **≤59 (Failing/incomplete):** Happy-path-only work, major semantic errors, or broken integration.

A solution that merely displays a funnel from straightforward event counts, without correct dedupe/order/window/revision/race handling, should **not exceed 60–65 points** even if the UI looks complete.
