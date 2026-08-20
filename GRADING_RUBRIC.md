# Grading Rubric — 100 points

A visually complete happy path with incorrect interval, stale-state, or retry semantics should not score above roughly **60–65**.

## Functional correctness — 20 points
- 18–20: preview and apply work end to end for temporary and open-ended scheduling; resulting timelines are correct.
- 13–17: core workflow works with one meaningful gap.
- 7–12: narrow happy path only.
- 0–6: feature is largely non-functional.

## Backend/domain behavior — 22 points
Evaluate date validation, active-plan validation, interval overlay semantics, preservation of unaffected timeline regions, restoration at `end_on`, coalescing, server-owned preview state, revision checks, and atomic apply.

Excellent work keeps timeline transformation deterministic and independently testable. Acceptable work is mostly correct with minor coupling. Partial work mixes route/mutation logic and misses difficult boundary cases. Failing work can create overlaps, gaps, or incorrect plan restoration.

## Frontend behavior — 12 points
Evaluate usable scheduling controls, readable preview rendering, disabled/in-flight behavior, apply state, preservation of operator inputs after conflict, and post-apply account/timeline reconciliation.

## Integration/API contract — 10 points
Evaluate whether client/server contracts clearly distinguish preview from apply and whether apply references server-owned preview state rather than trusting a client-authored replacement timeline.

## Edge cases & safety — 22 points
High-value evaluator checks include:
- `start_on` equal to business date;
- missing/invalid dates and `end_on <= start_on`;
- inactive/unknown plan;
- temporary interval entirely inside one segment;
- interval spanning multiple pre-existing future boundaries;
- `end_on` exactly equal to an existing boundary;
- target plan matching the plan before or after the inserted interval;
- coalescing adjacent equal-plan segments without zero-length rows;
- open-ended scheduling from a date inside a finite segment;
- preview producing no live mutation;
- immediate plan change after preview causing stale apply;
- stale apply producing zero timeline mutation;
- retrying an already-successful apply without another revision increment.

18–22 requires strong handling of most of these. A happy-path-only implementation should earn fewer than 10 points here.

## Tests — 8 points
- 7–8: focused domain tests cover interval transformation plus at least two stale/retry/boundary cases.
- 5–6: meaningful tests beyond the happy path.
- 2–4: limited or superficial coverage.
- 0–1: no useful feature tests.

## Code quality — 3 points
Clear naming, reasonable decomposition, consistency with the starter architecture, and no unnecessary framework/infrastructure rewrite.

## Verification/debugging — 3 points
Evidence the candidate ran existing tests/build, exercised an end-to-end browser path, and checked at least one conflict or boundary case.

## Overall calibration
- **90–100 Excellent:** robust semantics, focused verification, strong prioritization.
- **75–89 Good/acceptable:** core implementation is sound with a few gaps.
- **60–74 Partial:** substantial progress but important correctness/safety holes remain.
- **Below 60 Failing/incomplete:** happy-path-only, brittle, or materially incorrect.
