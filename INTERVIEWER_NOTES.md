# Interviewer Notes — POST-PRACTICE ONLY

Do not read before completing the practice exercise.

## Intended structure
Strong solutions separate: config validation/canonicalization, deterministic subject evaluation, ephemeral server-owned preview state, and atomic publish/idempotency handling. The browser submits editor text for preview and later publishes only by preview ID plus request key.

Use deterministic semantic rule ordering: priority descending, then rule ID ascending. For rollout bucketing, use a stable digest such as SHA-256 over an unambiguous encoding of flag key, seed, and subject key, then map to [0,9999]. Runtime-randomized hashing is incorrect.

Preview state should retain preview ID, flag ID, captured flag revision, canonical config, explanation, and consumed state. Publish re-checks current flag revision before any mutation, handles canonical no-op, mutates once when different, and records the original idempotent result.

## Hidden checks
- Reverse equal-priority rules: lexical smaller ID must still win.
- Reorder JSON object keys: preview/publish must remain identical.
- Typed equality must distinguish number, string, and boolean.
- exists checks key presence, not truthiness.
- Empty/malformed in values and invalid rollout totals must fail validation.
- ends_with on non-strings must not coerce.
- Rollout assignments must survive process restart.
- Delayed Preview A must never overwrite newer Preview B.
- Preview, then edit operator note, then publish: stale with zero rollout mutation.
- Same request key + same preview: original outcome with no extra revisions.
- Same key + different preview: clear mismatch.
- Consumed preview + new key: do not replay.
- Canonically identical publish: successful no-op with unchanged revisions.
- Duplicate subject keys: clear server error.

## Likely AI-agent failures
Browser-owned targeting; unstable hashing; priority-only sorting; string-coercing comparisons; truthiness-based exists; resubmitting config on publish; stale checks after mutation; idempotency recorded too late; no preview consumption; old fetches repainting new UI; replacing the starter rather than integrating with the note flow.

## Recommended prioritization
1. Inspect existing revision/mutation boundaries and fixtures.
2. Implement validation/evaluation/stable bucketing + preview tests.
3. Implement server preview storage and publish stale/no-op/idempotency semantics.
4. Add minimal frontend editor/preview/publish.
5. Add preview response sequencing and stale recovery.
6. Spend remaining time on adversarial tests and explanation.

## Walkthrough
Ask the candidate to explain stable bucketing, equal-priority ties, typed comparisons, delayed preview ordering, note-induced stale publish, retry behavior, preview consumption, canonical no-op, and preservation of existing note tests.

Alternative module layouts are fine if observable behavior and invariants are correct.
