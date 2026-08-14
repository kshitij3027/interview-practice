# Phase 2 — Service layer (`DataStore.snapshot()` + `ExperimentService.funnel()`)

Goal: expose the Phase 1 funnel core through the domain service, stamped with the dataset
revision it was computed from. Still no HTTP — Phase 3 adds the route and `delay_ms`.

Files touched:

| File | Change |
| --- | --- |
| `src/dataStore.js` | new `snapshot()` method |
| `src/experimentService.js` | import `src/funnel.js`; new `funnel({ segment })` method |
| `test/dataStore.test.js` | snapshot consistency + copy-safety tests |
| `test/experimentService.test.js` | funnel contract, segment, validation, revision-coupling tests |

Not touched: `src/funnel.js` (Phase 1 is frozen — if Phase 2 needs a funnel-core change,
that is a signal the Phase 1 contract was wrong, and it gets fixed with its own test),
`src/routes.js`, `src/http.js`, `server.js`, and everything under `web/`.

---

## 1. `DataStore.snapshot()`

```js
snapshot() {
  return { assignments: this.listAssignments(), events: this.listEvents(), revision: this.revision };
}
```

- `assignments` is `listAssignments()` output, so each row already carries `excluded` and
  `exclusion_reason` — exactly the shape `computeFunnel` expects. Exclusion state is therefore
  never passed as a separate argument that could drift from the assignment rows.
- `events` is `listEvents()`, already `structuredClone`d, so callers cannot corrupt the store.
- `revision` is read in the same expression as the data.

### Why this exists rather than three separate reads

The service must stamp a response with a revision that provably describes the data in that
response. Reading `store.listAssignments()`, `store.listEvents()` and `store.revision` as three
separate statements makes that a convention the caller has to remember; `snapshot()` makes it
the only reasonable way to use the store.

**Honest scoping note.** Node is single-threaded and `computeFunnel` is synchronous, so today no
exclusion can interleave *between* those three reads — `snapshot()` is not fixing a live bug. It
is a contract guard: Phase 3 introduces a deliberate `delay_ms`, and the moment any part of
report assembly becomes async, three separate reads become genuinely torn. The cost is one
method; the alternative is a latent bug waiting for the first `await`. This reasoning goes in a
comment on the method so a reviewer does not mistake it for cargo cult.

The `structuredClone` of ~27 events per call is irrelevant at fixture scale and is the price of
the store's existing "never hand out live references" posture, which Phase 2 does not relitigate.

---

## 2. `ExperimentService.funnel({ segment })`

```js
funnel({ segment = 'all' } = {}) -> FunnelResponse | { ok: false, code: 'invalid_segment' }
```

### Behaviour

1. Resolve `segment`, defaulting `undefined`/`null` to `'all'`.
2. Validate against `SEGMENTS` from `src/funnel.js`. Unknown values return
   `{ ok: false, code: 'invalid_segment' }` **before** the store is touched.
3. Take exactly one `this.store.snapshot()`.
4. Call `computeFunnel({ assignments, events, segment })`.
5. Return the response stamped with `snapshot.revision`.

### Response shape

```js
{
  ok: true,
  experiment: 'checkout-copy',   // EXPERIMENT constant from funnel.js
  revision: 1,                   // from the same snapshot as the data
  segment: 'all',                // the resolved segment, echoed back
  steps: ['product_viewed', 'checkout_started', 'order_completed'],
  eligible_total: 8,
  variants: { control: { eligible, steps, rates }, treatment: { … } }
}
```

Design notes:

- **`ok` discriminator.** Matches the existing `setExclusion` convention
  (`{ ok: false, code }`), so `src/routes.js` in Phase 3 can branch on `result.ok` uniformly
  instead of learning a second error protocol. `overview()`/`users()` cannot fail and so keep
  their bare shape — Phase 2 does not change them.
- **`segment` echoed back.** The client needs to confirm which segment a response describes in
  order to discard a response for a segment it no longer has selected (AC 12). Echoing it means
  the frontend guard checks server-reported truth rather than only its own request bookkeeping.
- **`steps` array included.** Carries the canonical step order and naming so the UI renders rows
  from the response instead of hardcoding a second copy of the funnel definition. Cheap, and it
  keeps the backend the single source of truth for funnel semantics (README constraint).
- **`experiment` included.** Consistent with `overview()`, and makes a response
  self-describing.
- **`revision` is the whole point.** AC 9 requires every funnel response to carry the revision
  it was calculated from; Phases 3–4 build the entire staleness guard on this field.

### What Phase 2 deliberately does not do

- No `delay_ms` (Phase 3 — it is an HTTP transport concern, not domain logic).
- No caching or memoisation of reports. State resets on restart and the fixture is tiny;
  caching would add an invalidation problem for no measurable gain.
- No change to `overview()`, `users()` or `setExclusion()` — AC 15 requires their behaviour to
  stay intact, and the existing tests for them must pass untouched.

---

## 3. Test plan

### `test/dataStore.test.js` (2 new)

1. **`snapshot` returns data and the matching revision together.** Fresh store: `revision === 1`,
   8 assignments, >20 events, every assignment row carries an `excluded` field. Then exclude
   `u-100` and take a second snapshot: `revision === 2` and the row shows `excluded: true`,
   **while the first snapshot still reads `revision === 1` and `excluded: false`**. That last
   assertion is the real content of the test — it proves a snapshot is a point-in-time read, not
   a live view.
2. **`snapshot` hands out copies.** Mutating the returned `events`/`assignments` does not affect
   what the store returns next.

### `test/experimentService.test.js` (4 new)

3. **Contract and oracle.** `funnel({ segment: 'all' })` on a fresh store returns `ok: true`,
   `experiment: 'checkout-copy'`, `revision: 1`, `segment: 'all'`, the three-name `steps` array,
   `eligible_total: 8`, and the Phase 1 oracle counts (control `4/4/4/2`, treatment `4/4/4/3`).
4. **Default and filtering.** `funnel()` deep-equals `funnel({ segment: 'all' })`; `enterprise`
   and `self-serve` each report `eligible_total: 4`.
5. **Validation.** `funnel({ segment: 'whales' })` deep-equals
   `{ ok: false, code: 'invalid_segment' }`, and the dataset revision is unchanged afterwards
   (a rejected request must not mutate anything).
6. **Revision/data coupling — the one Phase 4 depends on.** Capture a baseline report; exclude
   `u-102`; assert the new report's `revision` is `baseline.revision + 1` **and** its numbers
   changed in the same response (`eligible_total` down by one, treatment `3/3/3/2`). Then
   re-include `u-102` and assert `revision` advanced again while `variants` is deep-equal to the
   baseline. This pins the invariant the staleness guard rests on: revision and content always
   move together, and revision never repeats for different content.

Style: plain `node:test` + `node:assert/strict`, no helpers beyond what the existing files use.

---

## 4. Risks and how the tests catch them

| Risk | Caught by |
| --- | --- |
| Revision read separately from data, so a response is stamped with a revision that does not describe it | dataStore test 1 (point-in-time assertion) |
| Segment validation happening after a store read, or an unknown segment silently treated as `all` | service test 5 |
| Exclusion changing counts but not the revision (or vice versa) — would defeat the entire Phase 4 guard | service test 6 |
| Regression in `overview`/`users`/`setExclusion` | existing suites, unchanged, must stay green |

---

## 5. Exit criteria

- `npm test` green: 27 existing + 6 new = **33 tests**, with the 5 pre-Phase-1 tests unmodified.
- `npm run build` green (still 9 modules — Phase 2 adds no new file).
- `git diff` touches only the four files listed at the top.
- No frontend or route changes.

Phase 3 then exposes this via `GET /api/funnel?segment=&delay_ms=`, branching on `result.ok` and
applying the bounded delay **after** computing, so a delayed response is genuinely stale.
