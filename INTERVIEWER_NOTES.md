# POST-PRACTICE ONLY — Interviewer Notes

**Do not read this file before completing the 60-minute exercise.**

## Intended solution outline

A strong solution usually isolates timeline transformation as a pure function or domain helper. It validates the requested dates/plan, snapshots the account revision and existing segments, and computes the resulting timeline without touching live state. The simplest robust strategy is to reason in terms of interval boundaries: preserve the prefix before `start_on`, overlay the target plan for the requested interval, preserve or reconstruct the suffix after `end_on`, then normalize by sorting/coalescing adjacent equal-plan segments and rejecting impossible gaps/overlaps.

For a bounded temporary interval, the plan effective at `end_on` must be derived from the **pre-preview** timeline, not from a partially transformed result. Existing scheduled boundaries strictly inside the temporary interval are masked by the overlay. For an open-ended interval, all later schedule semantics are replaced from `start_on` onward.

Preview state should be stored server-side under an opaque ID with account ID, base revision, validated request inputs, proposed timeline, and application status. Apply should lock/mutate once, verify revision before any write, replace the timeline atomically, increment revision exactly once, and mark the preview applied. A repeated apply of that same successful preview should return the prior result or an explicit already-applied outcome without another mutation.

## Subtle traps / hidden checks

- `end_on` is exclusive. Boundary equality matters.
- If a temporary interval spans one or more existing future boundaries, those interior boundaries do not survive inside the overlay.
- At `end_on`, restore what the original timeline would have provided at that date. Do not blindly restore the plan that was active at `start_on`.
- If `end_on` lands exactly on an existing boundary, resume the segment beginning at that boundary.
- If target plan equals a neighboring segment's plan, coalescing may remove the newly created boundary entirely.
- Avoid zero-length segments when `start_on`/`end_on` coincide with existing boundaries.
- A preview must not mutate account segments or revision, even through shared object references.
- An intervening existing immediate plan change is the intended stale-conflict source.
- Revision check must occur before any timeline write; stale apply is all-or-nothing.
- Retry-safe apply is distinct from allowing a stale preview to apply after some unrelated mutation.
- Unknown and inactive plans are separate validation failures.
- Use the fixture business date, not `Date.today`, so behavior is deterministic.

## Expected prioritization

1. Understand and test existing segment/revision behavior.
2. Implement deterministic pure timeline overlay + normalization tests.
3. Add server-owned preview storage and preview endpoint.
4. Add atomic stale-protected, retry-safe apply endpoint.
5. Build the minimum usable UI and reconcile after apply/conflict.
6. Add polish only after the dangerous semantics are covered.

## Likely failure modes

- Appending a new segment without splitting/removing overlaps.
- Restoring the plan from `start_on` instead of the original plan at `end_on`.
- Losing future schedule segments after a bounded temporary interval.
- Treating `end_on` as inclusive.
- Mutating shared timeline objects during preview.
- Trusting client-submitted proposed segments during apply.
- Incrementing revision per changed segment instead of once.
- Checking revision after partially mutating.
- Treating retry of a successful preview as a new stale request and/or applying twice.
- Clearing form input after stale conflict.
- Breaking existing immediate plan change behavior.

## What to inspect after the hour

Look for a clean domain boundary around interval transformation, correct exclusive-date semantics, immutable preview behavior, explicit server-owned preview state, one mutation boundary for apply, clear retry semantics, preservation of the existing immediate-change invariant, targeted tests around interior/exact boundaries, and evidence of actual browser/error-path verification.
