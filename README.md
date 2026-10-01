# ScreenFlow — HARD One-Hour Full-Stack Interview Exercise

## Context
ScreenFlow is an internal digital-signage operations console used by venue teams. The starter app is already functional: Java 21 standard-library HTTP API, in-memory fixture-backed state, and dependency-free browser ES modules.

## Existing behavior
- Screens are ordered by venue, zone, then screen ID and can be filtered by zone/status.
- Detail shows baseline playlist, playback mode, screen revision, and global dataset revision.
- Operators can switch playback mode between `normal` and `muted`.
- Mode writes require the screen revision observed by the client. Stale writes do not mutate.
- A changed mode increments screen + dataset revision exactly once; writing the same mode is a no-op.
- Restart restores `fixtures/screens.csv`.

`fixtures/playlist_windows.csv` contains representative temporary scheduling windows. The starter does not yet expose or mutate that schedule.

## Customer / business problem
Venue teams routinely schedule temporary content for launches, sponsors, conferences, and special events. Several windows may intentionally overlap: a broad event loop can coexist with a shorter, higher-priority VIP message. Operators need a trustworthy answer for what should play at a specific instant, plus safe create/cancel actions when requests are retried or another operator changes the screen while a slow request is in flight.

## Primary feature request
**Add a server-authoritative temporary playlist-window workflow that loads the checked-in schedule, lets operators create and cancel windows, evaluates the effective playlist at an arbitrary instant, and remains correct under overlap, stale revisions, retries, and out-of-order browser responses.**

## Deterministic scheduling semantics
Each window has `window_id, screen_id, start_at, end_at, playlist_id, priority, reason, state`.

A window is half-open: it applies when `start_at <= at < end_at` after timestamps are compared as instants. Cancelled windows never participate. If no active window applies, the screen's baseline playlist wins. If several active windows apply, choose by:

1. greater `priority`;
2. shorter elapsed window duration;
3. later `start_at` instant;
4. lexicographically smaller `window_id`.

CSV row order must never affect the answer.

## Acceptance criteria
1. Load `fixtures/playlist_windows.csv` as the server-owned starting schedule. Restart discards runtime creations/cancellations.
2. Fail clearly on malformed fixture state: duplicate IDs, unknown screen, invalid or offset-less timestamps, `start_at >= end_at`, priority outside `0..9`, blank playlist/reason, or unsupported state.
3. Show the selected screen's windows ordered by start instant, end instant, priority descending, then window ID.
4. Add an **Evaluate at** control. The browser sends the selected screen and offset-aware timestamp to the backend; the backend returns the effective playlist plus baseline/winning-window explanation. The browser must not determine the winner.
5. Implement exact half-open boundaries, overlap precedence, offset-equivalent timestamps, and cancelled-window exclusion.
6. Evaluation rejects malformed/offset-less timestamps and never mutates state.
7. Evaluation accepts optional bounded `delay_ms` (`0..2000`) for race testing. A slower old evaluation or response for a previously selected screen must never repaint newer context.
8. Add create fields: `start_at`, `end_at`, `playlist_id`, `priority`, and `reason`. Trim text. Playlist ID must be 1..64 chars, reason 1..160 chars, timestamps must include an offset, `start_at < end_at`, and duration must be at most 168 hours.
9. Overlap is allowed. The backend generates the permanent window ID and owns the authoritative schedule.
10. Only an `active` screen may receive a new window. Creating for an offline screen fails with zero mutation.
11. Create includes the observed screen revision and a client-generated request key. A stale revision fails with zero schedule mutation and returns enough current state for recovery.
12. Request-key identity is based on normalized logical payload: screen ID, start/end instants, trimmed playlist ID, integer priority, and trimmed reason. `delay_ms` is excluded. Same key + same logical payload returns the original result; same key + different payload fails clearly.
13. Offset-equivalent timestamp text represents the same logical payload for retry identity.
14. A successful changed create increments the screen revision and dataset revision exactly once.
15. Add cancel for an existing selected-screen window. It requires the observed screen revision and a client-generated request key. Cancellation marks the row `cancelled`; do not delete history.
16. Same-key cancel retry returns the original result. Reusing that key for another window fails. A fresh cancellation of an already-cancelled window is an explicit no-op with no revision increment.
17. Create and cancel support bounded `delay_ms`. If playback mode changes while a delayed mutation is in flight, the old expected revision must make that mutation fail stale with zero schedule mutation.
18. After create/cancel success, reconcile selected screen, schedule, revisions, and any current evaluation without full reload. If an evaluation instant is still present, rendered output must correspond to the updated schedule.
19. Switching screens while create/cancel/evaluate is in flight must not let an older response overwrite the newly selected screen. The server mutation may still complete; client reconciliation must be scoped to matching screen context.
20. A transient create/cancel/evaluate failure preserves last-known-good screen/schedule data when possible. Failed create preserves entered form values.
21. Prevent duplicate submission of the same in-flight create/cancel while leaving unrelated browsing/evaluation usable.
22. Existing ordering/filtering/detail/mode validation, optimistic concurrency, no-op behavior, and revision accounting must remain green.

## Constraints
Keep the Java 21 + browser ES-module stack, one-process in-memory state, and checked-in fixtures. Do not add a database, queue, websocket, auth provider, or external API. Production screens may have tens of thousands of historical/scheduled windows, so avoid designs that depend on CSV row order or obviously scan every screen's global history for each operation. The server owns schedule state, timestamp normalization, winner selection, revisions, permanent IDs, and retry outcomes.

## Out of scope
Authentication, distributed locking, persistence across restart, recurring windows, editing an existing window in place, notifications, external CMS integration, and visual polish.

## Run / verify
```bash
./scripts/test.sh
./scripts/build.sh
./scripts/verify.sh
./scripts/run.sh
```

Open `http://localhost:8080`.

## 60-minute AI-assisted interview instruction
You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or similar tools. Inspect the existing revision boundary, HTTP routes, browser state, and both fixtures before coding. Implement incrementally and verify exact boundaries, overlap precedence, offset-equivalent times, stale mutations, retries, and slow/out-of-order responses.

A polished calendar that computes winners in the browser, depends on fixture order, double-creates after retry, ignores screen revisions, or lets old responses repaint a new screen is not a complete solution.
