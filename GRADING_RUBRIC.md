# Grading Rubric — 100 points

## Functional correctness — 18 points
- 16–18: End-to-end pacing report works for representative windows/cutoffs, renders useful results, and preserves the existing status workflow.
- 11–15: Core report works with minor gaps or UI limitations.
- 6–10: Happy path only; important semantics are missing.
- 0–5: Report is substantially incomplete or unusable.

## Backend / domain behavior — 20 points
Evaluate server authority, event canonicalization, correction-chain handling, refund arithmetic, occurrence/ingestion cutoffs, effective-dated budgets, timezone-local day construction, revision metadata, and validation boundaries.
- 17–20: Domain behavior is coherent, deterministic, and well-factored.
- 12–16: Mostly correct with one or two material semantic gaps.
- 6–11: Simplistic calculations that happen to work for basic fixture rows.
- 0–5: Browser-authored or fundamentally incorrect report logic.

## Frontend behavior — 12 points
Evaluate report controls, loading/error states, preserving last known-good data, campaign/input switching, stale-response suppression, and coexistence with pause/resume.
- 10–12: Robust and clear under slow/out-of-order requests.
- 7–9: Good ordinary flow with minor race/error issues.
- 3–6: Basic rendering but stale/error state is fragile.
- 0–2: Missing or misleading client behavior.

## Integration / API contract — 10 points
Evaluate request/response shape, server ownership of fixture data, validation/error status behavior, `delay_ms`, revision metadata, and clean coordination between route/service/store/UI layers.

## Edge cases and deterministic semantics — 20 points
High-value checks include:
- identical duplicate collapse versus conflicting duplicate winner;
- correction chains, orphan corrections, cycles, and cross-campaign references;
- refund subtraction;
- occurrence-time versus ingestion-time filtering;
- exact local-midnight budget boundaries;
- intra-day budget changes taking effect next local day;
- DST-short/long local days;
- `as_of` before/inside/after the report interval;
- zero-expected pacing semantics;
- row-order independence for both fixtures;
- invalid range / >92-day validation.

17–20 requires strong coverage of dangerous semantics. 10–16 means several are correct but important gaps remain. 0–9 indicates fixture-order assumptions or happy-path-only logic.

## Tests — 8 points
Reward focused tests around domain semantics and at least one stale/out-of-order frontend or endpoint behavior. Tests should assert outcomes, not mirror implementation details.

## Code quality — 5 points
Reward clear decomposition, readable naming, localized changes, integer-cents discipline, and consistency with the starter architecture.

## Verification / debugging — 7 points
Reward evidence that the candidate ran baseline checks, exercised the report end-to-end, deliberately tested at least one slow/stale-response path, and inspected edge-case outputs rather than relying only on generated code.

## Overall calibration
- **90–100:** Excellent. Correct, deterministic, robust under hidden checks, and well explained.
- **75–89:** Strong / acceptable. Solid end-to-end implementation with a few edge-case or polish gaps.
- **60–74:** Partial. Useful core path, but important correctness or race issues remain.
- **Below 60:** Incomplete, brittle, or not credible under stated constraints.

A polished happy-path report that linearly sums fixture rows, assumes 24-hour days, ignores replacement semantics, or allows stale responses to repaint newer inputs should **not score above roughly 60–65**.
