# PermitLens — Interviewer Notes (POST-PRACTICE ONLY)

**Do not share with the candidate until after the 60-minute exercise.** This document discusses the underlying problem structure, design approaches, hidden checks and likely failure modes.

## Intended problem structure
This is a temporal evidence-reconciliation problem combined with a conditional interval-based reservation and an optimistic, retry-safe full-stack transaction. The candidate is not required to use a particular algorithm or framework. A strong implementation separates a **read-only server-side review** from an **atomic issuance**; validates the current state before commit rather than accepting a verdict from the client; and uses deterministic explanations when evidence is incomplete.

The existing Python `VisitStore` has an RLock, revisioned notes and tenant-scoped reads. One defensible solution adds a domain review operation and issue command, plus a short-lived map of authoritative preview records and an immutable receipt map keyed by normalized (tenant, requestKey). Index credentials by vendor/category and issued visit intervals by site at initialization; update the pass index on each issue. Expose new HTTP POST routes in `server.py` and connect to the existing browser app without destabilizing note edits or navigation. There is no benefit in a paid LLM/API for the core correctness decisions; such tools can be justified for human-friendly explanation only if the numeric/time rules stay authoritative.

## Evidence reconstruction
Parse dates as timezone-aware instants, not lexical timestamp strings. Reject malformed rows locally without aborting unrelated vendors. Before computing current credential state, group by `eventId`: if that ID is used by different vendor IDs, discard the entire ambiguous identity; otherwise retain the latest recorded replay, breaking equal receipt instants by greatest canonical JSON payload. Canonical JSON has sorted keys and stable separators. Next, for each (vendor, required category), choose a surviving record effective no later than arrival by greatest effective instant, then latest received instant, then lexicographically smallest event ID. The winning record must be verified, with expiry at or after scheduled departure. Missing, revoked and expired are different reasons. Older revocations must not override later verification; a newer receipt for an earlier effective event does not automatically override a later effective event.

Production approach: parse/group O(E), sort per vendor/category O(E log E) once, then binary-search state for an arrival O(log E_vendor_kind), plus worst-case tie checks. A simple scan of a small vendor's few records is defensible with documented skew assumptions, but scanning all 250k events for each of 100k visits is not. Build reliable explainable semantics before optimizing.

## Temporal access and occupancy
Validate visit start/end as whole-minute, timezone-aware ISO-8601 instants; start < end; <=12 hours. Convert to UTC calendar date and ensure both endpoints fit wholly in one date and the site's [openUtc, closeUtc) access window. Arrival at open is valid, departure at close is valid, crossing UTC midnight is invalid by requirement. Only current issued visits at the same site consume capacity. A new pass is permitted iff adding its half-open [start,end) interval never makes concurrency exceed the site's capacity at any moment. Build endpoint deltas for intersecting issued visits (+1 at start, -1 at end) and process departures before arrivals for equal timestamps. Check the peak over the full proposed interval; checking only the arrival instant is incorrect. Use site-specific indexing or suitable interval/range-max structure rather than global scans for production. Sorting relevant endpoints costs O(P_site log P_site) for a basic sweep; incremental interval/range indexing can provide O(log P) updates and fast bounded queries. Explain worst-case heavy concentration at one site.

## Atomic issue, revisions, preview, and replay
Preview stores server-derived eligibility and exact account/visit/window plus observed revisions with <=10-minute TTL. It never mutates the visit or consumes a request key. In issue, normalize/validate key; **check recorded successful replay first**, including payload identity, even if the original preview is expired/consumed or the dataset revision has since changed. Same identity returns the exact immutable original receipt, different intent gives 409. For a genuinely new issuance, validate token/eligibility/revisions. If a delay is requested, sleep *outside* the mutation lock. Under the lock after delay, recheck observed target and dataset revisions, status, vendor/evidence, opening window and capacity. Only then create a unique deterministic pass ID, set status issued, append exactly one audit record, increment target and global revisions once, consume token, and record the successful immutable receipt. No rejected operation can partially change state or reserve its key. Single-process locking is sufficient for this starter; a production multi-process architecture would need durable uniqueness constraints and a transaction.

## Fixture discoveries (candidate should inspect)
- Two Harbor sites have different required evidence, opening windows and capacity; Orchid is isolated under a second account.
- `VIS-001` initially coexists with a pre-issued yard visit, but issuing another overlapping contractor changes capacity.
- `VIS-002` initially appears individually possible but can conflict after `VIS-001` is issued.
- `VIS-004` looks safe at arrival but overlaps an annex pass later; arrival-only occupancy gives a wrong answer.
- `VIS-005` crosses UTC midnight; `VIS-003` has an inactive vendor; `VIS-007` was cancelled and `VIS-008` already has a pass.
- `VIS-006` follows a background revocation effective after the initial verified event.
- `VEN-202` has safety evidence expiring at the exact end of `VIS-010`, which is acceptable.
- `C-VEN-102-insurance` has an older received replay with a shorter expiry. `REUSED-ID` is ambiguous across vendors and must be excluded. `BAD-DATE` is malformed but cannot poison all evidence.

## Hidden checks / adversarial cases
1. An offset-equivalent timestamp must be treated as the same instant. Naive dates and fractional seconds fail window validation.
2. Two copies of one event ID may differ in effective time; deduplicate by recordedAt before choosing effective evidence.
3. Equal recordedAt replay: greatest canonical JSON; equal effectiveAt among distinct IDs: latest recordedAt then **smallest** event ID.
4. Same eventId across vendors must be discarded for *both*, not silently assigned to the most recent vendor or globally corrupt all that vendor's other events.
5. Revocation effective exactly at arrival applies; a verification arriving after the visit's start but effective earlier is still potentially relevant.
6. Credential expiring exactly at departure is valid; one minute before is invalid.
7. Check opening-time equality, closing-time equality, UTC midnight crossing and endpoints that only touch.
8. Capacity may peak *mid-visit*. An existing issued pass ending at new arrival should not overlap; confirmed/requested visits don't consume capacity.
9. Two eligible previews competing for the final slot: only one can succeed after a delay and atomic revalidation.
10. An unrelated visit note edit increments dataset revision and stales the previously reviewed issue.
11. A same-key successful replay must succeed even after later note edits, other passes, or preview expiration; changed intent must 409; failed-key retry can succeed after correcting the request.
12. A token can only be consumed once. A different key cannot create a second pass from a consumed preview.
13. A cross-account ID, preview, or mutation must not reveal or change another customer's data.
14. Selecting visit B while a slow preview for A completes must not repaint B's panel or offer A's issue token. An issue response after navigation cannot repaint the current view.
15. Re-run existing list, detail, note trim/no-op, tenant filtering, stable ordering, and note stale-write tests.

## Alternative defensible designs
For evidence, sorted immutable per-vendor histories, indexed keyed lists, or a cache keyed by vendor/category/time are fine if the semantics are correct and memory bounded. For capacity, a per-site interval list plus localized sweep is acceptable with documented production limitations; interval trees, segment trees with coordinate compression, or indexed endpoint counts enable stronger large-scale behavior. For preview intent, opaque server tokens, signed canonical snapshots validated against revisions, or a server-side review cache are defensible; each must provide replay safety and expiration. Optimistic locking or serialized commands within the existing process are valid. A full database or external queue is not needed in this 60-minute environment.

## Likely AI coding-agent failures
Common failures include adding endpoint stubs that trust a browser verdict, using the last line of JSONL as authority, confusing effective and recorded timestamps, lexical timestamp comparison, including the departure endpoint as occupied, counting only capacity at arrival, double-incrementing global revision, checking staleness before replay, marking a key used before a failed issuance, sleeping while holding a lock, and replacing current UI controls with stale asynchronous responses. One-shot solutions often pass supplied starter tests because those tests intentionally exercise only pre-existing behavior.

## Recommended 60-minute prioritization
Minutes 0–8: inspect readme, store, HTTP routes, UI and fixtures; name the invariants. Minutes 8–27: domain review, evidence precedence, occupancy and unit tests. Minutes 27–41: atomic issue/idempotency, HTTP errors and at least one conflict test. Minutes 41–53: browser review/issue/receipt and stale response handling. Minutes 53–60: full regression suite, manually probe boundaries, prepare complexity and failure walkthrough. A coherent tested vertical slice merits more credit than untested breadth.

## Walkthrough inspection points
Ask why `VIS-004` is denied despite clear capacity at arrival, why `VIS-010` can pass expiry validation, and what concurrent issuance of `VIS-001` and `VIS-002` does. Inspect event replay selection before effective ordering, token+key lifecycle, error response security, lock coverage, post-delay checks, revision accounting, frontend cancellation/identity guards, and whether original note edits/search still work. Ask how latency changes with 250k credential rows and 50k pre-issued passes, especially when one site is highly skewed.
