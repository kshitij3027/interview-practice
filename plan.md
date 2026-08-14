# Signal Lab — Funnel Report Implementation Plan

Scope: implement the feature request in `README.md` (segment-aware three-step funnel with
deterministic event semantics and race-safe client reconciliation). Keep the dependency-free
Node + browser ES-module stack. No frameworks, no new dependencies, no persistence.

---

## Design decisions (locked before coding)

### Funnel semantics — backend is the source of truth (`src/funnel.js`)

- **Dedup by `event_id`:** group by `event_id`; the canonical occurrence is the one that sorts
  first by `(occurred_at, canonical JSON of the payload with sorted keys)`. File order is
  **never** consulted — a first-in-file rule would break AC 8, since shuffling the JSONL could
  change which of two differing duplicates wins. Documented in a module header comment.
- **Eligibility:** the user must be assigned to `checkout-copy`, not excluded, and match the
  segment filter. An event counts only if `occurred_at >= assigned_at` for that user.
  Events for unassigned users (`u-999`) are dropped.
- **Ordering:** each user's eligible events are sorted by `(occurred_at, event_id)`.
  `event_id` is the stable tiebreak so equal timestamps are deterministic.
- **Path selection — greedy earliest-valid:** earliest eligible `product_viewed` → earliest
  `checkout_started` at or after it → earliest `order_completed` at or after that.
  Greedy-earliest is optimal here: choosing the earliest valid occurrence of a step never rules
  out a later step, and it maximizes the remaining 24h budget. Criterion 5 ("repeated step
  events may be used") falls out of this naturally — e.g. `u-105`'s 09:00 view is
  pre-assignment and ineligible, so the 09:40 view is used instead.
- **24h window:** step 3 counts only if
  `order_completed - first_qualifying_product_viewed <= 24h` (inclusive boundary). The anchor is
  the user's **first qualifying** `product_viewed`; later `product_viewed` events do **not**
  re-anchor or reset the window (README line 36 reads "first qualifying"). Because the anchor is
  fixed and step 3 selects the earliest qualifying completion, no later completion can rescue a
  window miss — there is nothing to scan past.
- **Percentages:** `step2_rate = step2/step1`, `step3_rate = step3/step2`, plus an overall
  `step1/eligible`. A zero denominator yields `null` (never `NaN`/`Infinity`/`0`), rendered as
  `—` in the UI. Rounding is one decimal via `Math.round(ratio * 1000) / 10`.
- **Counts stay integers.** Only rates are rounded.

### Expected fixture outcome (segment `all`, nothing excluded) — the test oracle

- `u-101`: order at `2026-08-11T12:00` is more than 24h after the `09:12` view → **no step 3**.
- `u-103`: `order_completed` precedes `product_viewed` → **step 2 only**.
- `u-105`: `09:00` view is pre-assignment; uses `09:40` view → **step 2**.
- `u-999`: unassigned → **ignored entirely**.
- `e-09`: duplicate `event_id` → **counted once**.

### Race / staleness model (frontend)

- **Monotonic revision:** `revision = Math.max(known, incoming)` on every overview/users/
  exclusion/funnel response. It never decreases.
- **Request tagging:** each funnel request carries a client-side monotonic `requestId` and the
  `segment` it was issued for. A response is applied only if it is the newest issued request
  **and** its segment still matches the current selection (AC 12).
- **Stale-revision self-heal:** if an applied response's `revision` is lower than the store's
  known revision, discard it and immediately issue a fresh report (AC 11 — a slow older
  request finishing last can never re-render an excluded user).
- **Exclusion/inclusion:** the `PATCH` response's `revision` is applied to the store
  **immediately** (`revision = Math.max(current, result.revision)`) *before* awaiting
  `refresh()`. The current code only learns the new revision after `refresh()` resolves
  (`web/app.js:67`), which leaves a window where a stale funnel response looks current.
  Only after stamping the revision do we refresh users/overview and reload the funnel (AC 13).
- **Failures** set `reportError` and leave `report` untouched, so the last known-good report
  stays visible with an actionable inline message (AC 14).

---

## Phases

Each phase builds on the previous one and ships with its own tests.

### Phase 1 — Funnel core (pure module + tests)

- Add `src/funnel.js` exporting
  `computeFunnel({ assignments, events, segment, excluded })` → per-variant
  `{ eligible, step1, step2, step3, rates }`.
- Pure function, no store/HTTP coupling, so it is directly unit-testable.
- Tests — `test/funnel.test.js`:
  - duplicate `event_id` counted once
  - pre-assignment events ignored
  - unassigned user ignored
  - shuffled JSONL input produces byte-identical output (determinism, AC 8), using a synthetic
    fixture where two rows share an `event_id` but have **different payloads** — the shipped
    `e-09` duplicates are identical, so they cannot catch a file-order-dependent dedup rule
  - 24h boundary: exactly 24h counts, 24h + 1ms does not
  - repeated-step recovery when an earlier occurrence cannot form a valid path
  - zero denominator → `null`
  - rounding to one decimal

### Phase 2 — Service layer

- Add `DataStore.snapshot()` → `{ assignments, events, revision }`, where `assignments` already
  carry `excluded`/`exclusion_reason` (i.e. `listAssignments()` output). The store currently
  exposes only `listAssignments()`, `listEvents()`, and a bare `revision` field
  (`src/dataStore.js:24`), so there is no way to read a consistent triple today. `snapshot()`
  makes the contract explicit and guarantees the stamped revision matches the data returned.
- `ExperimentService.funnel({ segment })` → `{ experiment, revision, segment, variants }`, built
  from exactly one `snapshot()` call.
- Validate `segment ∈ {all, self-serve, enterprise}` → `{ ok: false, code: 'invalid_segment' }`.
- Tests — extend `test/experimentService.test.js`:
  - segment filtering changes eligible counts
  - excluding a user drops them from the funnel and increments the revision
  - invalid segment rejected

### Phase 3 — Route + bounded test delay

- `GET /api/funnel?segment=&delay_ms=` in `src/routes.js`.
- `delay_ms` parsed as an integer and clamped to `0..5000`; non-numeric input becomes `0`
  rather than an error.
- **Order of operations: compute → sleep → respond.** Computing first and sleeping afterwards
  is what makes a delayed response genuinely stale, which is required to exercise AC 11.
- Tests — extend `test/routes.test.js`:
  - 200 response shape includes `revision`, `segment`, `variants`
  - invalid segment → 400
  - `delay_ms` clamped and out-of-range values do not error

### Phase 4 — Frontend request lifecycle

- `web/api.js`: add `funnel(segment, delayMs)`.
- `web/store.js`: add `report`, `reportError`, `reportLoading`, `funnelRequestId`,
  `debugDelayMs`; route revision updates through a monotonic `setRevision` helper.
- `web/app.js`: add `loadReport()` implementing the requestId + segment + revision guards
  above. Segment `change` ignores the in-flight response and issues a new request;
  exclusion/inclusion triggers refresh plus `loadReport()`.

### Phase 5 — Report UI

- Replace the `.placeholder` section with a per-variant funnel table: eligible users, the
  three step counts, the step conversion rates (`—` when `null`), and a
  "Report for revision N (segment X)" line.
- Add a bounded "test delay (ms)" input so a reviewer can reproduce the staleness scenario
  manually.
- The report section renders independently of the user table, so a report error never clears
  the analysis area or disturbs existing table/toolbar behavior.

### Phase 6 — Verification

- `npm test` — full suite; all pre-existing tests must still pass (AC 15).
- `npm run build` — `scripts/verify-build.js:2` hard-codes its file list, so new modules
  (`src/funnel.js`) go unchecked unless the list is updated. Phase 1 adds `src/funnel.js` to
  that array (a small, explicit edit is preferable to introducing directory walking).
- Browser pass with both servers running:
  1. default report renders
  2. segment switch updates the report
  3. set delay to 3000 → refresh the report → immediately exclude a user → confirm the stale
     response is discarded/reconciled and the excluded user's contribution is gone

---

## Acceptance-criteria coverage map

| AC | Covered by |
| --- | --- |
| 1 API + UI | Phases 3, 5 |
| 2 segment filter, exclusions ineligible | Phases 1, 2 |
| 3 `assigned_at` eligibility, unassigned ignored | Phase 1 |
| 4 deterministic dedup by `event_id` | Phase 1 |
| 5 ordering by event time, repeated steps | Phase 1 |
| 6 24h window | Phase 1 |
| 7 counts + safe percentages | Phase 1 |
| 8 file-order independence, rounding | Phase 1 |
| 9 revision in every response, client tracks newest | Phases 2, 4 |
| 10 bounded `delay_ms` | Phase 3 |
| 11 stale response never rendered | Phase 4 |
| 12 segment race | Phase 4 |
| 13 exclusion reconciles report | Phases 4, 5 |
| 14 failure keeps last-good report | Phases 4, 5 |
| 15 existing behavior intact | Phase 6 |
