# FlagHarbor — HARD 60-minute AI-assisted full-stack interview

## Context
FlagHarbor is an internal feature-operations console for a multi-tenant SaaS platform. Support and product engineers use it to inspect feature flags for customer organizations, find a flag by name, and record operator notes before changes reach production. Customers within each organization have a plan and geographic region.

## Existing behavior (already working)
The starter uses **Node.js 20+**, an HTTP server with fixture-backed in-memory state, and a dependency-free browser JavaScript frontend. Choose an organization, search feature flags by name, filter enabled/disabled flags, select a flag, and edit its internal note. Lists are ordered by flag ID, `total` counts before the result limit, notes are trimmed, no-op edits do not increment revisions, and stale note edits return 409. The UI prevents late list/detail responses for a previous selection from overwriting the current one. Organization-scoped endpoints never expose another organization's flags. **Preserve these behaviors.** Data resets on server restart.

## Supplied data
`fixtures/workspace.json` includes three organizations, 11 customer accounts (each with plan/region), six flags (each with `enabled`, `revision`, and `note`) and initial rollout configuration. Existing `server/domain.js`, `server/http.js`, `public/`, and `tests/` implement the working console. The rollout configuration in the fixture is seed data; nothing currently evaluates or edits it.

## Customer/business problem
A product manager wants to expose a feature to selected subscription plans and regions, then gradually increase access without changing customer IDs or re-randomizing an existing pilot. Some named customers must be allowed into a pilot; others must be explicitly excluded. Operations needs to see **which** customers are eligible and **why**, not just a percentage. A customer-support operator may change the flag note while someone edits rollout settings. And a save may succeed even if its HTTP response is lost. The correct answer must come from the server, not from an optimistic client guess.

## Primary feature request
**Add one end-to-end customer rollout editor and audience-inspection workflow.** Allow an operator to edit a flag's targeting policy and inspect deterministic eligibility decisions for customers in that organization. Implement domain behavior, HTTP routes, browser controls and focused tests; the existing directory and note editor must keep working.

## Acceptance criteria — observable behavior
1. Add `GET /api/flags/:id/audience?org=<organizationId>&offset=<n>&limit=<n>` returning `{flagId,revision,total,enabledCount,customers}`. Each customer row is `{id,name,plan,region,eligible,reason}`. `total` is the count of **all** organization customers before pagination, and `enabledCount` is the number eligible across the **entire** organization. Rows sort by customer ID before pagination. Default `offset=0`, `limit=25`; require integer offset `0..100000` and limit `1..100`. The endpoint must not leak customers or flags belonging to another organization; unknown/hidden flags return 404; bad pagination returns a structured 400.
2. A rollout policy is `{plans,regions,percentage,overrides}`. `plans` is an array of unique values from `starter`, `team`, `enterprise`; `regions` is an array of unique values from `us`, `eu`, `apac`; `percentage` is an integer from `0` to `100`; `overrides` maps **existing customer IDs in that organization** to exactly `allow` or `deny`. Empty plan/region arrays match no non-overridden customers. Reject invalid enums, duplicate entries, unsafe numerical values, unknown/cross-organization customer overrides, malformed objects and over 100 overrides. Never partially apply an invalid policy. Plan/region array order and override object key order are semantically irrelevant.
3. Eligibility reasons are exactly `feature_off`, `explicit_deny`, `explicit_allow`, `plan_mismatch`, `region_mismatch`, `percentage`, and `included`, with that priority. A disabled feature is **never eligible**, even with an explicit allow. Otherwise explicit denies win, then explicit allows win even when plan, region or percentage would exclude a customer. For non-overridden customers, require a matching plan and region, then admit the specified percentage. A `0%` policy includes no non-overridden customers; `100%` includes every customer passing plan and region. For each customer and flag, the intermediate percentage decision must be deterministic across requests, restarts, input order, pagination and changes to unrelated accounts; raising the percentage must not remove someone who was already admitted. Explain your choice for stable percentage assignment during the walkthrough. Do not call an LLM or use per-request randomness for eligibility.
4. Add `POST /api/flags/:id/rollout?org=<organizationId>` with JSON `{policy,expectedRevision,requestKey}`. `expectedRevision` is the flag's currently observed nonnegative safe integer; `requestKey` is a trimmed string of length 8–64. Successful non-no-op changes replace the entire policy, increment **only that flag's** revision once, increment `datasetRevision` once, and return an immutable receipt `{requestKey,flagId,revision,datasetRevision,policy}`. Identical normalized policies are a no-op: preserve both revisions while returning a receipt. Validation errors return `{error:{code,message}}` with HTTP 400; hidden flags return 404; stale writes return 409 `STALE_REVISION`. The server owns the revision check and write.
5. A successful request key is scoped to an **organization** and identifies the complete intent `(flagId,expectedRevision,normalizedPolicy)`. An identical-key/identical-intent retry returns the **original response** unchanged, even after subsequent note edits or policy changes. A same-key/different-intent request returns 409 `KEY_CONFLICT`. Validation and stale rejection must not reserve keys. Concurrent saves must not both advance one revision; check successful replays before rejecting a now-stale revision. Preserve the original receipt's snapshot.
6. The browser must provide understandable plan/region/percentage/override controls for the selected flag, an action to save a rollout, and an audience table with eligibility reasons, totals and pagination. It must distinguish pending/success/error results, display the server's current revision, and refresh authoritative flag and audience data on success without a full-page reload. Parse/serialize overrides predictably and show validation errors rather than silently ignoring lines.
7. On a possible transport failure, keep the **same request key and the exact submitted policy/revision** for safe retry instead of generating a new key. On `STALE_REVISION`, keep the flag selected, explain the conflict and refresh authoritative data before a genuinely new save attempt. Disallow accidental double submissions while a request is pending. Ignore late detail/audience responses after switching organizations, flags or pages. An intervening **note edit** must invalidate an older rollout write. A changed rollout must also make an old note edit stale.
8. The `enabled` switch is not editable in this exercise; its seeded value controls the eligibility gate. Do not silently mutate it, mutate customer plans/regions, or change an organization's customers. Validate all policy inputs on the server even if the browser performs prevalidation. The API's error shape is `{error:{code,message}}`. Request bodies are capped at 32 KiB in the provided server; keep sensible bounded input handling.
9. The fixture is intentionally small; a production organization could have 100,000 customers and hundreds of flags, with frequent audience reads. Avoid quadratic per-customer operations, non-deterministic ordering, and whole-dataset state copies for each save. Describe expected time/space costs and what you would index or cache at scale.
10. Add focused tests for explicit override precedence, disabled flags, 0/100 percent, stable percentage decisions, cross-tenant overrides, policy validation, pagination and counts, stale notes/saves, no-op revision behavior, replay after later mutations, key collisions and race-like back-to-back requests. All existing tests must remain green.

## Constraints
Keep the Node HTTP server, fixture-backed in-memory state and browser frontend. No database, deployment, login system, external feature-flag provider, cloud services or UI framework is required. You may reorganize code, but avoid unnecessary infrastructure. The new operation is **one rollout-management feature**; do not implement a feature-flag SDK for downstream applications. Treat organization selection as the existing demo tenant boundary.

## Out of scope
Persisting changes across restarts, editing account attributes, enabling/disabling flags, emitting production events, statistical rollout analysis, and external authorization are not requested.

## Setup, verification and run
Requires Node.js **20 or newer**. No dependencies or installation step.

```bash
./scripts/build.sh
./scripts/test.sh
./scripts/verify.sh
./scripts/run.sh
```

Open **http://127.0.0.1:8080**. Existing API examples:

```bash
curl 'http://127.0.0.1:8080/api/flags?org=org-cedar&status=enabled'
curl 'http://127.0.0.1:8080/api/customers?org=org-cedar'
curl 'http://127.0.0.1:8080/api/flags/flag-search?org=org-cedar'
```

## Interview instruction — 60 minutes, AI-assisted
You have **60 minutes**. Use Claude Code, Codex, ChatGPT or another AI assistant if helpful. First inspect the running application, existing state/HTTP/frontend flow and fixture. Make explicit scope and correctness tradeoffs, implement incrementally, keep the baseline green, add targeted tests and demonstrate an end-to-end change in the browser or API. Be prepared to explain how your decisions handle unusual input, retries, concurrency and a much larger customer population. A credible partial implementation with defensible reasoning is preferable to an unverified one-shot rewrite.
