# POST-PRACTICE ONLY — Interviewer Notes

## Intended solution outline
A strong solution separates the problem into two deterministic server-side transformations and a race-safe client flow. First, canonicalize spend rows by event ID before evaluating correction relationships. Then resolve replacement relationships per campaign so only valid terminal logical events can contribute. Independently, build the report's local-day boundaries in the campaign timezone and select the budget effective at each day's local midnight. Compute actual and expected spend against the same clamped reporting interval, return revision/diagnostic metadata, and keep the browser responsible only for request orchestration/rendering.

Expected-spend arithmetic should avoid repeated binary-floating accumulation for cents. Reasonable approaches include rational/integer duration arithmetic with one documented final rounding step, or decimal arithmetic implemented carefully with the standard library.

On the client, bind each report request to the selected campaign plus normalized inputs (or a monotonically increasing request token). A response may update rendered report state only if it still corresponds to the latest requested context. Preserve the previous successful report through transient failures.

## Subtle traps / hidden checks
- Conflicting duplicate IDs must resolve by greatest `ingested_at`, then deterministic canonical-payload tie-break; input row order must not leak into the result.
- Canonicalization happens before replacement-graph evaluation.
- A correction chain contributes only its surviving terminal event; replaced ancestors must not also count.
- Unknown replacement targets are orphan corrections and do not contribute.
- Replacement cycles invalidate the cycle members rather than hanging traversal.
- Cross-campaign replacement references do not suppress the legitimate target in the other campaign.
- `occurred_at` determines report-window membership, but `ingested_at <= as_of` determines whether the row was known by the cutoff.
- Refund amounts subtract even though stored fixture amount is positive.
- Budget selection is evaluated at each campaign-local midnight. A budget change at 14:00 local does not change that local day's pacing budget.
- A change exactly at local midnight does apply to that day.
- Test at least one DST transition: local day duration may be 23 or 25 hours.
- `as_of` must be clamped to the interval before expected-spend duration is calculated.
- Zero expected spend must never emit `NaN` or infinity.
- Shuffling either fixture must preserve report output.
- A delayed older report response after changing campaign or date inputs must not repaint the new context.
- Existing stale status-write handling must remain intact.

## Likely failure modes
- Summing raw JSONL rows directly.
- Deduplicating by first-seen row.
- Treating `ingested_at` as spend time.
- Handling only one-level replacements and double-counting longer chains.
- Accidentally suppressing an event due to a cross-campaign correction.
- Assuming every day has 86,400 seconds.
- Applying a mid-day budget amendment immediately to the day's full budget.
- Building local midnights by adding 24 hours in UTC.
- Using browser timezone instead of campaign timezone.
- Accumulating expected cents with binary floats and inconsistent rounding.
- Clearing the previous report on a transient failure.
- Using only a loading boolean without guarding against out-of-order completion.

## Expected prioritization
1. Understand fixture fields, existing mutation/revision behavior, and candidate-facing semantics.
2. Implement/report-test deterministic spend canonicalization and correction handling.
3. Implement timezone-local report bounds and effective daily budget selection.
4. Produce a minimal report endpoint and validate the core metrics.
5. Add frontend controls/rendering with stale-response suppression and last-good preservation.
6. Exercise delayed-response behavior and add focused edge-case tests.

## What an interviewer should inspect after the hour
- Whether the candidate identified canonicalization and replacement relationships as distinct concerns.
- Whether timezone boundaries are represented by actual instants rather than fixed 24-hour arithmetic.
- Whether cents/rounding semantics are deliberate and explainable.
- Whether diagnostics expose enough information to debug excluded rows.
- Whether the frontend report is tied to request context rather than whichever promise resolves last.
- Whether existing pause/resume concurrency tests still pass.
- Whether tests target semantic boundaries instead of only the checked-in happy path.

## Alternative defensible designs
A candidate may use iterative chain resolution, memoized DFS-like resolution, or precomputed reverse relationships as long as cycles/orphans/cross-campaign edges are handled correctly and complexity is reasonable for repeated reports. They may pre-index events and budget changes at startup or process the small fixture per request, provided they can explain how they would scale production volumes without changing semantics.
