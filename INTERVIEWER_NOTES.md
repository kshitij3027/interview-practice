# POST-PRACTICE ONLY — Interviewer Notes

Do not read this file before completing the 60-minute exercise.

## Intended solution outline

A strong solution typically treats preview as a pure deterministic merge-plan calculation over one consistent snapshot of the survivor and source. The server stores that plan behind an opaque preview ID together with both input revisions, the relevant dataset revision, blocking-conflict state, and enough normalized output to apply without trusting browser-authored merged values.

Contact fields can be resolved through a small deterministic comparator: non-empty beats empty, verified beats unverified, later `updated_at` wins when verification matches, and the survivor wins exact ties. Tags should be normalized for identity while preserving the required display spelling. External IDs should be unioned by namespace with conflicting non-empty values promoted to blocking conflicts. Activities should be keyed by `event_id`: identical payloads dedupe, differing payloads block, and final ordering is timestamp then event ID.

Apply should validate the stored plan is conflict-free and that both records still match the revisions captured during preview before any mutation. It should atomically write the survivor, retire the source from the normal live set, increment the two record revisions and global revision exactly once, and cache the successful result by request key so retries are idempotent.

## Likely failure modes

- Concatenating arrays/maps and relying on iteration order.
- Letting the source status or segment overwrite the survivor.
- Treating a newer unverified field as stronger than an older verified field.
- Case-sensitive tag deduplication.
- Silently picking one of two conflicting source-system IDs.
- Deduping activity by event ID without comparing payloads.
- Trusting a client-submitted merged profile during apply.
- Checking revisions after mutating the survivor, enabling partial stale writes.
- Incrementing revisions once per merged field/activity instead of once per logical merge.
- Implementing request-key dedupe only in the browser.
- Clearing operator choices after a stale conflict.
- Breaking the existing status-change optimistic concurrency flow.

## Hidden checks

- Survivor and source are identical IDs.
- Survivor email is verified but older; source email is newer but unverified.
- Phone values are identical while verification metadata differs.
- Both field timestamps tie exactly; survivor must win.
- Tags include `Robotics`, ` robotics `, and `ROBOTICS`.
- Same external namespace/value on both sides is non-blocking.
- Same external namespace with different values is blocking even when other fields merge cleanly.
- Exact duplicated activity appears on both profiles and only appears once in the plan.
- Same activity ID with a changed summary blocks apply.
- Two activity timestamps tie; event ID determines order.
- Preview succeeds, then either source or survivor status changes; apply must reject before mutation.
- Successful apply is retried with identical request key and does not increment revisions again.
- The same request key is reused for a different preview and is rejected.
- Unrelated customer status edits still function after merge feature changes.

## Expected prioritization

1. Deterministic backend merge-plan calculation and focused tests.
2. Server-owned preview state with blocking-conflict reporting.
3. Atomic stale-safe/idempotent apply.
4. Minimal usable frontend selection + preview + apply.
5. Stale/transient recovery and presentation polish.

A backend-correct solution with a rough UI is stronger than a polished UI that performs merge authority or conflict resolution in the browser.

## What to inspect after the hour

Inspect whether merge semantics live in a testable domain boundary, whether apply can partially mutate before a stale/conflict failure, whether retry semantics are truly server-side, whether revision accounting is one logical mutation, and whether the existing status workflow still passes its original tests. Also inspect whether the candidate verified the fixture's overlapping tags/activity and at least one stale/retry case rather than relying on generated code alone.
