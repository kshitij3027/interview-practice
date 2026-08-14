# Phases 4 & 5 — Frontend request lifecycle and report UI

Planned together because they are one change in practice: the staleness guards (Phase 4) are
only observable through what the analysis section renders (Phase 5), and the UI's failure and
loading states are part of the guard contract. They are still implemented and committed in
order — Phase 4 first, with the report rendering as raw JSON, then Phase 5 replaces that with the
real table.

Files touched:

| File | Phase | Change |
| --- | --- | --- |
| `web/reportGuards.js` | 4 | **new** — pure decision functions, the testable seam |
| `test/reportGuards.test.js` | 4 | **new** — unit tests for those decisions |
| `web/api.js` | 4 | `funnel(segment, delayMs)` |
| `web/store.js` | 4 | report/error/loading/delay state |
| `web/app.js` | 4, 5 | `loadReport()` + guards; then the analysis section |
| `web/styles.css` | 5 | a handful of rules for the report table and error banner |
| `scripts/verify-build.js` | 4 | add `web/reportGuards.js` |

Not touched: everything under `src/` (Phases 1–3 are frozen) and `fixtures/`.

---

## 1. The testability problem, and the seam that solves it

There is no jsdom, no test runner with a DOM, and the repo is deliberately dependency-free — so
`web/app.js` cannot be unit-tested without adding infrastructure the README forbids. Left alone,
that means the most subtle logic in the entire exercise (the race guards) would ship covered only
by manual clicking.

The fix is a seam, not a framework: **the guard decisions are pure functions in
`web/reportGuards.js`**, importable by `node:test` because they touch no DOM and no `fetch`.
`app.js` keeps only the I/O and rendering, which manual browser verification covers adequately.

```js
// web/reportGuards.js
export function classifyReport({ requestId, latestRequestId, responseSegment, selectedSegment,
                                 responseRevision, knownRevision }) -> 'apply' | 'discard' | 'refetch'

export function nextRevision(known, incoming) -> number   // monotonic max, ignores null/undefined
```

### `classifyReport` decision table

Evaluated in this order — the order matters and is asserted by tests:

| # | Condition | Result | Why |
| --- | --- | --- | --- |
| 1 | `requestId !== latestRequestId` | `discard` | A newer request has been issued; this response is superseded no matter what it says (AC 11, AC 12) |
| 2 | `responseSegment !== selectedSegment` | `discard` | The user has switched segments; rendering this would show the wrong segment's numbers under the new label (AC 12) |
| 3 | `responseRevision < knownRevision` | `refetch` | The dataset moved on while this was in flight. Discarding alone would leave a stale report on screen, so we immediately re-request (AC 11) |
| 4 | otherwise | `apply` | Newest request, right segment, not behind the known revision |

Checks 1 and 2 overlap deliberately: check 1 is client bookkeeping, check 2 is server-reported
truth from the echoed `segment`. Either alone would cover the ordinary segment-switch case, but
keeping both means a bug in the request counter cannot silently produce a mislabelled report.

**Rule 3 must compare before applying.** `nextRevision` is *not* called until after
`classifyReport` returns, because folding the response's revision into the known revision first
would make `responseRevision < knownRevision` unsatisfiable — the guard would disable itself. This
is the single easiest way to get this wrong and gets its own test.

---

## 2. `web/api.js`

```js
funnel: (segment = 'all', delayMs = 0) => {
  const params = new URLSearchParams({ segment });
  if (delayMs > 0) params.set('delay_ms', String(delayMs));
  return request(`/api/funnel?${params}`);
}
```

`URLSearchParams` handles encoding; `delay_ms` is omitted entirely when zero so ordinary requests
carry no debug parameter. The existing `request` helper already throws `body.error` on non-2xx,
so an invalid segment surfaces as `Error('invalid_segment')`.

---

## 3. `web/store.js`

Added state:

```js
report: null,          // last known-good funnel response; survives errors
reportError: '',       // report-specific, kept separate from the existing `message`
reportLoading: false,
debugDelayMs: 0
```

`revision` already exists. What changes is that **every** revision update goes through
`nextRevision`, so the client's known revision is monotonic and a slow older response can never
drag it backwards (AC 9).

`createStore` itself is not modified — no reducers, no middleware. Monotonicity is enforced by a
single `applyRevision(incoming)` helper in `app.js` that all four call sites use (overview, users,
exclusion, funnel).

Request bookkeeping (`latestRequestId`) lives as a module-level counter in `app.js`, **not** in
store state: it is not rendered, and putting it in state would trigger a pointless re-render on
every request.

---

## 4. `web/app.js` — the lifecycle

### `loadReport()`

```js
let latestRequestId = 0;
let staleRetries = 0;
const MAX_STALE_RETRIES = 3;

async function loadReport() {
  const requestId = ++latestRequestId;
  const { selectedSegment: segment, debugDelayMs } = store.get();
  store.set({ reportLoading: true, reportError: '' });
  try {
    const response = await api.funnel(segment, debugDelayMs);
    const decision = classifyReport({
      requestId, latestRequestId,
      responseSegment: response.segment, selectedSegment: store.get().selectedSegment,
      responseRevision: response.revision, knownRevision: store.get().revision
    });
    if (decision === 'discard') return;                       // a newer request owns the UI
    if (decision === 'refetch') {
      if (staleRetries >= MAX_STALE_RETRIES) { /* surface error, keep last-good */ return; }
      staleRetries += 1;
      return loadReport();
    }
    staleRetries = 0;
    applyRevision(response.revision);
    store.set({ report: response, reportLoading: false, reportError: '' });
  } catch (error) {
    if (requestId !== latestRequestId) return;                // stale failure: stay quiet
    store.set({ reportLoading: false, reportError: error.message });   // `report` untouched
  }
}
```

Points worth stating:

- **`discard` returns without clearing `reportLoading`.** The newer request that superseded this
  one owns that flag and will clear it. Clearing it here would flicker the spinner off while a
  request is still running.
- **Stale failures are swallowed.** A superseded request that *errors* must not paint an error
  banner over a newer successful report — hence the `requestId` check in `catch` too.
- **`report` is never cleared on error** (AC 14). The last known-good report stays rendered
  underneath an error banner.
- **Bounded refetch, then resync — never adopt a stale response.** `refetch` recursion normally
  terminates after one retry. But the bound is not merely defensive: **restarting the API resets
  the revision counter to 1** (documented existing behaviour), so a client that knows revision 3
  would classify *every* subsequent response as `refetch` and wedge permanently — the report
  could never render again without a page reload, violating AC 13.

  The fix must not weaken the guard. Rendering the response after N retries would apply data
  `classifyReport` has already ruled stale, breaking AC 11 outright and lowering the known
  revision in violation of `nextRevision`'s monotonic rule. Instead the client calls
  `resyncRevision()`: it reads `overview`, which is **never delayed and therefore authoritative**.
  If that fresh read also reports a lower revision, the dataset really was reset — the client
  adopts *that* revision (the sole sanctioned backwards move), refreshes users/overview, notes
  that the server appears to have restarted, and re-requests the report. If the fresh read does
  not confirm a regression, the report is left untouched and an actionable error is shown.

  So the only value that can lower the known revision comes from an undelayed authoritative
  endpoint, never from a funnel response that lost a race.

  *The wedge was found during the manual browser pass; the first fix for it — adopting the stale
  response — was caught in review. Both are recorded here because the second mistake is more
  instructive than the first.*

### Exclusion / inclusion (AC 13)

```js
const result = await api.setExclusion(userId, true, reason);
applyRevision(result.revision);   // BEFORE any await — closes the stale window
await refresh();                  // overview + users
await loadReport();               // reconcile the visible report
```

Applying the PATCH response's revision *before* awaiting `refresh()` is the fix identified in
review: today the client only learns the new revision once `refresh()` resolves, leaving a window
in which an in-flight funnel response looks current. Stamping it first means any response
computed before the exclusion is already classifiable as `refetch`.

### Segment change (AC 12)

```js
store.set({ selectedSegment: value });
loadReport();     // increments latestRequestId, so the previous response is discarded
```

The user table filters client-side from `state.users` as it does today — unchanged.

### Initial load

`refresh()` then `loadReport()`, so the report renders against a known revision rather than `0`.

---

## 5. UI side effects to get right (Phase 5)

`render()` replaces `app.innerHTML` wholesale on every state change. That is fine for a table of
eight rows but has three consequences this feature must handle deliberately:

1. **Focus loss.** Any state change while typing destroys the focused element. So the delay input
   commits on `change` (blur/Enter), never `input` — matching how the existing segment `select`
   behaves. Typing a delay therefore does not re-render mid-keystroke.
2. **Exclusion buttons must stay enabled while a report is in flight.** AC 13's whole scenario is
   excluding *during* a slow report. Only the "Run report" button is disabled by `reportLoading`;
   the existing `Refresh` button keeps its current `loading` binding.
3. **No new user-controlled interpolation.** The report body contains only server-validated
   strings (`segment`, `experiment`, fixed step names) and numbers, so it introduces no new
   injection surface. The pre-existing `exclusion_reason` interpolation is untouched and out of
   scope.

---

## 6. The analysis section (Phase 5)

Replaces the `.placeholder` block. Rendered independently of the user table so a report error
never disturbs it.

```
Analysis                                    [segment: enterprise · revision 4 · updating…]
[ test delay (ms): 3000 ]  [ Run report ]
⚠ invalid_segment — showing the last successful report        ← only when reportError
┌──────────┬──────────┬───────────────┬──────────────────┬───────────────────┐
│ Variant  │ Eligible │ product_viewed│ checkout_started │ order_completed   │
├──────────┼──────────┼───────────────┼──────────────────┼───────────────────┤
│ control  │ 4        │ 4 (100.0%)    │ 4 (100.0%)       │ 2 (50.0%)         │
│ treatment│ 4        │ 4 (100.0%)    │ 4 (100.0%)       │ 3 (75.0%)         │
└──────────┴──────────┴───────────────┴──────────────────┴───────────────────┘
Rates use the previous step as denominator. Report computed at revision 4.
```

- **The meta line is read from `report`, never from current state.** After an exclusion or a
  segment change the previous report stays on screen until the new one lands, which is the right
  behaviour — but only if it is honestly labelled. So the header renders
  `report.segment` / `report.revision` (the response's own fields), *not*
  `state.selectedSegment` / `state.revision`. Rendering the selected segment beside an older
  report's numbers would actively mislabel stale data, which is worse than not labelling it at
  all. Same for the revision.
- **Divergence is shown, not hidden.** When `report.revision !== state.revision` or
  `report.segment !== state.selectedSegment`, the meta line reads e.g.
  `enterprise · revision 3 · updating to revision 4…`, so a reader can see at a glance that what
  they are looking at is not yet the current dataset. Combined with `reportLoading`, the
  transient old-report window is legible rather than misleading.
- **Columns come from `report.steps`**, not a hardcoded list, so the backend stays the single
  source of funnel semantics.
- **`null` rates render as `—`**, never `NaN`, `null` or `0.0%`.
- **Rates are printed with `toFixed(1)`** so `50` shows as `50.0%`; the backend already rounded to
  one decimal, and `toFixed` here is presentation only — it never re-rounds a value the backend
  did not already round.
- **Revision is always visible**, because the entire staleness story is invisible otherwise. A
  reviewer exercising AC 11 needs to see the number change.
- **Before the first successful report**: a plain "No report yet" line, not an empty table.
- **Error banner** sits above the table and says what failed plus that the table below is the last
  successful report — actionable, not just red text (AC 14).

`web/styles.css` gains only what the existing sheet lacks: a `.report-meta` muted line, a
`.report-error` banner, and reuse of the existing `table` styling.

---

## 7. Test plan

### `test/reportGuards.test.js` (new, ~9 tests)

1. Newest request, matching segment, equal revision → `apply`.
2. Response revision **greater** than known (nobody else moved) → `apply`.
3. Superseded request id → `discard`, even when segment and revision are fine.
4. Superseded request id **and** a stale revision → `discard`, not `refetch` — proves check order.
5. Segment mismatch on the newest request → `discard` (AC 12).
6. Response revision below known revision → `refetch` (AC 11).
7. Segment mismatch *and* stale revision → `discard` — segment check precedes the revision check.
8. `nextRevision` returns the max, ignores `null`/`undefined`/`NaN`, and never decreases.
9. **Regression for the ordering trap:** feeding a response through `nextRevision` first and then
   `classifyReport` yields `apply` where the correct order yields `refetch`. Written as an explicit
   assertion that the correct order is used, so the failure mode is documented in the suite.

### `e2e/funnel.e2e.js` (new, 7 tests) — `npm run e2e`

Driving a real browser with Playwright, so the race behaviour is verified reproducibly instead of
by hand. Kept out of `npm test`: the file sits outside `test/` and does not match Node's
discovery patterns, and Playwright is resolved from a global install rather than added to
`package.json`, so the graded suite stays dependency-free. The suite skips cleanly with
`# playwright not installed` where it is absent, and falls back to an installed Google Chrome
rather than downloading a browser build. Both servers are started and torn down by the suite
itself on non-default ports (3101/5273), so it never collides with a running dev server.

**The two race tests must make the old request finish LAST.** This is the entire point of AC 11
("a slow older request finishing last"), and getting it wrong produces a test that cannot fail:
give both requests the same delay and the stale response lands *first*, at a moment when its
content is identical to what is already on screen — indistinguishable from correct behaviour.
So each race test starts a 5s request, then drops the delay to 0 before triggering the
reconciling one, and asserts the screen is unchanged after the slow response finally lands.

Verified by mutation: with both staleness guards disabled, the first version of these tests
passed and the rewritten ones fail. Note that disabling the request-id check *alone* still
passes — checks 1 and 3 are genuinely redundant for these scenarios, which is the defence in
depth the design intends, not a gap in coverage.

### Manual browser verification (Phases 4–5)

The e2e suite covers these; the table is retained as the scenario definition and for reviewing
visual details (spacing, colour, wording) that assertions do not capture:

| Scenario | Steps | Expected |
| --- | --- | --- |
| Happy path (AC 1, 7) | load page | report renders, counts match the fixture oracle, rates one decimal |
| Segment filter (AC 2) | switch to `enterprise` | treatment shows `2/2/2/2`, revision unchanged |
| Stale exclusion (AC 11, 13) | delay 3000 → Run report → immediately exclude `u-102` | during the wait the old report stays visible but is labelled with **its own** revision plus "updating to revision N…"; the slow response never lands; the visible report ends at the new revision with `u-102` gone |
| Segment race (AC 12) | delay 3000 → Run report on `all` → switch to `enterprise` | during the wait the visible report is still labelled `all`, never `enterprise`; the `all` response never overwrites the enterprise report |
| Failure (AC 14) | stop the API server → Run report | error banner appears, previous table still visible; restart → Run report recovers |
| Existing behavior (AC 15) | exclude/include with an empty reason | validation message still shown, user table still updates |
| Server restart | exclude a user, then restart the API and run the report | the report renders at the server's reset revision with a "server appears to have restarted" notice — it must **not** wedge on endless refetches |

This script goes in the phase 5 commit message and is re-run before the final commit.

---

## 8. Risks

| Risk | Mitigation |
| --- | --- |
| Revision folded in before the staleness comparison, silently disabling the guard | `classifyReport` takes `knownRevision` as an argument and `applyRevision` is called only on `apply`; test 9 |
| A discarded response clearing `reportLoading`, flickering the UI | `discard` returns early; the owning request clears it |
| A superseded *failure* painting an error over a newer good report | `requestId` re-checked inside `catch` |
| Exclusion buttons disabled during a slow report, making AC 13 unreachable | only "Run report" binds to `reportLoading` |
| Delay input re-rendering on every keystroke | commits on `change`, not `input` |
| Report cleared on error | `store.set` in `catch` never touches `report`; manual scenario 5 |
| Meta line labelling an old report with the newly selected segment/revision, mislabelling stale data as current | header reads `report.segment`/`report.revision`, and divergence from current state is shown as "updating to…"; manual scenarios 3 and 4 check the label during the in-flight window |

---

## 9. Exit criteria

- `npm test` green: 41 existing + 9 new = **50 tests**, all Phase 1–3 tests unmodified.
- `npm run e2e` green: **7 Playwright tests**, and mutation-checked — the race tests must be seen
  to fail with the staleness guards disabled.
- `npm run build` green at **10 modules** (`web/reportGuards.js` added to the list).
- `git diff` touches only the files listed at the top; nothing under `src/` changes.
