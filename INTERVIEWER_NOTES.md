# POST-PRACTICE ONLY — GridPulse interviewer notes

Do not expose this file, its contents, or evaluator-specific checks to the candidate before the hour ends.

## Intended underlying problem structure

This is a static, revisioned interval-addition workload with arbitrary range queries for both **maximum point value (and leftmost argmax)** and **integrated sum**. After selecting each session's highest revision, each active upsert is a half-open weighted interval on one site's timeline. The query workload rewards reusable per-site time indexes, not a loop over all active sessions on every request.

A strong exact design:

1. Validate every CSV record, deduplicate identical `(session_id,revision)` rows, reject conflicts, then choose the highest numeric revision for each logical session. Ignore a winning `cancel` and include a winning `upsert` at its latest site.
2. For each site, emit `(start_ms,+kw)` and `(end_ms,-kw)` boundaries, coalesce all deltas at equal timestamps, and sort. When sweeping, apply delta at the boundary before considering the interval extending rightward. The resulting demand is constant on every interval between adjacent boundaries. Zero-draw sessions change neither load nor area; they need not allocate structural nodes.
3. Build a prefix integral in integer `kw*ms` across the compressed segments. For any timestamp `t`, evaluate the accumulated area to `t` by binary searching the segment and adding the partially traversed segment's demand times duration. `energy_kw_ms = area(until_ms)-area(from_ms)`.
4. Build a range-maximum index over the compressed interval loads with leftmost-index tie-breaking (e.g. segment tree or sparse table). For `[a,b)`, consider the active value at `a`, plus every piece that starts strictly after `a` and before `b`. Query the indexed range for the maximum and leftmost segment boundary. If both paths have equal maxima, `a` wins. Handle intervals with no boundaries, and queries wholly outside catalog bounds, using zero load, earliest time `a`.

With `N` winning sessions, sorting takes `O(N log N)` globally (per-site sum) and linear storage for compressed boundaries, area prefixes and range-max nodes. Each query is `O(log N_site)` using binary searches and a segment tree, or `O(1)` range max after a sparse-table setup with `O(N log N)` memory; the time integral needs boundary lookup `O(log N_site)`. A full-segment scan per query is not acceptable. Memory and time must be discussed for 300,000 queries and severe site skew.

## Why common shortcuts fail

- Scanning each session for every query is `O(NQ)` (up to 120 billion checks) and sorting events inside each query is worse.
- Reporting maximum only at explicit start events misses a peak already active at `from_ms` and idle intervals with no events.
- Adding all start events before subtracting end events at the same timestamp fabricates an instantaneous peak in half-open time; all deltas at a timestamp must be treated together.
- Last row wins is wrong: revision numeric order, not file order, determines the live session. Repeated identical rows must not amplify demand; cancellation is absolute.
- Binary floating-point and kWh conversion violate exact integer area, especially over 10^12-ms windows.
- Computing peak from a global site maximum is wrong for small windows. Integration from whole-session lengths misses partial clipping.
- Handling zero-demand intervals only between active events misses long idle prefixes/suffixes and empty sites.

## Hidden checks and subtle traps

1. Reordered session revisions, nonconsecutive revision numbers, identical replay, highest revision cancellation, cancel-only session, and correction that moves a session to a different site. Validate even superseded rows.
2. Two equal-duration sessions with starts/ends swapped at exactly the same millisecond; compare `[t-1,t)` to `[t,t+1)` and prevent boundary-only spikes.
3. Query `[205,210)` whose peak has been constant since 200: earliest peak must be 205. If the maximum occurs again later, the earliest wins.
4. Query window before all starts, after all ends, entirely within an idle gap, and empty site. Peak is zero with `peak_at_ms` exactly the request's `from_ms`.
5. Two equal peak plateaus separated by lower demand; earlier plateau wins. Compare with simultaneous max load at `from_ms`.
6. Overlapping sessions of zero and large draw, duplicated identical intervals with distinct session IDs, and accumulated energy greater than 64-bit signed integer limits (Python integers are exact).
7. Session with `end_ms=10^12`, query ending at `10^12`, nonzero `from_ms`, and a query of width 1 ms.
8. Shuffle CSV rows repeatedly, duplicate request IDs, booleans disguised as integer timestamps, `from_ms==until_ms`, malformed JSON line between two valid requests, and catalog-wide conflict failure before any output.
9. A site with 400,000 concentrated sessions and many short random query windows: look for `O(N)` per request, accidental generation of all integer milliseconds, and excessive per-session object churn.

## Alternative defensible approaches

- A single range-max segment tree plus an integral prefix is straightforward and precise. A sparse table provides faster queries at extra memory. Binary-searchable arrays of boundary coordinates and segment loads are often sufficient.
- An augmented balanced interval structure may support point demand and range queries but is harder to implement safely in one hour; give full credit if exact with well-defended bounds.
- A deliberately narrowed implementation using a correct sweep and binary searches can be worthwhile if the candidate states and demonstrates the unimplemented indexing upgrade, but scale points should reflect the actual code.
- Approximate or LLM-based methods cannot earn exactness points without proving the requested integer semantics and deterministic tie-breaking. LLMs can help build tests or reason about tricky inputs, but are not required.

## What should be discovered from the data

The fixture deliberately includes out-of-order corrections (S-01, S-08), cancel-after-upsert and cancel-only sessions (S-09, S-13, S-22), an explicit site move (S-16), an identical replay (S-17), zero-draw records (S-06, S-25), simultaneous start/end moments (S-02/S-03 and S-04/S-10), equal-demand plateaus, an empty site, a session covering almost the full time domain (S-21), and a high-draw record far from ordinary ranges (S-23). The JSONL file includes invalid interval, malformed JSON, unknown site, and JSON boolean timestamp cases.

## Likely AI-agent failure modes

An agent may implement direct per-query scans and claim scalability; return a numeric peak but the wrong earliest timestamp; mishandle the `end_ms` boundary; make the query parser permissive with bools or floats; only process last physical row rather than max revision; use one global timeline and leak demand between sites; replace parser validation with silently dropped records; mistake `energy_kw_ms` for energy in kWh; or rewrite the baseline tests instead of adding correctness assertions. Watch for confident claims unsupported by actual verification.

## Suggested 60-minute prioritization

- 0–8 min: inspect schema, explain winning revision and output semantics, establish baseline.
- 8–20 min: calculate winning sessions, group by site, produce coalesced timeline with correct half-open semantics.
- 20–38 min: implement point/area lookup and window peak with deterministic earliest time.
- 38–50 min: add reusable range-max indexing and test skewed/boundary windows.
- 50–60 min: adversarial tests, run full checks, justify complexity and remaining risks.

## Walkthrough inspection points

Ask for the mathematical invariant of a segment and the area-prefix definition; trace `[200,300)` at EAST-DEPOT; show a simultaneous end/start boundary; explain finding peak when `from_ms` lies inside a long interval; show how a superseded session is removed when it moves sites; then analyze memory and p95 when one site owns almost all intervals. Finally ask what correctness tests the candidate wrote that an AI-generated one-shot implementation missed.
