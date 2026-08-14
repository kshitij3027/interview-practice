# POST-PRACTICE ONLY — Interviewer Notes

**Do not read this file before completing the 60-minute exercise.**

## Intended solution outline

A strong solution usually centralizes funnel calculation on the server rather than scattering semantics through the route. It obtains one consistent snapshot of assignments, exclusions, events, and revision; normalizes/deduplicates events deterministically; groups relevant events per eligible user; sorts per-user events chronologically with a deterministic tie-break; walks the fixed funnel while respecting assignment time and the 24-hour window; aggregates per variant; and returns the snapshot revision.

The client should treat report requests as versioned asynchronous work. A request identity/generation plus requested segment and returned dataset revision is usually sufficient to prevent older completions from overwriting newer state. Exclusion/include should advance known revision and trigger or require report reconciliation.

## Subtle traps / hidden checks

- `e-09` is duplicated in the fixture and must not count twice.
- File order is not chronological for all users; correctness must survive shuffled input.
- `u-103` has `order_completed` before earlier funnel steps and should not get retroactive step-3 credit from that event.
- `u-105` has an event before assignment; it must not serve as the qualifying first step.
- `u-101` reaches completion well after 24 hours from the first qualifying step.
- Unassigned user `u-999` must not enter denominators or step counts.
- Repeated step occurrences should not automatically invalidate a user; a later occurrence can form the valid path.
- Excluding a user while a delayed report A is pending, then starting report B, must not allow A to paint stale counts when it finishes last.
- Switching from `enterprise` to `self-serve` while the first request is delayed is a separate race from revision staleness.
- Zero denominator handling should not emit invalid JSON numbers or misleading percentage strings.

## Expected prioritization

A strong 60-minute approach tends to prioritize: (1) backend pure funnel calculation + targeted tests, (2) report endpoint with revision/delay, (3) minimal UI rendering, (4) stale-response/segment race protection, (5) error polish and extra tests. Spending most of the hour on styling is a negative signal.

## Likely failure modes

- Counting event names globally rather than constructing per-user ordered paths.
- Sorting file rows globally but not handling repeated user steps correctly.
- Using file order as event order.
- Dedupe by `(user_id,name)` instead of `event_id`.
- Starting the 24-hour window at assignment time or completion time rather than the selected first funnel step.
- Computing authoritative analytics in the browser from raw fixture data.
- Refreshing after exclusions but allowing an old promise to overwrite the refreshed report.
- Clearing report output on transient failures.
- Breaking exclusion reason validation or revision increments.

## What to inspect after the hour

Look for isolated/testable domain semantics, deterministic behavior, a clear snapshot/revision model, request-race protection on the client, preservation of existing exclusions, and evidence that the candidate verified the tricky cases rather than trusting generated code.
