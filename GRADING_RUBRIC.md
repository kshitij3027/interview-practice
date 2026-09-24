# Grading Rubric — POST-PRACTICE ONLY

Total: 100 points.

## Functional end-to-end workflow — 18
- 6: Selected-flag UI supports editable rollout JSON, preview, understandable preview output, and publish without breaking browsing.
- 6: Preview/publish routes are integrated with the frontend rather than isolated helpers.
- 6: Successful publish reconciles flag/config/revisions and no-op/stale outcomes are distinguishable.

## Backend validation and canonical semantics — 18
- 8: Validates the complete candidate contract: shape, variations, unique IDs, priorities, conditions/operators/values, serve-vs-rollout exclusivity, seed, and exact 10,000 weight total.
- 6: Produces deterministic canonical configuration independent of JSON object-key order and incidental rule order.
- 4: Validation errors are structured and never mutate permanent state.

## Deterministic targeting behavior — 18
- 6: Correct rule precedence: priority descending, rule ID ascending, first match wins, fallback otherwise.
- 5: Exact condition semantics, including missing attributes, typed equality, in, exists, and string-only ends_with.
- 5: Percentage rollout uses a stable cross-process bucket derived from flag key + seed + subject key; no runtime-randomized hash or browser authority.
- 2: Counts, rule hits, and subject samples are deterministic and explainable.

## Preview/publish state boundary — 16
- 6: Preview is server-owned, non-mutating, captures flag revision, and publish references an opaque preview rather than trusting resubmitted config.
- 4: Stale flag revision is re-checked before any publish mutation.
- 3: Differing publish mutates atomically and increments flag + dataset revisions exactly once.
- 3: Canonically identical publish is a true no-op.

## Retry/lifecycle/failure correctness — 12
- 5: Same request key + same preview returns original result; key reuse for another preview fails.
- 3: A preview is logically consumable at most once and cannot be replayed later with a fresh key.
- 2: Delayed publish can surface note-induced stale conflict with zero rollout mutation.
- 2: Transient failures preserve last-known-good state.

## Frontend stale/out-of-order behavior — 8
- 4: Slower older preview responses cannot repaint newer editor/preview state.
- 2: Duplicate preview/publish submission is guarded while the same action is in flight.
- 2: Stale publish preserves editor/preview and refreshes current flag state.

## Tests and verification — 6
- 3: Focused tests cover validation/precedence/bucketing and publish stale/idempotency/no-op behavior.
- 2: Includes adversarial/boundary cases, not just happy path.
- 1: Existing starter tests/build remain green.

## Code quality and explanation — 4
- 2: Reasonable separation between validation/evaluation/state mutation/API/frontend concerns.
- 2: Candidate can defend invariants, hashing choice, retry/stale behavior, and tradeoffs.

## Score caps
- Happy-path-only editor + publish with weak validation or browser-owned targeting: max ~60–65.
- Uses unstable hashing, array order as precedence, or trusts client config again at publish: max 55.
- Can overwrite newer revision, double-publish on retry, or partially mutate on stale publish: max 50.
- Backend-only with no meaningful frontend integration: max 70.
