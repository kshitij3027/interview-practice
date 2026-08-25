# Grading Rubric — 100 points

A polished happy path that ignores ordering, cursor races, atomic validation, or retries should not score above roughly **60–65**.

## 1. Functional correctness — 20 points

- **18–20 Excellent:** the sync flow works end to end across multiple batches; state and UI outcomes match the stated semantics.
- **13–17 Acceptable:** core sync works with one meaningful correctness gap.
- **7–12 Partial:** useful happy path, but major cases are missing or fragile.
- **0–6 Failing:** feature is largely non-functional or corrupts state.

## 2. Backend / domain behavior — 20 points

Evaluate feed parsing boundaries, normalized case lookup, per-case deterministic ordering, source-version handling, atomic event validation, revision increments, and preservation of internal notes.

- **17–20 Excellent:** deterministic, explicit, testable domain logic with correct mutation boundaries.
- **12–16 Acceptable:** mostly correct but with minor coupling or one semantic omission.
- **6–11 Partial:** route-heavy implementation or several semantic errors.
- **0–5 Failing:** incorrect merge/version behavior or unsafe partial mutation.

## 3. Frontend behavior — 12 points

Evaluate batch-size controls, in-flight state, summaries, retention of filters/selection, updated case reconciliation, no-work handling, and stale/transient error recovery.

## 4. Integration / API contract — 10 points

Evaluate whether client and server agree on cursor, request key, row outcomes, updated cases, and failure shapes; the backend must remain authoritative for cursor and merge semantics.

## 5. Edge cases & safety — 22 points

High-value hidden-evaluator themes include:

- malformed JSON among valid rows;
- unknown case references;
- trim + case-insensitive case matching;
- duplicate event IDs within a batch and across batches;
- same-case events arriving out of source-version order;
- same-version deterministic tie handling;
- stale source versions after a newer event in the same batch;
- an event containing one valid and one invalid changed field applying **nothing**;
- explicit `owner_email: null` clearing ownership;
- cursor advancement counting malformed/duplicate rows;
- stale expected cursor causing zero processing/mutation;
- successful request-key retry returning the prior result without advancing again;
- request-key reuse with different parameters;
- preserving internal notes and existing note concurrency behavior.

**18–22 Excellent:** most hidden themes are handled correctly. A happy-path implementation should receive fewer than 10 points here.

## 6. Tests — 8 points

- **7–8 Excellent:** focused tests cover deterministic ordering plus at least two of duplicate/cursor/idempotency/atomic-validation risks.
- **5–6 Acceptable:** meaningful feature tests beyond the happy path.
- **2–4 Partial:** limited or superficial tests.
- **0–1 Failing:** no useful feature tests.

## 7. Code quality — 4 points

Clear naming, reasonable decomposition, limited accidental complexity, and consistency with the starter architecture.

## 8. Verification / debugging — 4 points

Evidence that the candidate ran baseline and feature tests/build, exercised the UI, and checked at least one failure/retry state rather than relying only on generated code.

## Overall calibration

- **90–100 Excellent:** robust under hidden cases; strong prioritization and verification.
- **75–89 Strong / acceptable:** core feature correct with a few gaps.
- **60–74 Partial:** substantial implementation, but meaningful correctness/safety holes remain.
- **Below 60 Failing / incomplete:** narrow happy path, brittle semantics, or broken integration.
