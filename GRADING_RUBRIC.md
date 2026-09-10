# Grading Rubric — 100 points

## Functional correctness — 20 points
- 18–20: Preview and apply work end-to-end on realistic mixed suggestion data; UI state accurately reflects results and mutations.
- 13–17: Core workflow works with one meaningful gap.
- 7–12: Happy path exists but several required semantics are missing.
- 0–6: Feature is largely non-functional.

## Backend/domain behavior — 22 points
Evaluate suggestion deduplication/conflict handling, range validation, existing-redaction subtraction, category precedence, canonicalization, server-owned previews, revision checks, batch mutation boundaries, and idempotency.

## Frontend behavior — 12 points
Evaluate confidence controls, readable preview categorization, apply state, duplicate-submit prevention, stale recovery, preservation of last known-good state, and post-apply reconciliation.

## Integration/API contract — 10 points
Evaluate whether client/server contracts are coherent, the browser avoids authoring authoritative normalized ranges, revision/idempotency data is propagated correctly, and existing manual redaction remains compatible.

## Edge cases and safety — 22 points
High-weight checks include exact duplicate IDs, conflicting duplicate IDs, invalid pages/ranges, full and partial coverage by manual ranges, partial overlap that splits a suggestion, cross-category overlap, adjacency/coalescing, CSV row-order independence, zero-result previews, approved documents, stale apply with zero partial mutation, and successful apply retry.

## Tests — 8 points
- 7–8: Focused tests cover normalization plus at least two stale/idempotency/conflict cases.
- 4–6: Meaningful feature tests beyond the happy path.
- 1–3: Limited or superficial tests.
- 0: No useful feature tests.

## Code quality — 3 points
Clear decomposition, readable interval/business logic, consistency with existing boundaries, and no gratuitous framework rewrite.

## Verification/debugging — 3 points
Evidence the candidate ran baseline/build checks and exercised at least one overlap case plus one failure/retry/stale path.

## Calibration
- **90–100 — Excellent:** robust semantics and races, focused tests, minimal regressions.
- **75–89 — Strong/acceptable:** core feature is correct with a few edge-case or polish gaps.
- **60–74 — Partial:** useful implementation but at least one major correctness dimension is weak.
- **Below 60 — Failing/incomplete:** brittle, happy-path-only, or materially unsafe.

A solution that simply filters suggestions and writes their original ranges, without correct overlap normalization, stale protection, or retry safety, should not exceed roughly **60–65 points** even if the UI looks complete.
