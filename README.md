# FindFix — HARD 60-minute AI-assisted full-stack interview

## Context
FindFix serves multiple customers whose support agents search a knowledge base. Operators want a targeted way to pin official answers, boost useful matches, or suppress misleading articles for a recurring support query. A curated answer for one customer must not leak to another.

## Existing behavior
The starter **already runs** using Node.js 20+ standard-library HTTP, fixture-backed in-memory state, and browser ES modules. Operators can select a tenant; search published articles by term and category; inspect article details; and edit internal notes. Search uses the existing deterministic score then article-ID order, with `total` before `limit`. Empty searches list published articles. Outdated list/detail responses cannot replace newer selections.

Note edits trim whitespace, require the article's `expectedRevision`, reject stale writes with 409, and increment article and tenant revisions exactly once on a real change. A no-op increments neither. Preserve all these behaviors.

## Supplied data
`fixtures/catalog.json` contains two tenants and twelve articles with IDs, titles, bodies, tags, categories, publication status, note and revision. It includes archived articles, content with no textual match for plausible searches, and records owned by another tenant. Restart resets state.

## Customer/business problem
Orchid Cloud asks support admins to curate the exact query "login": elevate an approved article, hide outdated guidance and boost another answer. They must preview what an agent would actually see before publishing. Two admins may concurrently edit notes or publish curations, and a lost HTTP response may prompt a retry.

## Primary feature request
Implement **one end-to-end query-curation preview-and-publish workflow** across domain, HTTP API and browser. Curations are scoped to one tenant and one normalized, nonempty query. A draft consists of 0–8 decisions of the form `{articleId, action}`, with action `pin`, `boost` or `hide`. At most two decisions may be pins. Pin order follows the draft input order; order of boost/hide decisions does not matter. Duplicate article IDs are invalid. Publishing an empty list removes the query's existing curation.

## Acceptance criteria
1. UI: load currently published decisions for tenant/query, edit a draft, preview current-vs-proposed ranked results, publish exactly the previewed draft, display success/no-op/stale/error, and preserve edits after a failure.
2. Use the existing `normalizeTerm` behavior for rule keys: Unicode NFKC, trim, locale-aware lowercase and whitespace collapse. Reject empty normalized queries. Rule matching must use **whole normalized query equality**, not substring matching, and never affect an empty search.
3. Validate every decision before preview: 0–8 entries, at most 2 pins, unique article IDs, supported actions, and articles that exist, are published and belong to the selected tenant. Reject invalid drafts with a clear 4xx; never partially accept or expose another tenant's article.
4. Search semantics: category and publication eligibility apply **before** curation. Hide eliminates a matching article; pin places an eligible article first (in specified pin order) **even with base score zero**. Ineligible pins never appear. Boost adds exactly **5** to an eligible article's *positive textual score*, but must not make a zero-score article appear.
5. Order eligible pins first, then remaining eligible textual matches ordered by effective score descending and article ID ascending. No duplicates. Calculate `total` after curation but **before limit (1–50)**; apply the limit only after pin/hide/boost. Searches with no applicable rule keep the pre-existing ranking and response behavior.
6. Preview is **read-only**: show before and after ordered IDs, scores, totals, category, limit and observed tenant revision. Server must bind publication to **the exact validated draft previewed**. Do not trust client-computed rank results or a subsequently modified draft.
7. Publish must accept an `expectedTenantRevision` and a request key (trimmed, 1–80 characters). A tenant mutation since the preview — including an unrelated article-note edit — makes publication stale (HTTP 409, no mutation). Invalid/stale attempts change no revision and must not reserve successful idempotency keys.
8. Idempotency: retrying a previously successful publication with the same tenant, trimmed request key and original preview intent returns the same success/no-op receipt with no new mutation, even after a later tenant change. Reusing the key for a different intent yields 409. Separate tenants may reuse the same request key.
9. A changed published curation increments **that tenant revision once** and **the rule revision once**; article revisions and other tenants remain unchanged. Semantically identical boost/hide reorderings are no-ops; changed pin order is not. Deleting an existing rule counts as a change; deleting a nonexistent rule is a no-op. Published search and rule reads immediately reflect the new state.
10. UI race/retry behavior: older preview/search/detail responses must not overwrite newer tenant/query/category/draft state. Changing draft or scope invalidates a preview. After publish, refresh visible search and published decisions. On 409 preserve draft for fresh preview. Retrying the same timed-out publication must reuse the request key.

## Constraints
Production may have 100,000 articles, 10,000 curated queries and repeated searches. Avoid needless quadratic work, stale cached results, and bulk copying all article objects per preview. The checked-in fixture is deliberately small; add focused correctness tests for large/edge cases. Cases worth exploring: full-width Unicode query aliases, zero-score pins, boost-only nonmatches, category-filtered pins, limit-before-pinning bugs, archived/cross-tenant IDs, duplicate decisions, stale note edits, semantically equivalent no-ops and lost-response retries.

## Expected deliverable
Working domain and HTTP implementation, a usable browser draft/preview/publish flow, new focused tests and a brief design/performance explanation. Endpoint names and internal design are yours to choose as long as all observable behavior holds.

## Out of scope
External search/LLM service, authentication provider, databases/queues, distributed persistence, audit analytics, article-content editing, and visual redesign.

## Setup / run / test
Node.js **20+**, Bash, and no `npm install`:
```bash
./scripts/test.sh
./scripts/build.sh
./scripts/verify.sh
./scripts/run.sh
```
Open http://localhost:8080. Alternatively `npm start`, or `PORT=8081 npm start`. Starter tests cover existing behavior **only**, not the requested feature.

## Explicit 60-minute AI-assisted interview instruction
You have **exactly 60 minutes**. Claude Code, Codex, ChatGPT and documentation are allowed. Inspect the working app and supplied data first. Implement incrementally, test domain invariants, verify integration, and be ready to defend tradeoffs in correctness, latency, complexity, retries and UI state. End with a walkthrough of what works, what is incomplete and how you verified it.
