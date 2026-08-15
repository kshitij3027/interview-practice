# LaunchPad — HARD One-Hour Full-Stack Interview Exercise

## Context
LaunchPad is an internal feature-rollout control plane for a SaaS company. Product engineers use it to inspect accounts and manually override whether a feature flag is enabled for a specific customer.

The starter app already works. It uses a dependency-free Node.js HTTP API, an in-memory domain store, a browser ES-module frontend with explicit client state, JSON/CSV fixtures, and existing tests for current override behavior.

## Existing behavior
- The dashboard lists accounts with plan, region, employee count, and current explicit override.
- Operators can filter the account table by plan.
- Operators can manually enable or disable `smart-compose` for one account.
- Every manual override increments the flag revision and dataset revision.
- Manual overrides use optimistic concurrency: a stale expected revision is rejected.
- Restarting the backend resets state.
- Existing tests cover current loading, validation, and stale-write behavior.

## Customer/business problem
A product manager wants to roll `smart-compose` out gradually to customer cohorts instead of managing dozens of one-off overrides. Cohort definitions arrive from the business as rows like those in `fixtures/cohorts.csv`.

The rollout must remain predictable even when cohort filters overlap, existing explicit overrides exist, operators supply exclusions, and another operator changes the flag while a rollout is being prepared.

The company also requires percentage rollout to be stable over time: an account that falls into the first 30% today should not jump in and out of that 30% merely because account-list order changes.

## Primary feature request
**Add a cohort-based percentage rollout workflow that deterministically selects eligible accounts, respects explicit overrides and exclusions, and safely applies a requested rollout without overwriting a newer flag revision.**

## Acceptance criteria
1. Add UI controls to choose one cohort from `fixtures/cohorts.csv`, choose a rollout percentage from 0–100, optionally enter comma-separated account IDs to exclude, and inspect which accounts would be affected before applying.
2. Cohort matching must support `plan`, `region`, and `min_employees`. Blank `plan` or `region` means “any”; `min_employees` is inclusive.
3. Explicit per-account overrides are authoritative. Accounts with any explicit override must be reported separately and must not be changed by cohort rollout.
4. Unknown exclusion IDs must be reported, but must not abort the whole calculation.
5. Percentage selection must be deterministic and independent of account-list order. The same flag key, account ID, cohort, and percentage must always produce the same selected set until those inputs change. Do not use `Math.random()`.
6. Percentage selection must be monotonic for a fixed cohort: every account selected at 30% must also be selected at 40%.
7. The calculation result must distinguish at least: selected eligible accounts, eligible accounts not selected by percentage, explicitly overridden accounts, excluded accounts, and unknown exclusions.
8. Add a backend apply action that enables the flag for exactly the selected eligible accounts from the operator’s current calculation. It must include the flag revision the calculation was based on.
9. If the flag revision changed after calculation—such as another manual override occurring—the apply action must reject the rollout without partially changing cohort accounts.
10. Successful apply must set an explicit `true` override on each selected account and increment the flag revision exactly once for the entire rollout, not once per account.
11. Re-submitting the same successful rollout request must be retry-safe: it must not increment the revision again or apply additional accounts.
12. The server must not trust a client-supplied arbitrary list of account IDs as proof of cohort eligibility; authoritative rollout semantics must remain server-side.
13. After successful apply, the account table and displayed revisions must reconcile without a browser reload.
14. If apply fails because the revision is stale, preserve the operator’s cohort, percentage, and exclusions, show a useful conflict message, and make it straightforward to recalculate.
15. Existing single-account manual override behavior, validation, plan filter, and stale-write protection must continue to work.

## Constraints
- Keep the dependency-free Node.js + browser ES-module stack.
- Keep state in memory; no database, Redis, auth provider, queue, or external service.
- You may add routes, domain/service modules, server-owned temporary state, and tests as needed.
- Do not replace the existing single-account override workflow.
- The backend is authoritative for rollout selection and apply semantics.

## Out of scope
- Scheduled/time-based rollouts.
- Multiple feature flags.
- Authentication/authorization.
- Distributed/multi-process coordination.
- Persistence across backend restarts.
- Visual polish beyond a clear usable workflow.

## Setup / run
```bash
npm start
```

In another terminal:
```bash
python -m http.server 5173 -d web
```

Open `http://localhost:5173`.

## Tests / build
```bash
npm test
npm run build
```

Existing tests cover current behavior only. Add focused feature tests based on the requirements.

## 60-minute interview instruction
You have **60 minutes**. Treat this as an AI-assisted live coding interview. Inspect the starter architecture and fixtures before making changes, identify the highest-risk correctness requirements, implement incrementally, and verify both the domain behavior and browser flow.

A polished happy path with unstable percentage bucketing, broken override precedence, unsafe stale handling, non-idempotent apply, or regression of manual overrides should not be considered a strong solution. Prioritize correctness and verification over styling.
