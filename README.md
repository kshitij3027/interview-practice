# PaceDesk — HARD One-Hour Full-Stack Interview Exercise

## Context

PaceDesk is an internal campaign-operations console for a digital advertising platform. Account managers use it to inspect live campaigns, filter by operational status, and pause or resume a campaign when delivery needs intervention.

The starter application already works. It uses a Python 3 standard-library HTTP API, an in-memory fixture-backed domain store, a dependency-free browser ES-module frontend with explicit client state, and existing tests for the current campaign status workflow.

## Existing behavior

- The dashboard lists campaigns ordered by account name, then campaign ID.
- Operators can filter campaigns by `active` or `paused` status.
- Selecting a campaign shows its timezone, current daily budget, revision, and recent budget-change history.
- Operators can pause or resume one campaign.
- Status writes require the campaign revision observed by the client. Stale writes fail without mutation.
- A successful status change increments the campaign revision and global dataset revision exactly once.
- Restarting the backend resets state from the checked-in fixtures.

## Customer/business problem

Campaign managers currently have no trustworthy pacing view. Finance exports spend telemetry as append-only JSONL, while budget changes are maintained separately. The spend feed is realistic rather than clean: rows are not ordered by event time, exact duplicate event IDs can appear, later correction rows can replace earlier spend events, refunds reduce spend, and records may arrive after the period they describe.

The team wants a report that answers: **for a selected campaign and reporting window, how much valid spend has actually accrued by a chosen cutoff, how much budget should have been consumed by that point, and is the campaign under-, on-, or over-pacing?** The answer must be stable regardless of fixture row order and must remain correct when users rapidly change report inputs while slow requests are still in flight.

Representative data is in `fixtures/spend_events.jsonl` and `fixtures/budget_changes.csv`.

## Primary feature request

**Add a server-authoritative campaign pacing report that deterministically reconciles noisy spend events with effective-dated budget changes and renders the latest requested report without stale responses overwriting newer UI state.**

## Acceptance criteria

1. Add report controls for the selected campaign: reporting `start` date, `end` date, and an `as_of` timestamp. Dates are interpreted in the campaign's IANA timezone. The reporting interval is local-date based: `start` is inclusive at local midnight and `end` is exclusive at local midnight after that date range boundary as described by the UI.
2. The browser must not calculate authoritative spend or pacing from raw fixture rows. Add a backend report API that reads the server-owned spend and budget fixtures/state.
3. Spend events belong to one campaign and have `event_id`, `occurred_at`, `ingested_at`, `kind`, `amount_cents`, and optional `replaces_event_id`. `charge` adds spend and `refund` subtracts spend; fixture amounts are non-negative integers.
4. Exact duplicate rows with the same `event_id` and materially identical payload count once. If the same `event_id` appears with different payload data, choose one deterministically using the greatest `ingested_at`; if those timestamps tie, choose the lexicographically greatest canonical serialized payload. Report how many duplicate/conflicting rows were collapsed.
5. A row with `replaces_event_id` supersedes that earlier logical event for the same campaign. Replacement chains are possible. Only the terminal surviving event in a valid chain contributes spend. A replacement that points to an unknown event is reported as an orphan correction and contributes nothing. A correction cycle is invalid and every event in that cycle contributes nothing.
6. Event inclusion is based on the surviving event's `occurred_at`, not JSONL row position or `ingested_at`. Include only surviving events whose occurrence is inside the requested reporting interval **and** whose `ingested_at` is less than or equal to `as_of`.
7. A correction is only allowed to replace an event from the same campaign. Cross-campaign replacement references are invalid, reported, and must not suppress either campaign's otherwise valid event.
8. Budget changes have `campaign_id`, `effective_at`, and `daily_budget_cents`. For each local calendar day in the report interval, the day's budget is the latest change effective at or before that day's local midnight. A campaign's initial `daily_budget_cents` acts as the fallback before its first budget-change row.
9. Budget changes exactly at local midnight apply to that new local day. A change later during a local day does **not** retroactively alter that day's pacing budget; it begins affecting the next local day unless another later change wins before that next midnight.
10. Compute `expected_spend_cents` through `as_of` by summing each report day's pacing budget multiplied by the fraction of that local day elapsed inside the report window by the cutoff. Respect real local-day duration from timezone rules rather than assuming every local day is exactly 24 hours.
11. Clamp the effective cutoff to the reporting interval: an `as_of` before the interval yields zero elapsed expected spend and zero included spend; an `as_of` after the interval behaves as the interval end.
12. Return at least: actual spend cents, expected spend cents rounded to the nearest cent in a documented deterministic manner, total full-period budget cents, pace percentage, pace classification, contributing event count, collapsed duplicate count, invalid/orphan correction count, and the campaign/dataset revision observed by the report.
13. Pace classification uses the ratio `actual / expected`: `under` below 0.90, `on_track` from 0.90 through 1.10 inclusive, and `over` above 1.10. If expected spend is zero, return a safe explicit representation instead of `NaN`/`Infinity`; actual zero with expected zero is `on_track`, while positive actual with expected zero is `over`.
14. Report output must be deterministic when the order of spend-event rows or budget-change rows is shuffled.
15. Reject malformed report inputs clearly: invalid timestamps/dates, `end` not after `start`, unknown campaign, or an impractically large range over **92 local days**. A bad report request must not affect campaign state.
16. The report endpoint must accept an optional bounded `delay_ms` query parameter so out-of-order response behavior can be reproduced locally without external services.
17. If the user changes campaign or any report input while a report request is in flight, a slower older response must never overwrite the newer requested report. The UI may discard obsolete responses or reconcile them explicitly, but rendered controls and report data must always correspond.
18. A transient report failure must leave the last known-good report visible when one exists and show an actionable error instead of clearing the campaign workspace.
19. Pausing/resuming a campaign through the existing workflow must continue to work while report controls are present. Preserve the current campaign-status filter, selection, and report inputs after a successful status mutation when still applicable.
20. Existing campaign ordering/filtering, detail rendering, status validation, optimistic concurrency, and revision behavior must continue to pass unchanged.

## Constraints

- Keep the Python standard-library backend and browser ES-module frontend; do not introduce a framework or external service.
- Keep mutable application state in one process and in memory. Spend and budget fixture data may remain read-only after startup.
- The backend is authoritative for event reconciliation, timezone handling, budget semantics, derived metrics, and revisions.
- You may add modules, routes, client state/actions, DOM rendering, and focused tests.
- Use integer cents for stored monetary values. Do not make floating-point accumulation the source of nondeterministic cents.

## Out of scope

- Editing spend events or budget-change fixtures from the UI.
- Currency conversion, taxes, fees, attribution modeling, or forecasting future spend.
- Authentication/authorization.
- Persistence across server restarts.
- Multi-process locking, queues, websockets, or polling.
- Charting libraries or visual polish beyond a clear usable report.

## Setup / run

```bash
./scripts/run.sh
```

Open `http://localhost:8080`.

## Tests / build

```bash
./scripts/test.sh
./scripts/build.sh
```

Existing tests cover the current campaign workflow and fixture loading only. Add focused feature tests around the report semantics you consider highest risk.

## 60-minute interview instruction

You have **60 minutes**. Treat this as an AI-assisted live product-engineering interview. Inspect the campaign store, status mutation boundary, timezone-bearing fixtures, spend feed, budget history, API routing, and frontend state before making changes. Choose a correctness-first slice, implement incrementally, and verify ordinary plus slow/out-of-order report behavior.

A polished report that depends on fixture row order, double-counts corrected spend, mishandles local-day boundaries, returns unsafe zero-denominator values, or lets an old response repaint newer inputs should score poorly. Prioritize observable correctness and the most dangerous semantics over cosmetic completeness.
