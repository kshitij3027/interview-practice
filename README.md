# FlagDesk — HARD One-Hour Full-Stack Interview Exercise

## Context
FlagDesk is an internal feature-flag console. Operators filter active/paused flags by owner, inspect a flag's published targeting config, and edit an operator note. The starter already works using a Python 3.11+ standard-library HTTP API, in-memory fixture state, and dependency-free browser ES modules.

## Existing behavior
- Flags are ordered by owner, then key; filtering/detail are server-backed.
- Note writes require the observed flag revision. Stale writes fail without mutation and return current state.
- A changed trimmed note increments that flag revision and global dataset revision exactly once; saving the same normalized note is a no-op.
- Restarting the server restores `fixtures/flags.json`.

`fixtures/subjects.json` contains a small synthetic population for rollout simulation.

## Customer/business problem
Product teams hand operators rollout configs such as “internal subjects are on; tier-A subjects in zone z1 get a 20/80 rollout; everyone else is off.” Today operators spot-check a few subjects and publish elsewhere. Misordered rules, unstable percentage bucketing, malformed conditions, or publishing after a concurrent flag change can target the wrong population.

## Primary feature request
**Add a server-authoritative rollout preview-and-publish workflow that validates candidate targeting JSON, deterministically evaluates subjects, explains assignments, and publishes the exact reviewed configuration with stale-state and retry protection.**

## Candidate configuration
```json
{
  "fallback": "off",
  "rules": [
    {
      "id": "internal",
      "priority": 100,
      "conditions": [{"attribute":"segment","op":"equals","value":"internal"}],
      "serve": "on"
    },
    {
      "id": "tier-a-z1",
      "priority": 50,
      "conditions": [
        {"attribute":"tier","op":"in","value":["a"]},
        {"attribute":"zone","op":"equals","value":"z1"}
      ],
      "rollout": [
        {"variation":"on","weight":2000},
        {"variation":"off","weight":8000}
      ],
      "seed": "launch-v3"
    }
  ]
}
```
Only `on` and `off` are valid variations.

## Acceptance criteria
1. Add a JSON rollout editor, Preview action/results, and Publish action to the selected-flag view without breaking the existing list/detail/note workflow.
2. Preview sends candidate JSON to the server. The browser must not decide validity, winning rules, rollout buckets, or canonical publishable config.
3. Validate top-level shape, fallback, unique rule IDs, integer priorities, non-empty conditions, supported operators/values, exactly one of `serve` or `rollout`, valid variations, rollout seeds/weights, and total rollout weight exactly `10000`.
4. Supported operators are `equals`, `in`, `exists`, and `ends_with`. Conditions inside a rule are ANDed. Missing attributes fail `equals`/`in`/`ends_with`; `exists` compares key presence to a boolean. `equals` is exact by JSON scalar type/value; `in` is a non-empty scalar array; `ends_with` is string-only.
5. Evaluate rules by higher priority first, then lexicographically smaller rule ID. First match wins; otherwise use fallback. Submitted rule array order must not affect results.
6. A `serve` rule chooses directly. A `rollout` rule uses cumulative weights and a stable server-side bucket in `[0,9999]` derived from flag key + rule seed + subject key. Results must be stable across restarts/machines; runtime-randomized hashing is not acceptable.
7. Subject identity is `key`. Duplicate subject keys are invalid fixture data and must fail clearly.
8. Preview must be deterministic regardless of JSON object-key order and return an opaque preview ID, captured flag revision, canonical validated config, per-variation counts, per-rule match counts, and deterministic subject samples sorted by key with winning-rule/fallback explanation.
9. Invalid preview returns structured diagnostics and no mutation. A failed preview must not replace the last known-good preview in the UI.
10. Preview supports bounded `delay_ms`; slower Preview A must never repaint newer Preview B/editor state.
11. Publish references the server-owned preview ID plus a client request key. Publish the canonical config stored in that preview, not a client-resubmitted config.
12. Before mutation, current flag revision must equal the previewed revision. If the existing note workflow changes the flag while publish is delayed, publish must fail stale with zero rollout mutation.
13. A different canonical config replaces the published config atomically and increments flag revision and dataset revision exactly once. Publishing a canonically identical config is a successful no-op with no revision increments.
14. Retrying the same request key for the same preview returns the original result without another mutation. Reusing that key for another preview fails. A consumed preview cannot be replayed later with a new key.
15. Publish supports bounded `delay_ms` for stale testing. After success, reconcile selected detail, published config, revisions, and status without reload while preserving active filters. On stale publish, preserve editor/preview and refresh current flag state.
16. Transient preview/publish failures preserve last-known-good UI state when possible. Prevent duplicate submission of the same in-flight action while keeping ordinary browsing usable.
17. Existing deterministic ordering/filtering, detail, note validation/no-op behavior, optimistic concurrency, and revision accounting must continue to pass.

## Constraints
- Keep the Python standard-library backend and dependency-free browser ES-module frontend; no database, Redis, queue, websocket, auth provider, or external API.
- State stays in one process/in memory. Use the checked-in subjects fixture as the preview population.
- Backend owns validation, canonicalization, rule precedence, assignment, previews, permanent config, revisions, and idempotency outcomes.
- Use a deterministic cryptographic hash from the Python standard library (or equivalently stable approach) for rollout bucketing.

## Out of scope
Authentication/permissions, creating/deleting flags, owner/status editing, persistence across restart, distributed locking, external subject lookup, more than `on`/`off`, nested boolean groups, regex/range/custom operators, or visual polish.

## Setup / run
```bash
./scripts/run.sh
```
Open `http://localhost:8080`.

## Tests / build
```bash
./scripts/test.sh
./scripts/build.sh
```
Starter tests cover existing behavior only. Add focused tests around the rollout semantics and state transitions you consider highest risk.

## 60-minute AI-assisted interview instruction
You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or similar tools. Inspect fixtures, mutation/revision boundaries, HTTP routes, and frontend state before changing code. Choose a correctness-first slice, implement incrementally, and verify ordinary, malformed, deterministic-assignment, stale, retry, no-op, and slow/out-of-order behavior.
