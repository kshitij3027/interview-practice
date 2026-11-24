# Interviewer notes — POST-PRACTICE ONLY

## Intended shape and tradeoffs
This is primarily a reporting-contract and consistency problem, not a request to add a new CRUD workflow. Keep the existing review endpoints and preserve their revision semantics. A credible implementation takes a site-scoped immutable snapshot of the relevant meter catalog, revision and readings under the existing mutex (or computes under the lock), then uses a shared report function for JSON and CSV. Avoid recursive locking when reusing Store methods. For CSV, validate the requested revision within the same snapshot boundary; do not check revision, release the lock and later read live mutable data. Snapshot copying costs memory but keeps lock duration bounded; a single synchronized computation is defensible at interview scale. Never hold the lock during network writes.

Group by meter and hour, retain the greatest source sequence (not array order, reading ID or review status), and compare distinct payloads at that sequence. A greater sequence supersedes all conflicts at lower sequences. Identical winning payloads collapse; disagreement including review status makes the endpoint a conflict. A rejected greatest sequence is not a reason to revert to older data. Determine endpoint validity before comparing epoch and cumulative values. For each requested hour read the two exact endpoints, checking earlier endpoint errors first. Epoch mismatch takes precedence over a decrease. Use an integer difference, and track known counts independently of sums so true zero remains distinguishable from all-unknown.

Expected complexity: O(R + M*H + M log M) time for R input observations, M selected meters and H hours, plus O(U + M*H) memory for U indexed observations/endpoints and the report. Sorting relevant rows once also works (O(R log R)); per-hour scans of all readings do not. A database query with snapshot semantics and suitable indices is another defensible design but unnecessary. Ruby integers preserve exactness; UI should not introduce rounding for ordinary fixture/production values. Discuss precision if values exceed JavaScript safe integer range.

## Concrete fixture oracle
For Harbor, start 2026-11-24T00:00:00Z and end 2026-11-24T04:00:00Z, no search:
- m1 hourly values 200, 50, null (replacement), 0; 3/4 known, 250 Wh.
- m2 hourly values null (rejected), null (rejected), null (missing), null (decrease); 0/4 known, usage null.
- m3 four missing hours; 0/4 known, usage null.
- Summary 3/12 known, 250 Wh (partial, 25% coverage).
- q=' LINE ' normalizes to 'line' and selects m1 only in Harbor; 3/4 known, 250 Wh. Ridge m4 is independent and its first hour is 8 Wh.
- CSV contains 12 data rows plus header; m1 name with comma must be quoted. Last m1 row has usage 0 and empty reason; unknown rows have empty usage and a reason.

## Hidden checks
1. Shuffle fixture order, add a conflicting lower-sequence sample, add a conflicting equal-winning-sequence sample, and add identical winning repeats. Lower conflicts must not influence the winner. Equal winners with different review/epoch/Wh invalidate both adjacent hours. Review one of r4/r5: same sequence now disagrees and the 01:00 endpoint is unusable.
2. Reject the only highest-sequence reading while an older accepted record remains; do not fall back. Verify both endpoints and precedence when an early rejected endpoint precedes a later missing endpoint.
3. Exercise zero, decreasing cumulative values, replacement even when the new register is higher, missing interior/endpoints, meter with no observations, no matching meters and a one-hour window. Do not bridge any gaps.
4. Reject reversed/equal windows, malformed calendar dates, non-hour UTC timestamps, non-Z offsets and >168 hours. Test exactly 168 hours and an observation at the exclusive report end (needed as a boundary).
5. Check cross-site search and unknown sites, stable ID/hour order, and CSV quoting for comma, quote and newline in meter names. Test missing, negative, decimal and nonnumeric revision parameters. JSON errors must not accidentally be emitted as a successful CSV.
6. Generate Harbor revision 3 report. Edit Ridge: Harbor export still succeeds. No-op Harbor review: still succeeds. Material Harbor edit: old export returns 409/current revision, never a CSV. Generate a new report; new CSV matches new result. Concurrent read/edit must yield a coherent old report or coherent new report, never mixed rows.
7. Browser: generate report, edit filter without generating, click export (must use reviewed parameters or disable until regenerated); simulate slow response followed by site/window change and verify old response is discarded. Simulate failed report/export, retry and stale export regeneration. Existing review editing must remain usable, including stale edit recovery.
8. Synthetic scale: many meters, many unrelated readings, sparse and duplicate-heavy data. Inspect that work is not proportional to R*M*H. Keep runtime and memory practical; do not impose a machine-specific hard latency threshold.

## Likely AI-agent failure modes
Filtering accepted readings before selecting revisions; summing cumulative counters; bridging missing endpoints; using truthiness to conflate zero and null; selecting a last-row winner; averaging per-meter coverage; dropping empty meters; generating CSV separately from unreviewed parameters; checking the revision outside the snapshot; serializing CSV by string joining; extending JSON-only browser helper without handling CSV errors; allowing stale async results to overwrite a newer selection.

## Recommended 60-minute prioritization
0–8 min: run starter, inspect fixture and existing Store/HTTP/browser state.
8–30 min: domain report and tests, strict time validation, scoped API.
30–45 min: UI report and coverage/reasons, reuse canonical result for CSV.
45–55 min: stale export and async recovery, test tricky fixture cases.
55–60 min: run tests/build and demonstrate one report, export, and a stale conflict. Partial but verified behavior beats many untested changes.

## Walkthrough inspection points
Ask the candidate to explain the fixture oracle, specifically why m1's first hour is 200 rather than 100, why m2 cannot use its older reading, and why 0 Wh is not missing. Inspect the snapshot lock boundary, report parameter normalization and export implementation. Ask what happens when one of two identical highest-sequence readings is reviewed differently, or a site changes while a CSV is being generated. Inspect whether browser response guards capture both selection and parameters, and whether old notes/review behavior continues to work. Discuss production-scale indexing and alternatives without requiring new infrastructure.
