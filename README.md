# PromiseClock — 60-minute AI-assisted systems interview

## Customer context
A B2B support platform promises response times measured only when the customer's regional support desk is open. Scheduled coverage windows sometimes overlap, and outages, regional closures, and customer-requested ticket pauses stop the SLA clock. Today, agents manually calculate deadlines and supervisors refresh overdue queues; the resulting answers disagree when calendars contain overlaps or when customers reopen old cases.

Implement an **exact, repeatable SLA clock** over one immutable operations snapshot. You choose the solution strategy. An LLM, deterministic implementation, or hybrid approach is permissible only if you can defend correctness, latency, cost, and failure behavior.

## Supplied data
- `fixtures/coverage.csv`: `coverage_id,region,starts_at,ends_at`. Each record marks an available support interval for one region. Windows can overlap; overlapping availability never counts twice.
- `fixtures/blackouts.csv`: `blackout_id,region,starts_at,ends_at`. Support is unavailable during a regional blackout even if coverage exists. Blackouts may overlap each other or extend outside all coverage.
- `fixtures/tickets.csv`: `ticket_id,region,opened_at,budget_minutes`. Each ticket belongs to one region and has a nonnegative whole-minute allowance.
- `fixtures/pauses.csv`: `pause_id,ticket_id,starts_at,ends_at`. A ticket does not consume its allowance while paused. Pauses may overlap, start before the ticket opens, or extend outside support coverage.
- `fixtures/queries.jsonl`: one independent JSON query per line; examples and schema below.

Every CSV ID is a nonempty case-sensitive ASCII letter/digit/underscore/hyphen string of length 1–40. Each record ID is unique, except identical repeated rows are harmless delivery replays. Conflicting reuse is a fatal snapshot error. Regions referenced by blackouts/tickets must have coverage, and pauses must reference known tickets. All intervals are **half-open** `[starts_at,ends_at)`, with strictly positive duration. Times are RFC3339 seconds with `Z` or an explicit `+HH:MM` / `-HH:MM` offset; normalize equivalent instants to UTC. Invalid snapshot rows fail the whole load.

## One primary customer request
For every ticket, its SLA clock starts at `opened_at` and advances **one second per actual second** that its regional desk is covered, is not blacked out, and the ticket is not paused. Otherwise it stands still. The budget is `budget_minutes * 60` seconds. The **deadline** is the earliest instant the accumulated eligible time reaches the budget. For a zero-minute ticket, the deadline equals `opened_at` even outside coverage. If the finite supplied calendar ends before the allowance can be exhausted, the deadline is `null`.

Implement `PromiseClock.resolve(request)` in `slaops/resolver.py` and supporting code/tests as you see fit.

Two supported request types:

- `{"request_id":"r1","type":"ticket","ticket_id":"K-100","as_of":"2026-10-19T12:00:00Z"}` returns `request_id,status:"resolved",ticket_id,as_of,deadline,elapsed_seconds,remaining_seconds,breached`. `as_of` and non-null deadline use canonical UTC `YYYY-MM-DDTHH:MM:SSZ`. `elapsed_seconds` counts all eligible time in `[opened_at,as_of)` (zero before opening, and allowed to exceed the budget). `remaining_seconds=max(0,budget_seconds-elapsed_seconds)`. `breached` is true exactly when `deadline` is non-null and `as_of >= deadline` (and false before opening).
- `{"request_id":"r2","type":"overdue","as_of":"2026-10-20T12:00:00Z","limit":5}` returns `request_id,status:"resolved",as_of,total_overdue,tickets`, where `tickets` contains at most `limit` objects with `ticket_id,deadline`. Include every ticket whose deadline is non-null and no later than `as_of`, even if its allowance is zero. Order by deadline ascending, then case-sensitive ticket ID ascending. `total_overdue` includes all qualifying tickets, not just returned tickets. Tickets with unreachable deadlines do not count.

## Observable acceptance criteria
Output one compact JSON object per query line, preserving input order and request ID (including repeated IDs); stdout must contain no diagnostics. `request_id` must be a nonempty string, `ticket_id` must name a known ticket, and `limit` must be an integer (not bool) from 1–50. An unknown ticket yields `status:"invalid",reason:"unknown_ticket"`. Malformed JSON, invalid timestamps, missing fields, invalid types, or unsupported request types yield `status:"invalid",reason:"invalid_query"`. Preserve a nonempty string request ID on an invalid query when available, otherwise use `null`. Continue after query-level failures.

Correctness must cover overlapping/adjacent windows, closures bisecting coverage, overlapping pauses, pauses outside support hours, fractional-minute opening times, equivalent timezone offsets, exact zero-allowance and deadline boundaries, unreachable deadlines, tie ordering, duplicated input rows, and queries far outside the fixture horizon. Results must be independent of row order, request ordering, and hash iteration.

## Production constraints
One immutable loaded snapshot can contain **2 million coverage windows**, **750,000 blackouts**, **500,000 tickets**, **1 million pause records**, and **2 million mixed queries**, with highly skewed region/ticket sizes. Target ~**1.5 GB RAM** and, after initialization, p95 below **20 ms for ticket lookups** and **35 ms for overdue top-50** on normal data. These are engineering targets: benchmark and explain where your runtime may miss them. Re-scanning every calendar, pause, or ticket for every query is not an acceptable production strategy. Do not expand a calendar minute-by-minute.

## Scope and expected deliverable
In scope: loading/validation, exact per-ticket deadlines and elapsed time, overdue summaries, malformed-query continuation, focused tests, and a complexity/tradeoff explanation. Out of scope: calendar recurrence/DST rule interpretation (intervals are already explicit), streaming mutations, ticket resolution/closure, authentication, network calls, databases, UI, and persistence between runs. Do not edit fixture inputs to satisfy tests.

## Setup and verification
Python 3.11+ standard library only:

```bash
bash scripts/test.sh
bash scripts/build.sh
bash scripts/verify.sh
python3 promise_clock.py check --coverage fixtures/coverage.csv --blackouts fixtures/blackouts.csv --tickets fixtures/tickets.csv --pauses fixtures/pauses.csv
```

After implementing the resolver:

```bash
python3 promise_clock.py assess --coverage fixtures/coverage.csv --blackouts fixtures/blackouts.csv --tickets fixtures/tickets.csv --pauses fixtures/pauses.csv --queries fixtures/queries.jsonl
```

The starter tests verify loading, input validation, and command wiring only. The requested clock computation is **not implemented** in this baseline.

## 60-minute AI-assisted interview instruction
You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or comparable AI tools. Inspect the data, identify the hard semantics, choose and implement a strategy, add adversarial checks, run verification, and explain correctness, complexity, and tradeoffs. Do not assume that a generated solution is correct merely because the provided small dataset runs.
