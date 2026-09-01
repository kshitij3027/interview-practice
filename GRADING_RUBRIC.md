# Grading Rubric — 100 points

## Functional correctness — 20 points
- **18–20 Excellent:** Preview and apply work end-to-end on realistic duplicate pairs; successful merges leave one coherent survivor and preserve all required existing behavior.
- **13–17 Acceptable:** Core workflow works but one meaningful requirement is incomplete or fragile.
- **7–12 Partial:** Happy path works but important merge semantics or apply safety are missing.
- **0–6 Failing:** Workflow is largely non-functional or corrupts state.

## Backend/domain behavior — 22 points
Evaluate deterministic contact-field selection, survivor-owned status/segment semantics, tag normalization, external-ID namespace handling, activity deduplication/conflict detection, source retirement, revision accounting, and server-owned preview state.

- **19–22 Excellent:** Domain rules are explicit, deterministic, testable, and separated from transport concerns.
- **14–18 Acceptable:** Mostly correct with small semantic gaps.
- **7–13 Partial:** Logic is endpoint-heavy, order-dependent, or misses several rules.
- **0–6 Failing:** Unsafe/non-deterministic merge behavior.

## Frontend behavior — 12 points
Evaluate survivor/source selection, readable preview categorization, disabled/in-flight controls, apply feedback, filter/selection preservation, stale recovery, and preservation of last known-good state on transient failures.

## Integration/API contract — 10 points
Evaluate whether client/server contracts are coherent, preview authority stays on the server, stale responses are handled correctly, and existing list/detail/status flows still work.

## Edge cases & safety — 22 points
High-value evaluator themes include:
- source and survivor accidentally identical;
- empty vs non-empty contact fields;
- verified older field vs unverified newer field;
- equal verification with timestamp tie;
- case-insensitive duplicate tags and deterministic output order;
- identical external IDs vs conflicting IDs in one namespace;
- exact duplicate activity events vs same-ID/different-payload conflicts;
- activity ordering when timestamps tie;
- preview followed by a status change on either profile;
- stale apply producing zero partial mutations;
- successful apply retried with the same request key;
- request-key reuse against another preview;
- survivor/source/global revision increments exactly once;
- existing status update still works on an unrelated profile.

A pure happy path should receive fewer than half of these points.

## Tests — 8 points
- **7–8:** Focused tests cover deterministic merge semantics plus at least two high-risk conflict/stale/retry cases.
- **5–6:** Meaningful feature tests beyond the happy path.
- **2–4:** Limited or superficial coverage.
- **0–1:** No useful feature tests.

## Code quality — 3 points
Reasonable decomposition, naming, consistency with the starter architecture, and minimal accidental complexity.

## Verification/debugging — 3 points
Evidence that the candidate ran the existing baseline, exercised the end-to-end workflow, and checked at least one failure/retry path.

## Overall calibration
- **90–100 Excellent:** Robust under hidden cases, strong prioritization, safe integration.
- **75–89 Strong/acceptable:** Core workflow is correct with a few edge-case or polish gaps.
- **60–74 Partial:** Useful implementation but meaningful correctness/safety holes remain.
- **Below 60 Failing/incomplete:** Happy-path-only, unsafe, brittle, or substantially unfinished.

A solution that merely concatenates two profiles and hides the source, without robust conflict, stale-state, and idempotency semantics, should **not exceed roughly 60–65 points** even if the UI looks complete.
