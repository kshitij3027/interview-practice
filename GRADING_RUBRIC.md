# POST-PRACTICE ONLY — ServiceClock grading rubric (100 points)

**Evaluate only after the 60-minute session.** The candidate-facing starter deliberately leaves the SLA workflow unimplemented. Score observed behavior, evidence, and justified tradeoffs, not framework preference or total lines generated.

| Category | Points | Evidence to seek |
|---|---:|---|
| Requirements decomposition and domain modeling | **12** | Discovers current note revision contract and historical feed; distinguishes business hours, pauses, resolution, as-of evaluation, deadline, account ownership, idempotency; prioritizes a vertical slice. |
| Historical event normalization and correctness | **15** | Validates event/time shape, quarantines conflicting event IDs, deduplicates exact redelivery, sorts by occurredAt and event ID, handles same instant and terminal resolution, never trusts receivedAt for chronology. |
| Business-calendar clock and deadline correctness | **22** | IANA timezone rules, site-specific weekdays/holidays, half-open day windows, exact integer minutes, multiple active/paused segments, actual deadline at exhaustion, remaining/overdue/state semantics, date boundaries and DST. |
| Transition backend and consistency | **17** | Legal transitions, server timestamps, per-job revision checks, immutable successful replay, key collision, transaction/lock around check+write, one activity and exactly one revision increment, isolation and structured errors. |
| Frontend functionality and integration | **12** | Selected-work-order SLA, controls, authoritative re-render, pending and failure feedback, account/selection race guard, safe retry retaining same key after uncertainty, conflict recovery, existing note/list behavior retained. |
| Edge cases and validation | **8** | Offset-aware minute-level timestamps, stale/unknown resources, invalid events isolated, wrong-account attempts, same-instant tie, on-budget threshold, waiting/resolved deadline nulls, bounded requests. |
| Focused testing and verification | **7** | Keeps baseline green; adds meaningful tests for calendar exceptions, redelivery/conflicts, transitions/idempotency/concurrency, API and UI integration; actually runs checks. |
| Scalability / complexity | **4** | Does not scan unrelated jobs or all events per query; calendar-day intersection rather than per-minute history scans, handles large gaps; complexity explanation includes indexing, cache invalidation. |
| Code quality / maintainability | **2** | Clear boundaries, readable error handling, minimal unnecessary dependencies and abstractions. |
| Walkthrough / AI-assisted reasoning | **1** | Can explain why choices work, AI contributions reviewed and known limitations. |
| **TOTAL** | **100** | |

## Calibration and ceilings

- **90–100:** Runs a correct full vertical slice, includes robust history/calendar/transition behavior, preserves baseline, verifies material tricky cases and explains performance.
- **75–89:** Solid vertical slice with a small number of missing edge cases, or robust domain/backend with a slightly unfinished UI.
- **60–74:** Meaningful integration with demonstrable gaps around history, concurrency, or deadlines. Do not award the top of this band to happy-path-only work.
- **Below 60:** Basic read-only badge or new state action only, partial plumbing, or reliance on optimistic client assumptions.
- **Hard cap at 60:** Naïve happy path with straightforward work-hours calculation, no robust idempotency, no conflict/replay handling, or missing pause/history logic, regardless of UI polish.
- **Hard cap at 55:** Scans every raw activity per job, iterates each minute over arbitrarily long periods, or assumes fixed UTC offsets despite the explicit production constraints; also cap at 55 if work-order changes can occur without revision checks.
- **Hard cap at 45:** Breaks current note editing or account isolation, or marks successful operations in the browser before server confirmation.

Award partial credit based on what can be shown or reasonably walked through during the allotted hour. Do not expect the candidate to solve all DST pathological time-zone configurations perfectly, but expect an explicit boundary policy and thoughtful verification.
