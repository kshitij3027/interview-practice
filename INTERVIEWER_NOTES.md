# POST-PRACTICE ONLY — WaveSend interviewer notes

**Evaluator reference for post-practice review.**

## Intended underlying structure
The problem is an incremental, point-in-time data-reconciliation and bulk side-effect workflow, not a text-generation task. Use per-event-ID deduplication, chronological consent registers by contact/scope, a canonical-phone grouping index, a rolling-window per-phone history index, and a server-owned preview token. Then enforce an idempotent dispatch transaction with partial provider outcomes and version checking. AI can help scaffold routes and UI, but eligibility must be reproducible and explainable.

## Strong implementation approach
1. Parse fixtures once; reject or quarantine malformed event rows with structured diagnostics. Index contacts by ID, segment and normalized phone. Do not throw away invalid-phone contacts silently in explanations.
2. Deduplicate consent eventId: if event ID appears with multiple contact IDs, quarantine that ID for all implicated contacts (conservative suppression is reasonable); otherwise select newest receivedAt, tie by canonical stable JSON serialization with sorted keys. Validate explicit time zones, event kind and source. Build effective events indexed by `(contactId, scope)` and sort by `(effectiveAt, source priority, receivedAt, eventId)`; binary-search as-of time for repeated previews. Tie on eventId is **ascending** for the final choice (if all preceding fields equal), while payload canonical tie for a repeated ID picks lexicographically **greater**.
3. For a contact default global is not suppressed, default SMS is NOT opted in. Global opt-in does not change SMS; SMS opt-in does not change global. Contacts with invalid/conflicting evidence should be conservatively excluded, not treated as opted in by a malformed replay.
4. For a campaign, identify active in-segment candidates and group by canonical phone. For each phone consult *all* cross-segment/archived identities on it for effective opt-outs. Require an effective SMS opt-in for the chosen representative (or for a positive contact with deterministic representative selection, according to README). The conservative design can choose the lowest active/in-segment consented contact; make that interpretation explicit and consistent. Block the phone if **any** matched identity is opted out; it is incorrect to select a clean duplicate and ignore a suppressed duplicate.
5. Use history indexed by canonical phone with sorted timestamps. Count queued/delivered sends in `(t-24h,t]`, excluding failed. Add sends atomically with dispatch; update indexes on accepted provider outcomes. At exact lower boundary, history is excluded. Report transparent counts/reasons for blocked groups and contacts.
6. Preview material stores campaign ID/revision, dataset revision, instant, maxRecipients, ordered selected contact/phone pairs, explanations and createdAt. Preview creates no send/history/revision mutations. Server should discard/expire old previews. Dispatch first checks completed request-key outcomes: same canonical request arguments replay immutable receipt, different payload conflicts. For a new dispatch validate campaign ownership, current revisions and preview age, then attempt each recipient once; accepted queues a record, transient/rejected remain unsent. Bump campaign/data revision once if any success; note/contact revisions unchanged.
7. UI must persist draft inputs across errors, bind receipt to selected campaign, ignore late responses from an older request/selection (epoch or AbortController + epoch) and refresh the current canonical state after a commit. Test with `delayMs` to simulate races.

## Complexity
Let C = contacts, E = events, H = history, S = candidate contacts in requested segment, G = selected phone groups, R = dispatch recipients. Startup O(C + E log E + H log H), memory O(C+E+H). With indexed per-contact consent registers and per-phone history: a preview is approximately O(S log E + G log H + G log G) worst-case rather than O(S(E+H)). Repeated query optimization can cache group summaries at stable revision/time intervals; never cache across mutation without invalidation. Dispatch O(R) provider attempts and O(R log H) history updates or amortized O(R) append in a monotonic time index.

## Subtle traps and hidden checks
- The same physical number appears under `c-101` and `c-107`; `c-107` opted out. Sending to `c-101` violates the group veto despite its own opt-in.
- `c-103` has a global opt-out followed by an SMS opt-in. Still blocked.
- `c-112` opts in at the same effective instant after an earlier opt-out: verify event source priority governs ties before receivedAt, not merely arrival order; a test with legal vs self_service on the same instant should preserve legal priority.
- `c-102` opts in after an opt-out and simulates `transient`. It must not block `c-112`'s accepted queue.
- `c-105` has two quota-consuming events in the rolling interval; events exactly at `at-24h` are excluded; failed history does not count.
- `c-108` has an invalid phone. No crash or invalid outbound destination.
- Duplicate `ev-007` differs in receivedAt. It is one logical event, never two. Add a collision with same event ID/different contact IDs and verify conservative behavior.
- An SMS opt-in alone must not clear a prior global opt-out. A global opt-in alone must not authorize SMS.
- Preview at ISO `-07:00` equals the equivalent `Z` instant. Parsing naive datetimes as local machine time is wrong.
- Cross-campaign history counts; accepted results must appear in the next preview. A `rejected` or `transient` outcome must not consume frequency quota.
- Preview must not write, dispatch must not trust client-supplied numbers. Reused keys with modified preview or expectedRevision must 409, but *exact* retries after revision changes must return the original receipt first.
- A no-accept batch does not bump revisions; partial successes bump once, not once per recipient. Concurrent note changes invalidate an old dataset preview; error must not send.
- Switch campaigns while a delayed preview is pending, or trigger a second preview with shorter delay: old response must not replace new view. Same concern for delayed dispatch outcomes.
- Search/note edits must continue to pass starter tests; HTML escaping must prevent content injection from names/notes.

## Alternative defensible designs
A compact event-sourced reducer per phone is acceptable if indexed and semantics are exact. Precomputing as-of intervals per consent scope is strong for repeated previews. A DB solution with unique keys/versioned writes could be discussed, but external infrastructure is intentionally unnecessary. Rejecting whole previews when any ambiguous evidence appears is safe but loses useful recipients; per-group quarantine is better. Strict transactional serialization can be a simple in-process request lock because the starter is a single-process server. LLM-only consent interpretation without deterministic adjudication is unlikely to satisfy reproducibility or reliability requirements.

## Likely AI-agent failure modes
A generated implementation may sum every history row (including failed), use >= on the 24-hour lower boundary, take the last JSONL consent event, ignore record-level conflict, treat same phone twice, clear global opt-out after SMS opt-in, trust browser-generated recipients, bump revisions for no-op/failures, dedupe requestKey after rather than before stale checks, hold on to a stale preview, or fail to protect delayed browser responses. Test adversarially rather than trusting generated happy-path tests.

## Suggested 60-minute prioritization
0–8 min inspect starter and fixtures; 8–22 min phone/consent/history domain with tight tests; 22–37 min preview + dispatch + idempotency/revision; 37–49 min browser flow; 49–57 min boundary/race checks and regressions; 57–60 min prepare walkthrough and known limitations. For a candidate under time pressure, a correct backend and primitive UI beat a sophisticated UI with unsafe dispatch.

## Walkthrough inspection points
Ask which consent evidence currently blocks `c-101`, why `c-103` is excluded, which events count toward `c-105`'s cap at 15:00Z, what happens to `c-102` and `c-112` on dispatch, how a lost-response retry behaves after a revision increment, how notes invalidate previews, how many indexes are scanned per preview at 200k contacts, and how one would adapt this single-process in-memory model for multiple servers or a real provider. Have the candidate demonstrate delayed requests and state preservation on errors. Inspect modified code for unsupported assumptions, unexplained AI output and omissions.
