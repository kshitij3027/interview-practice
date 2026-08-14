# Phase 1 — Funnel core (`src/funnel.js` + `test/funnel.test.js`)

Goal: a pure, dependency-free module that turns a dataset snapshot into a per-variant funnel
result. No store coupling, no HTTP, no dates-from-`Date.now()`. Everything in this phase is
directly unit-testable, and Phases 2–5 only wire it up.

Files touched:

| File | Change |
| --- | --- |
| `src/funnel.js` | new — the whole funnel algorithm |
| `test/funnel.test.js` | new — semantics + determinism tests |
| `scripts/verify-build.js` | add `'src/funnel.js'` to the hard-coded `files` array (line 2) |

Nothing else changes in Phase 1. `dataStore.js`, `experimentService.js`, `routes.js` and the
frontend stay untouched, so `npm test` must keep passing unchanged.

---

## 1. Public contract

```js
export const FUNNEL_STEPS = ['product_viewed', 'checkout_started', 'order_completed'];
export const FUNNEL_WINDOW_MS = 24 * 60 * 60 * 1000; // 86_400_000, inclusive bound
export const SEGMENTS = ['all', 'self-serve', 'enterprise'];

export function computeFunnel({ assignments, events, segment = 'all' }) -> FunnelResult
```

`assignments` is `listAssignments()`/`snapshot()` shape — each row already carries `excluded`
and `exclusion_reason`, so exclusion is **not** a separate parameter. `events` is the raw parsed
JSONL array. The function mutates neither.

### Return shape

```js
{
  segment: 'all',
  eligible_total: 8,
  variants: {
    control: {
      eligible: 4,
      steps: { product_viewed: 4, checkout_started: 4, order_completed: 2 },
      rates: { product_viewed: 100.0, checkout_started: 100.0, order_completed: 50.0 }
    },
    treatment: { /* … */ }
  }
}
```

- `steps[k]` = count of eligible users who reached step *k* (integers, never rounded).
- `rates.product_viewed` denominator = `eligible`; `rates.checkout_started` denominator =
  `steps.product_viewed`; `rates.order_completed` denominator = `steps.checkout_started`
  (AC 7: "immediately preceding step as denominator").
- A zero denominator yields `null`, never `NaN`/`Infinity`/`0`.
- Variant keys come from the **assignment set**, not from whoever has events, so a variant with
  zero eligible users still appears with zeroed counts and `null` rates. Keys are inserted in
  sorted order for stable JSON output.

---

## 2. Algorithm

The funnel itself is **three steps** (`product_viewed` → `checkout_started` → `order_completed`),
per the README. The five items below are *pipeline stages* of the computation, not funnel steps —
they are named A–E to keep the two ideas apart. Only Stage D walks the funnel; the rest is data
preparation (A–C) and reporting (E).

### Stage A — index assignments

Filter to `experiment === 'checkout-copy'`, drop `excluded === true`, and drop rows whose
`segment` does not match when `segment !== 'all'`. Build
`Map<user_id, { variant, assignedAtMs }>`. Rows with an unparseable `assigned_at` are dropped
(defensive; there are none in the fixture).

`eligible` per variant is counted here — a user is *eligible* purely by assignment/exclusion/
segment, independent of whether they have any events (AC 7 wording: "counts for eligible
assigned users **and** users reaching each step").

### Stage B — deduplicate by `event_id` (AC 4)

Group all events by `event_id`. For a group of size 1, take it. For size > 1, pick the
occurrence that sorts first by:

1. `occurred_at` ascending (parsed ms; unparseable sorts last), then
2. `stableStringify(event)` ascending — `JSON.stringify` over keys sorted with
   `Array.prototype.sort()`.

**File position is never used as a tiebreak.** A "first row in the file wins" rule would make
the winner depend on JSONL order the moment two duplicates disagree, violating AC 8. The two
sort keys above are total and content-derived, so the winner is identical under any input
permutation. This rule goes in a header comment in `src/funnel.js` (AC 4 requires it be
documented).

### Stage C — filter to qualifying events

Keep a deduped event only if all hold:
- `name` is one of `FUNNEL_STEPS`
- `user_id` is in the eligible map (drops `u-999` and excluded/off-segment users, AC 3)
- `occurred_at` parses
- `occurredAtMs >= assignedAtMs` for that user (AC 3)

### Stage D — per-user ordered path (AC 5, AC 6)

Group qualifying events by `user_id` and sort each group by `(occurredAtMs asc, event_id asc)`.
`event_id` is the tiebreak so identical timestamps resolve deterministically.

Then, selecting by **time** rather than array index (so "at or after" correctly admits equal
timestamps):

```
t1 = min occurredAtMs where name === 'product_viewed'
     → none ⇒ user reached 0 steps
t2 = min occurredAtMs where name === 'checkout_started' and t >= t1
     → none ⇒ user reached step 1 only
t3 = min occurredAtMs where name === 'order_completed'  and t >= t2 and t <= t1 + FUNNEL_WINDOW_MS
     → none ⇒ user reached step 2 only
otherwise ⇒ user reached all 3 steps
```

**Why greedy-earliest is correct, not just convenient.** The 24h window is anchored on the
user's *first qualifying* `product_viewed`, so `t1` is fixed by the spec — later views do not
re-anchor. With `t1` fixed, choosing the smallest valid `t2` is optimal (it maximally relaxes
the `t >= t2` constraint on step 3), and the smallest valid `t3` is optimal for the window
bound. No backtracking or "try later occurrences" pass is needed: if the earliest valid
completion misses the window, every later one misses it too.

This also gives AC 5's "repeated step events may be used if an earlier occurrence cannot form a
valid ordered path" for free — the min-over-qualifying-occurrences selection naturally skips
an out-of-order occurrence (`u-103`'s `order_completed` at 09:12 precedes its checkout, so it is
never selected) and naturally picks a later repeat when the earlier one is ineligible
(`u-105`'s 09:00 view is pre-assignment, so the 09:40 view becomes `t1`).

### Stage E — aggregate and rate

Increment `steps.product_viewed` / `.checkout_started` / `.order_completed` cumulatively
(reaching step 3 also counts toward steps 1 and 2, so counts are monotonically non-increasing
down the funnel — asserted in tests).

```js
function rate(numerator, denominator) {
  if (!denominator) return null;                       // 0 or undefined ⇒ null, never NaN
  return Math.round((numerator / denominator) * 1000) / 10;
}
```

Single rounding function, applied identically to all three rates (AC 8: "rounded to one decimal
place in a consistent way"). Half-up via `Math.round`; documented in a comment.

---

## 3. Module layout

```
src/funnel.js
  ├─ header comment: dedup rule, window anchoring, greedy-earliest rationale
  ├─ FUNNEL_STEPS, FUNNEL_WINDOW_MS, SEGMENTS (exported)
  ├─ toMs(iso)                    → number | null
  ├─ stableStringify(obj)         → string          (sorted-key JSON)
  ├─ dedupeEvents(events)         → Event[]         (exported for direct testing)
  ├─ userPathSteps(sortedEvents)  → 0 | 1 | 2 | 3   (exported for direct testing)
  ├─ rate(n, d)                   → number | null
  └─ computeFunnel({...})         → FunnelResult
```

Exporting `dedupeEvents` and `userPathSteps` lets the tests pin the two subtle rules directly
rather than only through the aggregate, which keeps failures diagnosable.

---

## 4. Fixture oracle

Hand-derived from `fixtures/*`, segment `all`, nothing excluded. These are the exact numbers the
tests assert:

| User | Variant | Segment | Outcome | Why |
| --- | --- | --- | --- | --- |
| u-100 | control | self-serve | 3 steps | clean path 09:10 → 09:20 → 09:40 |
| u-103 | control | enterprise | 2 steps | `order_completed` 09:12 is both pre-assignment and pre-checkout |
| u-105 | control | self-serve | 2 steps | 09:00 view pre-assignment; anchors on 09:40 view, no completion |
| u-107 | control | enterprise | 3 steps | clean path |
| u-101 | treatment | self-serve | 2 steps | completion 08-11T12:00 is ~26.8h after the 09:12 anchor — outside the window |
| u-102 | treatment | enterprise | 3 steps | `e-09` duplicated twice, counted once |
| u-104 | treatment | self-serve | 3 steps | clean path |
| u-106 | treatment | enterprise | 3 steps | clean path |
| u-999 | — | — | ignored | not assigned to `checkout-copy` |

Aggregates:

| Segment | Variant | eligible | s1 | s2 | s3 | rates |
| --- | --- | --- | --- | --- | --- | --- |
| all | control | 4 | 4 | 4 | 2 | 100.0 / 100.0 / 50.0 |
| all | treatment | 4 | 4 | 4 | 3 | 100.0 / 100.0 / 75.0 |
| self-serve | control | 2 | 2 | 2 | 1 | 100.0 / 100.0 / 50.0 |
| self-serve | treatment | 2 | 2 | 2 | 1 | 100.0 / 100.0 / 50.0 |
| enterprise | control | 2 | 2 | 2 | 1 | 100.0 / 100.0 / 50.0 |
| enterprise | treatment | 2 | 2 | 2 | 2 | 100.0 / 100.0 / 100.0 |

---

## 5. Test plan — `test/funnel.test.js`

Plain `node:test` + `node:assert/strict`, matching the existing files' style (no framework, no
helpers beyond a small synthetic-dataset builder).

**Fixture-driven (uses `loadFixtureData()`):**
1. `computeFunnel` over the real fixture, segment `all`, matches the oracle table exactly
   (counts and rates, deep-equal on the whole result object).
2. Same for `self-serve` and `enterprise`; asserts segment filtering changes `eligible`.
3. Passing `excluded: true` on `u-102` removes them from both `eligible` and every step count.
4. `u-999` contributes nothing (assert `eligible_total === 8`).
5. Funnel counts are monotonically non-increasing across the three steps, for every variant.

**Determinism (AC 8) — the important one:**
6. **Differing duplicates:** synthetic dataset with two rows sharing `event_id` `d-1` but with
   different `occurred_at` (one inside the 24h window, one outside). Assert the result is the
   same for the array *and* its reverse, and equals the `occurred_at`-ascending winner. The
   shipped `e-09` duplicates are byte-identical and cannot catch a file-order-dependent rule,
   which is exactly why this synthetic case exists.
7. **Payload-only difference:** two rows sharing an `event_id` and `occurred_at` but differing in
   an extra field; assert the `stableStringify` tiebreak picks the same winner in both orders.
8. **Deterministic shuffle:** the real fixture events run through a seeded (LCG, no
   `Math.random`) permutation produce a result deep-equal to the unshuffled run. Repeat over
   several seeds.

**Window semantics (AC 6):**
9. Completion at exactly `t1 + 24h` counts as step 3 (inclusive boundary).
10. Completion at `t1 + 24h + 1ms` does not.
11. A later `product_viewed` does **not** re-anchor: view at T, view at T+20h, completion at
    T+23h with a checkout in between ⇒ step 3 counts (anchor is the *first* view, and T+23h is
    inside 24h of T). Contrast case: completion at T+25h ⇒ step 2, even though it is within 24h
    of the second view.

**Ordering / repeats (AC 5):**
12. `order_completed` before `checkout_started` in event time ⇒ step 2 only, regardless of file
    order.
13. Repeat recovery: checkout at T-1 (before the view) and a second checkout at T+1 ⇒ step 2 is
    reached via the later occurrence.
14. Identical timestamps across two candidate events resolve by `event_id` and the outcome is
    order-independent.

**Eligibility (AC 3):**
15. Event exactly at `assigned_at` qualifies (inclusive); one millisecond before does not.

**Rates (AC 7):**
16. Zero eligible users ⇒ all three rates `null`, counts `0`, and `JSON.stringify` of the result
    contains no `NaN`/`Infinity` (assert via round-trip parse).
17. Rounding: 1/3 ⇒ `33.3`, 2/3 ⇒ `66.7`, 1/8 ⇒ `12.5`.
18. A variant present in assignments but with no events still appears with zeroed counts.

**Purity:**
19. `computeFunnel` does not mutate its `assignments`/`events` arguments (deep-equal against a
    pre-call `structuredClone`).

---

## 6. Exit criteria

- `node --test test/funnel.test.js` green.
- `npm test` green — the three existing suites unchanged and still passing.
- `npm run build` green **and** actually syntax-checking `src/funnel.js` (verify the printed
  module count went from 8 to 9).
- No changes outside the three files listed at the top.

Phase 2 then consumes `computeFunnel` from `ExperimentService.funnel()` via the new
`DataStore.snapshot()`.
