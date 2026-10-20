# CaseFuse — HARD one-hour AI-assisted full-stack interview

## Context
CaseFuse is a B2B support-operations console. A customer's incident frequently produces several support tickets through email, chat and escalations. Agents want a trustworthy way to consolidate duplicate cases while retaining conversation provenance and protecting active agent work.

## Existing behavior
The **starter application already works** with a Node.js 20+ standard-library HTTP API, in-memory fixture-backed domain state and dependency-free browser ES modules. Agents can filter cases by tenant and lifecycle, search by case ID, customer ID, issue key and subject, open details, read a chronological activity feed and edit internal notes. Note writes use `expectedRevision`; a changed trimmed note increments both the case and dataset revisions once, a no-op changes neither, and stale writes fail with HTTP 409. Slow list/detail responses must not replace a newer filter or case selection. Preserve these working flows.

## Supplied data
`fixtures/cases.json` includes ten tickets across two tenants, multiple customers, lifecycle states, owners, urgency levels, labels and SLA deadlines. `fixtures/activity.jsonl` contains unordered support events, IDs repeated across cases with either equivalent timestamp representations or inconsistent contents, and distinct events from different channels. Restarting resets the data.

## Customer/business problem
Several of Acme's mobile-login tickets describe the same incident. A support manager wants to designate one primary ticket and absorb one or more duplicates while retaining all distinct activities and deadlines. A note edit may race a slow merge. A lost HTTP response can trigger a retry. A merge must never leak or mutate another tenant's or another customer's records.

## Primary feature request
Implement **one case consolidation feature** across server domain state, HTTP API and browser UI. Let the operator choose a primary case and 1–5 source cases, review their observed revisions, submit an atomic merge, see the resulting case and audit receipt, and recover safely from stale state and lost requests. The backend is authoritative; the browser must not construct or trust merged events.

## Acceptance criteria
1. Implement `POST /api/cases/merge`, receiving `{primaryCaseId,sourceCaseIds,observedRevisions,requestKey,delayMs?}`. Return the updated primary case and timeline, absorbed IDs, a merge audit receipt, per-case revisions and dataset revision. Distinguish HTTP 400 invalid input, 404 unknown cases and 409 conflicts, with useful structured details; any failure is atomic.
2. `primaryCaseId` is a nonempty string. `sourceCaseIds` contains 1–5 **distinct** case IDs, none equal to the primary. `observedRevisions` has exactly the participating IDs as keys and a nonnegative safe integer for each; reject missing and extra entries, duplicate sources and unknown IDs.
3. All participants must share the exact `tenantId` and `customerId`. The primary must be `open` or `pending`; a source may be `open`, `pending` or `resolved`. No already-`merged` case may participate. An invalid source invalidates the entire action, not merely that source. Different issue keys are permitted if the operator chooses to consolidate them.
4. Preserve the primary's ID, subject, issue key, owner, status, note and openedAt timestamp. Its priority becomes the most urgent among all participants using `P0 > P1 > P2 > P3`. Trim and ASCII-lowercase labels from all participants; remove blanks and duplicates and sort ascending.
5. Calculate primary `slaDueAt` as the earliest non-null deadline **among cases that were open or pending before the action**. Compare offset-aware timestamp strings as instants. A resolved source's earlier deadline must not shorten the primary SLA. If none of the active participants has a deadline, use null.
6. Consolidate the event timelines. Events with the same `eventId` and identical `type`, `body` and `externalRef` and the same actual timestamp represent one activity even if timestamp strings have different offsets. Choose one representative deterministically. If any repeated ID has different contents or instant, reject the entire merge with an explicit evidence-conflict error and no changes. Sort final activity ascending by instant, then event ID, independently of fixture row order. The primary's subsequent GET must show this same consolidated activity.
7. Mark every source case `merged` with `mergedInto` equal to the primary ID. Keep its detail accessible for audit, including status-filter visibility. Record exactly one audit entry on the primary with merged source IDs and originating case revisions. Unrelated cases' details and activity remain unchanged.
8. A successful merge increments each participating case revision **once** and the global dataset revision **once**. Preserve note-edit conflict behavior, trim/no-op semantics and all existing filters.
9. Normalize `requestKey` by trimming; require 8–64 characters. Its request identity is primary ID, sorted source IDs and sorted observed case/revision pairs. Source order and delay do not affect identity. A successful same-key/same-intent retry returns the original receipt without mutating state, including after subsequent edits. A same-key/different-intent request returns 409. Failed validation or stale merges must not consume keys.
10. Optional `delayMs` must be an integer 0–1200. Recheck all participating revisions immediately before mutation, **after any delay**. A competing note edit during the delay must make the merge stale without partial application. Concurrent same-key requests must not merge twice.
11. Build a usable browser workflow for selecting eligible source cases, submitting the merge, displaying the authoritative receipt and updated merged timeline, and understanding failures. Preserve selected inputs on network failure. On stale revisions refresh authoritative information so the operator can choose whether to retry.
12. Switching selected cases or filters while merge/detail requests are in flight must not display obsolete responses as current. Prevent unintended double-click duplicate submissions. Refresh relevant case list, selected details, statuses and versions after success, without reloading the page.
13. Add targeted verification for repeated events, inconsistent evidence, resolved-case SLA exclusion, label normalization, cross-customer/tenant rejection, stale writes, concurrent retries, revision accounting, and existing behavior. Production scale can be 100,000 cases and 1 million activities; avoid repeatedly searching unrelated events and be ready to explain scale and time/space tradeoffs.

## Constraints
Keep Node.js standard library, a single-process in-memory application, checked-in fixtures and dependency-free browser code. Do not add a database, Redis, auth provider, background queue, framework, external service, or mandatory installation step. The customer problem is deliberately rich; prioritize correctness of a credible vertical slice.

## Out of scope
Real helpdesk integrations; reversing merged cases; cross-customer identity matching; persistent storage; distributed locks; permission enforcement beyond the stated tenant/customer checks; aesthetic design polish.

## Setup and verification
Requires Node.js 20+; no npm installation needed.

```bash
./scripts/test.sh
./scripts/build.sh
./scripts/verify.sh
./scripts/run.sh
```

Open `http://localhost:8080`. Existing `npm test`, `npm run build` and `npm run verify` commands also work.

## Explicit 60-minute AI-assisted interview instruction
Use **60 minutes** and any AI assistant (Claude Code, Codex, ChatGPT or similar). Explore the existing app, tests and fixtures before changing code. Break down the customer request, implement progressively, run the tests and explain your assumptions and tradeoffs in a walkthrough. A happy-path-only implementation that silently duplicates activity, ignores stale edits or loses provenance is insufficient.
