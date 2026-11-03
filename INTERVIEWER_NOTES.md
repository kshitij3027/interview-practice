# POST-PRACTICE ONLY — BatchGuard interviewer notes

**Do not open before completing the timed candidate exercise. This file contains solution guidance and private checks.**

## Intended underlying problem
This is not merely a CSV upload button: it is an incremental, replay-safe multi-entity state reconciliation problem. The source feeds unordered revisions and replayed delivery IDs. A valid solution needs different boundaries for global request-key integrity, row/sample validity and per-lot concurrency. Quality is derived from the authoritative sample set, not supplied by the instrument or computed by the browser.

## Strong approach
A practical implementation can parse `csvText` with Python's `csv.DictReader` over `io.StringIO(newline='')` with `utf-8-sig` support and a strict contract for field names. Represent exact values with `Decimal`, rejecting non-finite numbers explicitly. Canonicalize IDs and numeric values before comparison. First validate the envelope and the batch-wide limits. Then canonicalize rows, collect event IDs to detect both exact replay and contradictory duplicate IDs, and group rows by `(lot_id,sample_id)`. A group with any contradictory same-ID event or multiple different payloads at its maximum sample revision is rejected regardless of source order. Keep the newest valid revision per group. Store current samples indexed by `(lotId,sampleId)` instead of scanning all samples repeatedly.

Apply the intake under a single in-process lock. Check global idempotency before revision validation; a repeated successful request returns its *original* deep-copied receipt. Track an immutable request fingerprint over `{csvText,expectedRevisions}` using canonical JSON serialization; the request key itself is the lookup key. A collision with different contents is 409. For each referenced lot, check existence, status and revision, reject the lot without mutation on mismatch, and otherwise evaluate its groups independently. Apply all successful changes for that lot together, bump that lot's revision once if any sample changed, and bump the dataset revision once per changed lot. Derive quality from the resulting canonical sample set for each lot. Return sorted results and stable error codes. A valid no-op key must still create a durable receipt, or future replay can become inconsistent.

Keep `GET /api/lots` behavior stable (sort/search/total-before-limit) while enriching every lot with quality. `GET /api/lots/:id` should expose the same quality and current samples. A lightweight `quality_for_lot` can iterate only that lot's samples using a lot-to-samples index, rather than the global sample history. For very large production settings, cache/maintain per-lot aggregates and update them when samples are replaced; a 2,500-row demo request may tolerate an O(samples for changed lots) recompute but must avoid O(global samples × CSV rows).

Browser: maintain the exact text and a request key until a receipt is confirmed. Gather current revisions from authoritative lot list (or fetching detail per referenced lot), send the request, and display *all* outcomes including stale errors. Treat network failure as ambiguous: preserve key and contents for retry, not auto-resubmit with a fresh key. After a confirmed response, invalidate list and selected detail, guard async updates with monotonically increasing request tokens, and ensure note editing still functions.

## Expected complexity
Let `R` be CSV rows, `S` be total stored samples, `A` be accepted new/corrected samples and `L` be touched lots. Parsing/validation is O(R), grouping and deduplication average O(R) with dictionaries, and deterministic sorting O(R log R) in the conservative case (usually O(L log L + A log A)). State lookups are O(1) average per sample with indexes; recomputing only affected lots is O(sum of samples in touched lots), not O(R × S). Memory for a request is O(R + A) and for the state O(S + L). A database-based design with unique constraints/version checks is an acceptable production extension if the candidate can explain transaction and key semantics.

## Why naive approaches fail
- `split(',')` breaks quoted fields and BOM; decimal `float` can drift at moisture boundaries.
- The first or last row wins incorrectly when source revisions arrive out of order or equal-revision records disagree.
- Global rollback punishes valid independent samples and lots; per-row mutation without a per-lot revision check causes partial/stale writes.
- Comparing request key after mutation allows duplicate changes; omitting failed/no-op receipts makes an uncertain retry non-repeatable.
- Arrays scanned for every row scale quadratically; counting CSV rows rather than distinct persisted sample IDs inflates readiness.
- UI can display success for a prior file or lot if async responses are not checked against a local generation token.

## Hidden checks (run after practice, do not seed candidate tests)
1. CSV UTF-8 BOM + reordered headers + quoted text with commas; wrong/missing/extra headers (decide consistent strictness and explain).
2. Two byte-identical events with the same event ID; an event ID reused with differing payloads across *two lots*; both implicated samples must be rejected.
3. Versions 3,1,2 for a sample; one source v3 correction wins independent of row order. Two differing v3 rows reject, even when a v4 row exists? The stated contract rejects conflicts at greatest revision only; test v4 highest with conflicting lower v3 to ensure intentional behavior.
4. Stored revision 2, incoming revision 1 (no-op, never revert), matching revision 2 with equal normalized values (no-op), mismatching revision 2 (reject), incoming revision 3 (replace and recount).
5. Exactly pH lower/upper boundary and moisture cap after `fraction * 100` conversion. `Decimal('0.012') * 100` must equal exactly `1.2`. Very small positive values, scientific notation and non-finite values.
6. One report with valid open lot, stale lot, unknown lot, closed lot and two malformed samples: valid groups apply; no rejected lot mutates; per-lot counts/revisions correct.
7. Replayed key after an unrelated note edit returns the original receipt, not a newly generated receipt; same key different expected revisions or changed CSV returns 409.
8. Concurrent same-key submissions: exactly one application and two equivalent receipts (not two revision increments).
9. `GET` detail and `GET` list quality agree; seeded failing sample flips corrected state correctly. Closed lots still expose quality; they simply reject new import.
10. Request 2,501 rows or >256 KiB must reject pre-mutation; malformed CSV quoting and embedded newlines; boolean/noninteger request revision, case-sensitive identifiers, empty sample ID.
11. Browser lost response: preserve input and key; changing input invalidates old pending response; after success filter/search/note behavior still works and server remains authoritative.

## What to discover in the supplied fixture
`LOT-1001` has a seeded sample, allowing the minimum count to be reached with one more. An incoming 7.51 pH is just outside the resin-A upper bound. `LOT-1003` has a corrected `S-C2` sample whose latest pH exceeds the coating-C upper bound despite the earlier acceptable version. `LOT-1004` and `LOT-1009` are closed, so their rows cannot be ingested. `LOT-1005` includes both a valid fractional moisture row and a NaN reading. `EXP-010` is a byte-identical replay. `LOT-1007` has a quoted comma-containing moisture reading that is not a valid decimal. `LOT-1011` contains conflicting equal-revision results. `LOT-1012` has an unsupported moisture unit. Several lots already have non-default revisions, making stale handling testable.

## Alternative defensible designs
- A database approach using a request-key receipt table and unique `(lotId,sampleId)` keys, with per-lot version checks inside transactions, may be discussed but is outside the starter scope.
- A queue-based ingestion design is possible in production, but asynchronous receipts still require durable job IDs and exact replay semantics; a superficial queue does not solve correctness.
- Canonical hash keys rather than full serialized CSV payload are fine if collision risks and canonicalization are explained.
- `Decimal` or scaled integer percentages can be exact; binary floats are risky at the boundaries without formal handling.

## Likely AI-agent failures
Agents often scaffold an upload UI and send CSV rows to an endpoint without preserving the request key, pick last-in-file revisions, let one malformed number abort the whole request, or compute readiness from the current upload instead of the full stored sample set. Others will accidentally count identical retries as separate samples, use plain floats for thresholds, or omit clear per-lot diagnostics. Watch for an impressive-looking UI backed by unconstrained mutation.

## Suggested time allocation
0–8 minutes inspect existing flows and data; 8–18 define wire contract, samples and errors; 18–38 implement server-side normalization/reconciliation and quality; 38–48 integrate UI and retry; 48–57 add tests and verify; final 3 minutes explain choices and gaps. A working safe vertical slice with explicit uncovered cases is more valuable than a partially wired maximal design.

## Interviewer walkthrough inspection points
Ask candidate to trace a v1/v2 sample received in reverse order; to distinguish a duplicate event from conflicting equal revision; to explain whether an uncertain response can be retried safely; to walk through lot-versus-sample failure isolation; to show the sample indexes and complexity; and to prove a note edit racing import results in per-lot conflict without invalidating other lots. Inspect whether `pass` and `fail` can be recomputed identically from the stored record history and whether old UI responses can override newer inputs.
