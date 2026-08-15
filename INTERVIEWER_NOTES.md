# POST-PRACTICE ONLY — Interviewer Notes

## Intended solution outline
A strong solution parses cohort definitions server-side, computes a stable bucket per account from immutable inputs, separates eligibility from percentage selection, treats explicit overrides as protected, and stores an opaque server-owned calculation/rollout token with the inputs, selected IDs, and base flag revision. Apply validates the token and current revision before any mutation, writes all selected overrides as one logical rollout, increments flag revision once, and records completion so retries return the prior result.

## Subtle traps / hidden checks
- Blank cohort plan/region are wildcards, not empty-string matches.
- `min_employees` is inclusive.
- Stable bucketing should not depend on input array order or runtime randomness.
- Monotonicity must hold when percentage increases.
- Explicit `false` overrides are still explicit and protected.
- Excluded accounts should not be reclassified as percentage misses.
- Duplicate exclusion IDs should not distort counts.
- Unknown exclusions are surfaced but do not abort.
- A manual override after calculation invalidates apply.
- Stale apply must make zero rollout mutations.
- Flag revision increments once for the rollout.
- Same successful rollout applied twice must not increment revision twice.
- Client should retain controls after stale conflict and reconcile revisions.

## Expected prioritization
1. Backend cohort parsing and deterministic selection helper.
2. Focused domain tests for monotonicity/precedence.
3. Server-owned calculation endpoint and apply endpoint with revision/idempotency.
4. Minimal UI.
5. Conflict recovery and polish.

## Likely failure modes
Using `Math.random`, hash threshold that is not monotonic/stable, trusting selected IDs from browser, incrementing revision per account, treating explicit false override as no override, partial mutation before stale detection, clearing UI inputs on conflict, or breaking existing single override behavior.

## What to inspect after the hour
Look for deterministic pure domain logic, explicit mutation boundary, idempotent apply semantics, preservation of current manual override invariants, targeted tests, and evidence the candidate actually exercised stale/retry behavior.
