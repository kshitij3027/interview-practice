# PulseDesk — HARD One-Hour Full-Stack Interview Exercise

## Context

PulseDesk is an internal customer-success console for a B2B SaaS company. Customer-success managers use it to inspect account health signals and, when business context demands it, place a temporary manual health override on an account.

The starter application already works. It uses PHP 8.4's built-in web server, an in-memory domain store loaded from JSON/JSONL fixtures, a dependency-free browser ES-module frontend with explicit client state, and existing tests for current account/signal/override behavior.

## Existing behavior

- The dashboard lists customer accounts with segment, owner, renewal date, and current manual health override.
- Selecting an account shows its raw health-signal observations.
- Accounts can be filtered by segment.
- A CSM can set or clear a manual health override (`healthy`, `watch`, or `critical`) with a non-empty reason.
- Manual override writes use the account revision for optimistic concurrency; stale writes are rejected without mutation.
- Every successful override change increments the account revision and global dataset revision exactly once.
- Restarting the backend resets state from fixtures.

## Customer/business problem

Leadership wants PulseDesk to calculate a consistent health classification instead of asking each CSM to interpret raw signals manually. The policy team has supplied a small ordered rule pack in `fixtures/health_policy.json`. Raw observations in `fixtures/signals.jsonl` are realistic rather than clean: rows are not guaranteed to be chronological, duplicate observation IDs exist, some observations are newer than the configured reporting cutoff, and individual metrics can become too old to trust.

CSMs may also change a manual override while a health calculation is still in flight. A slow calculation must not make the UI look as though the newer override never happened.

## Primary feature request

**Add an explainable account-health evaluation workflow that derives each account's effective health from the policy pack and signal observations, while honoring active manual overrides and preventing stale asynchronous results from overwriting newer account state.**

## Acceptance criteria

1. Add a backend health-evaluation API and corresponding UI for the currently selected account. The UI must show the effective classification and a concise ordered explanation of why it was produced.
2. The policy file defines an `as_of` timestamp, metric freshness limits, and an ordered list of rules. Treat the backend policy fixture as authoritative; do not reimplement the authoritative evaluation only in the browser.
3. For a given account and metric, choose observations using event time, not JSONL file order. Ignore observations strictly after policy `as_of`.
4. Duplicate observations are identified globally by `observation_id`. Exactly one occurrence of a duplicated ID may influence evaluation. Which occurrence wins when duplicate payloads differ must be deterministic and documented in code or tests.
5. After deduplication and `as_of` filtering, the value for each metric is the latest eligible observation by `observed_at`. If two different observations for the same account/metric have the same timestamp, use a deterministic tie-break that does not depend on file order.
6. Each metric has a configured `max_age_hours`. A latest observation older than that freshness window relative to `as_of` is treated as missing for policy evaluation, but the explanation must distinguish stale from never-observed.
7. Rules are evaluated in fixture order and the first matching rule wins. Every condition within one rule must match. Supported operators are `lt`, `lte`, `gt`, `gte`, and `eq`.
8. A rule condition that references a missing/stale metric does not match unless that condition explicitly uses `{ "missing": true }`. A `{ "missing": false }` condition matches only when a fresh value exists.
9. If no rule matches, return the policy's configured default classification. Rule evaluation and explanation ordering must be deterministic regardless of signal-file order.
10. If an account has a manual health override, that override is the effective classification. The response must still include the policy-derived classification separately so the UI can explain that a manual decision is masking the derived result.
11. Every evaluation response must include the account revision and global dataset revision captured for that evaluation. The response must be internally consistent with one snapshot of account/override state.
12. The evaluation request must support an optional bounded local delay (for example `delay_ms`) so stale-response behavior can be exercised without external infrastructure.
13. If a manual override is changed or cleared while an older evaluation request is in flight, the frontend must not render that older response over the newer known account/dataset revision. It may discard the stale response or fetch a replacement, but the final visible state must reflect the newer override.
14. Rapidly switching selected accounts while evaluations are in flight must not let the previously selected account's response overwrite the newly selected account's health panel.
15. A transient evaluation failure must leave the last known-good evaluation visible for that account when one exists and show an actionable error; it must not clear the account list or raw signal history.
16. After a successful manual override set/clear, keep the selected account and current segment filter, reconcile revisions without a browser reload, and refresh/reconcile the displayed health evaluation.
17. Existing account filtering, raw signal display, override validation, optimistic concurrency, and revision behavior must continue to work.

## Constraints

- Keep the existing PHP 8.4 + browser ES-module stack.
- Keep state in one process and in memory; no database, Redis, queue, auth provider, or external API.
- Use the timestamps from fixtures; do not make correctness depend on the machine's wall clock.
- You may add service/domain modules, routes, frontend state/actions, and focused tests.
- Keep the implementation interview-sized and preserve the existing manual-override workflow.

## Out of scope

- Configurable policy editing UI.
- Background recalculation jobs or polling.
- Statistical models or machine learning.
- Persisting overrides across server restarts.
- Authentication/authorization.
- Multi-process/distributed coordination.
- Visual charting libraries or design polish beyond a clear usable workflow.

## Setup / run

```bash
./scripts/test.sh
./scripts/build.sh
./scripts/run.sh
```

Open `http://localhost:8000`.

## Tests / build

```bash
./scripts/test.sh
./scripts/build.sh
```

Existing tests cover current behavior only. Add focused feature tests based on the requirements; there are intentionally no starter TODOs or feature-specific tests that reveal the intended design.

## 60-minute interview instruction

You have **60 minutes**. Treat this as a demanding AI-assisted full-stack/product-engineering interview. Inspect the repository, fixtures, state flow, and current invariants before changing code. Prioritize the highest-risk semantics first, implement incrementally, and leave observable verification behind.

A polished panel that mis-handles duplicate observations, event-time ordering, freshness, first-match rules, override precedence, or stale async responses should not be considered a strong solution.
