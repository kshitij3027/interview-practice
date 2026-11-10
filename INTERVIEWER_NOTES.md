# POST-PRACTICE ONLY — FlagHarbor interviewer notes

Do not read these notes until after the 60-minute attempt.

## Intended structure and strong approach
The problem is a **multi-tenant, server-authoritative policy evaluation and transactional update** system with a small deterministic cohort-selection problem, not merely a form. Separate validation/canonicalization, evaluation, state mutation, HTTP translation and browser flow. Existing `createStore`, `getFlag`, `editNote`, `listCustomers`, selection epochs and HTTP error envelope provide integration points; preserving note editing is a critical regression.

An efficient domain path: normalize the policy to sorted unique plan/region arrays and sorted override entries. Validate all types without coercing floats, unknown IDs or prototype-mutating override keys. Resolve a per-organization customer map once or index for scale. Evaluate each customer independently with precedence: feature off → explicit deny → explicit allow → mismatched plan → mismatched region → stable bucket threshold → included. Use a stable keyed hash such as SHA-256 of a length-delimited `(orgId, flagId, customerId)` encoding to a 0..9999 integer; include when bucket `< 100 * percentage`. Keep buckets invariant across threshold changes so eligibility is monotone. Hash the ID, **not the customer's array index, plan, revision, or current policy**, and do not use `Math.random`/process-seeded hashes. 0/100 boundaries should be unconditional.

Compute whole-organization totals before pagination, sort by customer ID, and return only page rows. For persistent scale, index customers by org and flags by `(org,id)`, memoize cohort buckets by stable identity, and optionally maintain/cache audience counts invalidated by flag/customer changes. Straight O(C log C) sorting per request is acceptable for the fixture and a simple solution; repeated O(C) reads can be explained. Lookup/validation need not scan every customer for each override if indexed.

For writes, normalize and validate completely *before* mutating. Identity of a successful request key is `(org,key)` mapping to `{normalizedIntent,deepCopiedReceipt}`. Check this map before stale validation, replay the original receipt on identical intent even if the flag's revision changed. Reject key reuse for changed intent. An invalid/stale/unknown request does not claim a key. Node synchronous mutation without awaits between check and update suffices for this in-memory server; a real distributed backend requires a transactional compare-and-swap plus a durable unique idempotency record. A no-op policy still records a successful receipt but does not increment revisions. Notes must use the same revision field. Keep original response immutable using deep copies; never substitute current flag on replay.

Frontend: expose a form prefilled from `flag.rollout`, allow multi-select plan/region, percentage, and newline override syntax `customerId:allow|deny`. On submit freeze `policy`, `expectedRevision`, and `requestKey` into a pending intent. A failure that might have occurred after commit must retry *that exact object*. Distinguish validation/conflict HTTP responses from ambiguous transport failures. After success fetch detail+audience, but gate response application by an incremented selection or request token for org/flag/page; switching pages must not display an old page. On 409 refresh detail and require a new save intent. Re-fetch note detail after policy changes; editing a note should stale an older rollout form, not silently rebase it.

## Hidden checks / subtle traps
1. Feature `enabled=false`, but override is `allow`: always `feature_off`.
2. Explicit `deny` on enterprise/us and 100%: `explicit_deny`.
3. Explicit `allow` on starter/apac and 0%: eligible `explicit_allow`.
4. `plans=[]` or `regions=[]` with explicit allows: only allowed overrides eligible.
5. Increase percentage from e.g. 15 to 65: every previously included non-overridden customer stays included. Same IDs must hash identically across cold starts, pagination and shuffled fixture ordering.
6. Empty overrides, override for h-001 under org-cedar, unknown bad, duplicate plan entries, string percentage or fractional 33.5: reject invalid policies; no mutation, no key reservation. Plain JS objects need own-property checks.
7. Offset=1 and limit=2 with total=6: enabledCount is from all six, not the displayed two. Offset beyond end yields an empty page with unchanged total.
8. Save policy using revision N; change note to N+1 first: policy save must fail stale. Conversely rollout save stales an older note edit.
9. Successful save key K, later mutation, then replay K: exact original revision, datasetRevision, and policy. K reused with different revision conflicts; semantically equivalent reordered policy must replay.
10. Two saves at one expected revision with different keys: only first succeeds. Same key/intent twice: only one mutation.
11. Same requestKey under different organizations must not collide; flags remain organization-scoped.
12. Saving a policy identical after canonicalization: no revision bumps.
13. Invalid HTTP JSON, oversized body or nested malformed policy: structured error and no partial state.
14. Stale browser fetch after org/flag/page selection switch must not overwrite the screen. For network errors, retain exact original request key and payload.

## Why naive approaches fail
- Random rollout or customer-array-index modulo 100 shifts access on every request, fixture shuffle, pagination or insertion; growth may remove customers.
- Checking expectedRevision before replay turns genuine post-success retries into conflicts.
- Mutating before validating every override creates partial application; cross-org lookup leaks data.
- Reusing mutable flag objects as receipts changes historical responses after future updates.
- Counting page eligibility instead of whole-org, or trusting browser-derived decisions, breaks authority.
- Reissuing saves after lost responses with fresh keys can apply two writes.
- UI response races render the prior tenant's audience after quick switching.

## Suggested timing and prioritization
0–8 min inspect console/routes/fixture; 8–20 min policy validation and stable targeting; 20–33 min audience route, mutation and idempotency; 33–48 min browser editing and audience; 48–57 min focused tests and conflict handling; 57–60 min smoke run and explain tradeoffs. Credit a reasonable partial implementation with precise limitations.

## Walkthrough inspection points
Demonstrate seeded flag-search audience, saving a 100% matching policy, excluding an explicit-deny account, no-op save, stale note conflict, key replay after subsequent mutation, and switching org during slow fetch. Inspect complexity: per audience O(C log C) if sorting, per evaluation O(1) expected with set/indexed overrides, per write O(P+O) validation plus override lookup; memory O(C) per audience request and O(C+F+K) persistent in-memory state. Discuss distributed transactions for exactly-once effects.

## Alternative defensible designs
FNV-1a or any portable stable hash is defensible if distribution and monotonicity are explained. A 0..99 bucket is acceptable though less granular than 10,000. ETags / If-Match are fine if JSON contract is honored. A dedicated policy service or audience cache is fine if not prematurely complex. AI tools are permitted; grade observed behavior, not amount of generated code.

## Common AI-agent failure modes
Agents add editor controls with no authoritative evaluator, sort after pagination, stringify uncanonicalized policy as intent (key order differs), fail tenant checks on override IDs, generate a new UUID on every retry, or allow late fetches for a prior selection to win. Inspect code and tests rather than accepting claims that it works.
