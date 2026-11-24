# MeterDesk — HARD 60-minute full-stack interview

## Context
A facilities company monitors electricity consumption from cumulative meter readings across buildings. A utility analyst uses MeterDesk to review observations before reporting consumption to customers.

## Existing behavior
Ruby 3.2+ / WEBrick JSON API with a browser JavaScript console and fixture-backed in-memory state. Choose a site, search meters, inspect their readings and toggle a reading's review status. Review changes require the current site revision; unchanged reviews preserve it. Another site's resources return 404. State resets on restart. Preserve these behaviors.

## Customer problem
The analyst needs a trustworthy hourly usage report for a site. Telemetry can arrive twice, be corrected, be rejected by a reviewer, or span a meter replacement. Missing data must not be interpreted as zero consumption. Customers also need a CSV matching exactly what the analyst reviewed, even when someone changes an observation before export.

## Primary feature request
Build one end-to-end hourly consumption report and export workflow: choose a UTC reporting window and optional meter search, inspect per-meter and site usage/coverage, then export exactly the reviewed report with stale-state protection.

## Supplied data
`fixtures/sites.json` defines sites, meters and observations. A reading has `id`, `meter`, `at` (UTC hourly timestamp), `seq` (positive source correction sequence), `epoch` (physical meter installation identifier), `wh` (nonnegative integer cumulative watt-hours), and `review` (`accepted` or `rejected`). Array order is not meaningful. Reading IDs are unique; repeated samples can share a meter, timestamp and sequence. The fixtures deliberately contain overlaps, corrections, replacements and gaps.

## Acceptance criteria
1. Add `GET /api/report?site=...&start=...&end=...&q=...`. Start/end are exact UTC hour strings `YYYY-MM-DDTHH:00:00Z`, with start < end and at most 168 hours. Invalid windows return JSON 400. Site scoping matches existing endpoints. Filter meters by the existing case-insensitive name/ID search; blank includes all. Report all matching meters, even with no data, sorted by ID.
2. Each hour is `[t,t+1h)`. A reading at end is required for the last hour. At each endpoint use the greatest sequence among ALL readings for that meter and instant. At that sequence, identical `(epoch,wh,review)` payloads collapse; differing payloads make the endpoint unusable. A rejected winner is unusable; do not fall back to an older accepted reading. Ignore array order and never borrow from another meter or site.
3. An hour is `known` only when both endpoints are usable, have equal epoch, and end Wh >= start Wh. Its usage is the integer difference (including genuine zero). Otherwise usage is null and reason is exactly `missing`, `conflict`, `rejected`, `replacement`, or `decrease`: evaluate endpoints in chronological order, and at each endpoint missing/conflict/rejected in that order; check replacement before decrease after both endpoints are usable. Do not bridge gaps or estimate across replacements. Known hours have reason null.
4. Return `{site,revision,start,end,q,meters,summary}` with normalized q (trimmed/lowercase). Each meter is `{id,name,hours,knownHours,expectedHours,usageWh}`; each hour is `{at,usageWh,reason}`. `usageWh` is null when no hour is known, else sum of known hours. Summary has `{knownHours,expectedHours,usageWh}` across all selected meter-hours, using the same null rule. Coverage is known/expected, not the average of per-meter percentages; an empty selection has 0/0 coverage, shown as N/A. Do not label partial totals as complete consumption.
5. Add `GET /api/report.csv` with the same query parameters and required `revision` (nonnegative integer). Export only if that revision matches the current site revision; otherwise return JSON 409 and current revision, without a CSV. The read and revision check must use a consistent snapshot. A different site's edit does not invalidate the report; a material review change at this site does. CSV uses header `meter_id,meter_name,hour_utc,usage_wh,reason` and one row per meter-hour in meter-ID then hour order; unknown usage is empty, zero is `0`. Use proper CSV quoting. Export must match the reviewed report, not current unsaved browser filters.
6. Browser: provide window inputs and a report search, render coverage, known usage and reason per hour (or clearly inspectable per-meter breakdown), and download the reviewed CSV. Show pending and useful errors. If export is stale, keep the user's window/search and offer regeneration; do not silently export a newer report. Late report responses after changing site or report inputs must not replace the current view. A failed request should be retryable; after review changes the user must be able to refresh without reloading the page.
7. Preserve existing meter search, detail and revision-checked review editing. Tests should cover both data semantics and API integration, including a stale export after an edit.

## Constraints
No external service, auth or database required. Up to 500 meters/site, 168 hourly buckets, 200,000 source observations; keep a report practical on a laptop, avoid scanning the full feed for every hour. Ruby integers are exact. Site revision is intentionally conservative. CSV is intended for trusted analyst tooling; formula sanitization is out of scope.

## Out of scope
Time zones other than UTC, pricing, interpolation, dashboard charts, ingesting new files, persistent storage, authentication and visual polish.

## Setup / run / test
Requires Ruby 3.2+, WEBrick and Minitest (install if absent: `gem install webrick minitest`), and Node 20+ for JS syntax checks. No package install otherwise.

```sh
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
ruby server.rb
```
Open http://127.0.0.1:8080. Two browser tabs can simulate competing reviewers.

## 60-minute interview
AI assistance is allowed. Inspect the data and current app first; implement and verify incrementally. Aim for a credible vertical slice with correct domain semantics, then cover failure cases. Add tests and be prepared to explain tradeoffs, what you verified, and what remains incomplete. Do not replace the working application with a standalone script.
