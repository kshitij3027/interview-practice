# POST-PRACTICE ONLY — CaseFold Interviewer Notes

**Never show this to the candidate before the hour ends.** The candidate README contains all required observable behavior and deliberately omits the intended approach and these checks.

## Intended reasoning and structure

This is an **atomic two-entity consolidation with in-process idempotency and activity-set reconciliation**, not a fuzzy duplicate detector or generic graph problem. The source and target cases are independently versioned. The chosen target is canonical, the source becomes a historical alias. A strong solution creates one domain operation with a single mutex/transaction protecting **both** cases and the request-key receipt map. The current Store mutex is adequate for the single-process model. Avoid updating source and target with separate calls or using frontend-calculated activity merges.

Choose (orgId, requestKey) as idempotency identity. Compare full logical payload (sourceId, targetId, expectedSourceRevision, expectedTargetRevision); if same key and payload, return the stored **original snapshot** before freshness checks. Verify the org can see the requested IDs before receipt lookup to prevent side channels. Validate a new attempt's IDs, tenant/customer equality and statuses, then both revisions. Compute a complete candidate timeline and detect conflicts **before** mutating any case. Commit source status and mergedInto, target priority/tags/timeline, source/target revision increments and receipt under the same critical section.

Activity map keyed by id, preserving each canonical {id, at, actor, text}. If the same ID has exact matching fields, dedup and count extra occurrences. If one field differs, reject the entire merge. RFC3339 timestamps must be parsed with time.Parse(time.RFC3339, ...); compare time.Time instants, then ID. The original at string must remain unchanged. Do not treat equivalent-offset strings as identical payloads unless candidate can justify that normalization under the exact field equality contract. Priority ranking high > medium > low; tags union unique and lexicographically sorted. Source's original timeline is left intact and still retrievable.

### Complexity

Let S and T be the activity counts of source and target and K be unique IDs. Build merged timeline with a hash index in expected **O(S+T)** time, then sort in **O(K log K)** time, with **O(K)** additional memory. An idempotency lookup should be average O(1) using an organization-qualified key. The existing list search scans all cases; optimizing list indexing is out of scope, but merging must not rescan all cases or all customer history. Receipts must store immutable snapshots, not pointers to the live target.

## Why naive approaches fail

- Blindly concatenating two timeline arrays double-counts partner redeliveries and preserves contradictory activity under one identity.
- Sort-by-string timestamps misorders differently offset RFC3339 instants.
- One case update followed by another allows half-merged data on collision or stale revision.
- Checking expected revisions outside the critical section permits two competing successful operations.
- A retry response synthesized from current state changes between attempts and can leak another customer's updates.
- Replaying after a prior merge and only then checking status mistakenly returns 409 rather than the original success.
- A browser that generates a fresh request key after a timeout can issue duplicate requests.
- Filtering a listing after pagination produces inaccurate totals and phantom pages.

## Supplied data discoveries

- CS-101, CS-102 and CS-103 belong to the same c-n-a customer, despite different statuses/priorities.
- partner-ev-7 is identical between CS-101 and CS-102; partner-ev-10 is identical between CS-102 and CS-103.
- partner-ev-8 claims different text in CS-104 and CS-105; merging these must be rejected with no revisions changed.
- CS-201 and CS-202 share c-m-a and contain distinct IDs at equal timestamps.
- Similar summaries for different customers must not be merged. Same organization alone is insufficient.
- The starter's note edit increments case revision and must block stale merge attempts.

## Hidden checks (post-practice only)

1. Successful CS-102 into CS-101: target priority high; status open, title/note preserved, tags sorted union, partner-ev-7 appears once; source becomes merged, points to CS-101, both revisions increment once.
2. Resolved CS-103 into an open target is allowed; canonical activity includes source events while source activity remains readable.
3. CS-104 into CS-105 conflicts on partner-ev-8; HTTP 409; both cases and receipt registry unchanged; later valid operation still works.
4. Same request key/payload after a successful merge and subsequent target note edit returns the identical original success response; no revision changes.
5. Same org/key but swapped source and target or changed expected revision returns 409. Different orgs may use the same key independently without leakage.
6. Cross-org source with valid target and a known key returns 404, not receipt. Same-org different-customer returns 400. Unknown target returns 404.
7. Stale source after note edit; stale target after note edit; no mutation; useful current snapshot on conflict.
8. Concurrent merges with shared target or source: exactly one succeeds, no double revision increment or activity duplication.
9. Sort activity at 2026-11-15T07:00:00-05:00 versus 2026-11-15T12:00:00Z by instant, then ID; don't use string order.
10. Repeated identical activity within one case counts once. Conflicting shared ID within a single case rejects the merge.
11. Directory totals fall after merge; source GET still works and exposes mergedInto; note update to merged source returns 409.
12. Reject boolean/fractional expected revisions, malformed request keys, unknown JSON fields, too-large request, invalid timestamps; do not mutate.
13. UI org/selection changes during network response must not show stale data; uncertain failure must reuse the same request key and payload.

## Alternative defensible designs

A sorted-merge implementation can be O(S log S + T log T) without a hash map and still be correct. Receipt storage may be a durable write-ahead record in production, but an in-memory map under the store mutex is sufficient here. A database transaction or compare-and-swap is appropriate for a multi-instance extension, outside this interview. Stable normalized canonical activity is defensible if exact identity and all original source fields are preserved.

## Likely AI-agent failure modes

Agents commonly add only a POST route and array concatenation; compute receipts from mutable state; ignore one revision; overwrite target note/subject; use globally unscoped request keys; forget directory counts; or build a browser action that loses its original payload after a network timeout. They may write tests that assert only status 200. Beware coercing JSON booleans/floats to integers, accepting unexpected fields, and timestamp lexicographic comparisons.

## Recommended prioritization (60 minutes)

1. **0–8 min:** Inspect fixture, existing store/API/UI/tests; articulate invariants.
2. **8–25 min:** Implement domain merge with full validation, dedup, revision and receipt handling under one atomic operation.
3. **25–37 min:** Add HTTP route, strict body parsing and tests for success/conflict.
4. **37–49 min:** Build browser target selection, retry/stale handling and authoritative refresh while preserving note edit.
5. **49–60 min:** Run scripts and targeted checks; fix correctness/privacy before polish.

## Walkthrough inspection points

Ask where the atomicity boundary sits, how retries survive lost responses, how external activity conflicts are detected, why ordering compares instants, what prevents cross-tenant and cross-customer merges, how note changes participate in revisions, why listing excludes merged sources, how late UI responses are ignored, and how the implementation scales to 20,000 activity entries per case. Ask the candidate to identify their most serious remaining limitation.
