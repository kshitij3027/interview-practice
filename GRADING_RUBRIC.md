# Grading Rubric — 100 points

The happy path alone is capped around **60–65** even if the UI looks polished.

## 1. Functional correctness — 20
- 18–20: preview and commit both work end-to-end on realistic mixed-validity CSV data; committed state matches previewed semantics.
- 12–17: core flow works but one meaningful correctness area is incomplete.
- 6–11: only a narrow happy path works.
- 0–5: feature is largely non-functional.

## 2. Backend/domain behavior — 18
Assess parsing boundary, account matching, money handling, allocation order, mutation boundaries, and revision semantics.
- Excellent: domain behavior is explicit, deterministic, and isolated enough to reason about.
- Acceptable: mostly correct with minor leakage/duplication.
- Partial: endpoint-heavy implementation with fragile mixed concerns.
- Failing: incorrect monetary or allocation semantics.

## 3. Edge cases and safety — 22
High-weight hidden-evaluator checks include:
- mixed valid + malformed + unknown-customer rows;
- duplicate payment IDs inside a file;
- multiple payments for one account in the same import;
- payment spanning multiple invoices and leaving account credit;
- tie-breaking between invoices;
- stale preview caused by an intervening manual credit;
- retrying a successful commit;
- ensuring rejected stale commits apply nothing.

18–22 requires strong handling of most of these. A pure happy path should receive fewer than 10 here.

## 4. Frontend behavior — 12
Evaluate import input, readable preview outcomes, commit state, disabled/in-flight behavior, stale-state recovery, and post-commit refresh.

## 5. Integration/API contract — 10
Evaluate whether client and server agree on stable, understandable data shapes and whether server-owned preview state prevents client-side plan tampering.

## 6. Tests — 10
- 9–10: targeted tests cover deterministic allocation plus at least two important failure/retry cases.
- 6–8: meaningful backend tests beyond the happy path.
- 3–5: limited tests or mostly superficial assertions.
- 0–2: no useful feature tests.

## 7. Code quality — 5
Clarity, naming, reasonable decomposition, minimal accidental complexity, and consistency with the starter architecture.

## 8. Verification/debugging discipline — 3
Evidence that the candidate ran existing tests/build, exercised the feature, and checked failure states rather than relying only on generated code.

## Overall calibration
- **90–100 Excellent:** interview-ready, robust under hidden cases, strong prioritization.
- **75–89 Strong/acceptable:** core feature correct with a few gaps.
- **60–74 Partial:** substantial progress, but meaningful correctness/safety holes remain.
- **Below 60 Failing:** happy-path-only, brittle, or incomplete implementation.
