# POST-PRACTICE ONLY — Interviewer Notes

## Intended solution outline
A strong implementation introduces a playlist-window model and server-owned schedule at the existing store/service boundary, parses fixture timestamps to normalized instants at startup, and keeps create/cancel mutations synchronized with screen revision checks. The browser treats evaluation results as server-owned output and guards async responses by selected screen plus request identity.

Among active windows containing `at`, select by priority descending, duration ascending, start instant descending, ID ascending. A linear scan of one screen's windows is acceptable for the hour if the candidate explains production indexing; correctness matters more than premature complexity.

Create should normalize timestamps/text before building an idempotency fingerprint and store the first successful outcome by request key so a retry returns the same generated window ID/result. Stale checks must occur inside the mutation boundary after any simulated delay. Cancel follows the same principle and preserves historical rows.

## Complexity/scalability
A credible interview solution can index windows by screen and scan/sort only that screen. Production discussion may cover pre-sorted per-screen collections, interval indexes, caching, or bounded idempotency-result retention. Rebuilding a global schedule for every evaluation should lose scalability points.

## Why naive approaches fail
- Comparing timestamp strings breaks equivalent offsets and ordering.
- Treating `end_at` as inclusive causes boundary double-application.
- Picking the first CSV match makes output row-order dependent.
- Sorting only by priority misses duration/start/ID tie-breaks.
- Browser-side winner selection can diverge from server state.
- Generating a fresh permanent ID on retry duplicates windows.
- Fingerprinting raw timestamp text breaks logically equivalent retries.
- Checking revision before delay but mutating afterward creates a stale-write race.
- Deleting cancelled rows loses history and complicates retries/no-ops.
- One global frontend loading/result slot lets old responses repaint a different screen.

## Subtle traps
1. Start inclusive, end exclusive.
2. Duration uses elapsed instants, not formatted local-clock text.
3. Priority beats duration; duration beats later start; later start beats ID.
4. Lexicographically smaller ID is final tie-break.
5. Cancelled rows remain visible/history-capable but never win.
6. `2026-10-01T15:00:00Z` equals `2026-10-01T11:00:00-04:00`.
7. Trim playlist/reason before retry identity.
8. `delay_ms` is not part of logical payload identity.
9. A fresh cancel of an already-cancelled row is a no-op.
10. Existing mode behavior must remain unchanged.

## Hidden checks
- Shuffle the window fixture; evaluation and ordering stay identical.
- Evaluate exactly at a window start and exactly at its end.
- For `s-lobby` around `2026-10-01T15:10:00Z`, higher priority beats the broad lower-priority window and shorter duration resolves equal priority.
- Add equal-priority/equal-duration windows with different starts; later start wins.
- Add equal priority/duration/start windows; lexicographically smaller ID wins.
- Cancelled high-priority row never wins.
- 168-hour create succeeds; slightly longer fails.
- Empty/65-char playlist ID or empty/161-char trimmed reason fails.
- Same request key with `15:00Z` then equivalent `11:00-04:00` returns original result.
- Same key with changed playlist or priority conflicts with zero mutation.
- Start delayed create, mutate playback mode through existing endpoint, then let create finish: stale with no schedule mutation.
- Successful create increments screen + dataset revisions once; retry increments neither.
- Cancel success increments once; same-key retry increments neither; fresh already-cancelled cancel is no-op.
- Switch screens while evaluation is delayed; old response does not repaint.
- Slow Eval A then fast Eval B for same screen; B stays rendered.
- Existing zone/status filters and mode mutation still pass.

## Alternative defensible designs
The exact class/module layout is flexible. IDs may be sequential, UUID-like, or another process-unique server-generated scheme. Linear per-screen evaluation is acceptable if correctness is strong and scale tradeoffs are articulated. Client race protection may use monotonic request tokens, AbortController, or equivalent context checks.

## Likely AI-agent failure modes
One-shot agents often build the UI first, calculate the winner in JavaScript, compare raw timestamp strings, omit idempotency payload binding, or validate stale state before sleeping. Generated client code also tends to reuse one global result/loading flag, allowing delayed responses to overwrite whatever screen is currently open.

## Recommended prioritization
Secure fixture parsing and deterministic evaluation first, then create with stale/idempotency safety, then cancel, then minimal UI integration. Add async race guards as soon as evaluation is wired. Styling comes last.

## What to inspect after the hour
Where are timestamps normalized? Can client data dictate the winner? Is selection independent of row order? Are stale checks inside the mutation boundary? Does request-key state bind to normalized payload? Are revisions exact? Does cancel preserve history? Can an old response repaint a different screen? Did existing mode behavior remain green?
