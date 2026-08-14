# Signal Lab — HARD One-Hour Full-Stack Interview Exercise

## Context

Signal Lab is an internal experimentation-operations dashboard for a SaaS company. Product analysts use it to inspect experiment assignments, segment users, and exclude known test/internal accounts from analysis.

The starter application already works. It uses a dependency-free Node.js HTTP API, an in-memory domain store, a browser ES-module frontend with explicit client state, and existing tests for assignment/exclusion behavior. The repository also contains a noisy JSONL event fixture representing product telemetry from the experiment.

## Existing behavior

- The dashboard loads the `checkout-copy` experiment overview and assigned users.
- Users can be filtered by segment (`self-serve` or `enterprise`).
- An operator can exclude a user with a reason or include them again.
- Every exclusion/inclusion change increments the dataset `revision`.
- The overview reports assignment and raw-event counts by variant.
- Restarting the server resets exclusions.
- Existing tests cover fixture loading, overview behavior, revision changes, and exclusion API behavior.

## Customer/business problem

The experiment owner now needs an actual conversion funnel, not raw counts. The telemetry is realistic rather than clean: events can arrive out of order, duplicate event IDs exist, users can emit steps more than once, and some events belong to users who are not assigned to the experiment. Analysts also exclude internal/test users while dashboards are open, which means a slow report request can return after the underlying dataset revision has already changed.

The source telemetry is in `fixtures/experiment_events.jsonl`; experiment assignments are in `fixtures/assignments.json`.

## Primary feature request

**Add a segment-aware three-step funnel report (`product_viewed` → `checkout_started` → `order_completed`) with deterministic event semantics and race-safe client reconciliation when exclusions change while a report is in flight.**

## Acceptance criteria

1. Add a backend funnel-report API and corresponding UI for the fixed funnel `product_viewed` → `checkout_started` → `order_completed`, grouped by experiment variant.
2. The report must support segment filtering for `all`, `self-serve`, or `enterprise`. Excluded users are never eligible.
3. A user is eligible only for events occurring at or after that user's `assigned_at`. Events for users not assigned to `checkout-copy` must be ignored.
4. Duplicate telemetry is defined by `event_id`: only one occurrence of a repeated event ID may influence the report. Which duplicate occurrence wins must be deterministic and documented if their payloads ever differ.
5. Funnel progression is ordered per user by event time, not file order. A user reaches a later step only if a qualifying occurrence happens at or after the occurrence selected for the previous step. Repeated step events may be used if an earlier occurrence cannot form a valid ordered path.
6. The entire three-step path must complete within **24 hours of the user's first qualifying `product_viewed` step**. A completion outside that window must not count as step 3.
7. For each variant, return counts for eligible assigned users and users reaching each step. Also return step conversion percentages using the immediately preceding step as denominator; zero denominators must be represented safely rather than producing `NaN`/`Infinity`.
8. Results must be deterministic regardless of JSONL file order. Preserve integer counts; percentages must be rounded to one decimal place in a consistent way.
9. Every funnel response must include the dataset `revision` used to calculate it. The client must track the newest revision it knows from overview/users/exclusion responses.
10. The report request must support an optional local test delay (for example a bounded `delay_ms` query parameter) so stale-response behavior can be exercised without external infrastructure.
11. If an exclusion/inclusion changes the dataset while an older funnel request is in flight, the UI must not render that older response over newer state. It must either discard the stale response or immediately reconcile with a fresh report. A slow older request finishing last must never make the screen appear to include an excluded user.
12. Changing the segment while a report request is in flight must not let the previous segment's response overwrite the newly selected segment's report.
13. Excluding/including a user must keep the existing user table behavior working and must cause the visible funnel report to reconcile to the new dataset revision without a browser reload.
14. Report failures must leave the last known-good report visible (if one exists) and show an actionable error rather than clearing the entire analysis area.
15. Existing overview, user filtering, exclusion validation, and revision behavior must continue to work.

## Constraints

- Keep the current Node.js + browser ES-module stack and dependency-free setup.
- Keep state in memory; no database, queue, auth provider, analytics service, or external API.
- The backend is the source of truth for funnel semantics; do not compute the authoritative funnel only in the browser.
- You may add service/domain modules and tests as needed.
- Do not rewrite the app into a framework or replace the current exclusion workflow.

## Out of scope

- Configurable arbitrary funnels.
- Statistical significance/confidence intervals.
- Persistent storage across process restarts.
- Real streaming/websockets.
- Authentication/authorization.
- Visual charting libraries or polished data visualization.

## Setup / run

```bash
npm start
```

In a second terminal:

```bash
python -m http.server 5173 -d web
```

Open `http://localhost:5173`.

## Tests / build

```bash
npm test
npm run build
```

Existing tests cover current behavior only. Add feature-specific tests based on the requirements; there are intentionally no TODOs or starter tests that encode the funnel solution.

## 60-minute interview instruction

You have **60 minutes**. Treat this like a demanding AI-assisted product-engineering/FDE live build. First inspect the existing data model, state flow, and fixtures. Then choose a core path, implement incrementally, and verify semantics with focused tests plus an end-to-end browser pass.

A visually complete happy path that mishandles event ordering, duplicates, exclusions, 24-hour semantics, or stale async responses should not be considered a strong solution. Prioritize correctness, observable verification, and time management.

**Do not read `INTERVIEWER_NOTES.md` until after you finish.**
