# Implementation notes — funnel report

Companion to `README.md` (which is the exercise specification and is unmodified). This file
records the semantics the spec asks to be documented, the decisions behind them, and how to run
everything.

---

## Funnel semantics

The backend is the source of truth. All of the rules below live in `src/funnel.js`.

**Steps.** The fixed three-step funnel `product_viewed → checkout_started → order_completed`.

**Eligibility.** A user counts only if assigned to `checkout-copy`, not excluded, and matching the
requested segment. An event counts only if `occurred_at >= assigned_at` for that user. Events for
users with no assignment (`u-999` in the fixture) are ignored entirely.

**Duplicate `event_id`s.** Only one occurrence of a repeated `event_id` may influence the report.
The winner is the occurrence that sorts first by:

1. `occurred_at` ascending (unparseable timestamps sort last), then
2. the stable JSON of the payload, with object keys sorted recursively.

**File position is never a tiebreak.** A "first row in the file wins" rule would make the winner
depend on JSONL ordering the moment two duplicates disagree, and results must be identical under
any permutation of the input. Both sort keys are total and derived from content alone. The two
`e-09` rows in the fixture are byte-identical, so they cannot detect a file-order-dependent rule —
the tests use synthetic duplicates that differ in timestamp and in payload.

**Ordering.** Each user's qualifying events are sorted by `(occurred_at, event_id)`; `event_id` is
the tiebreak so identical timestamps resolve deterministically. Steps are then selected by
timestamp comparison rather than array position, so "at or after" correctly admits equal times.

**Selection is greedy-earliest, and that is optimal rather than merely convenient.** The 24h
anchor is fixed by the spec (below), so choosing the smallest valid `checkout_started` maximally
relaxes the constraint on `order_completed`, and the smallest valid `order_completed` is the one
most likely to land inside the window. No backtracking is needed: if the earliest valid completion
misses the window, every later one misses it too.

This also yields "repeated step events may be used if an earlier occurrence cannot form a valid
ordered path" for free — an out-of-order occurrence is simply never selected (`u-103`'s completion
precedes its checkout), and a later repeat is picked when the earlier one is ineligible (`u-105`'s
first view predates assignment).

**24-hour window.** The path must complete within 24h of the user's **first qualifying**
`product_viewed`. Later `product_viewed` events do **not** re-anchor or reset the window. The
boundary is inclusive: exactly 24h counts, one millisecond later does not.

**Rates.** Each step's percentage uses the immediately preceding step as denominator; the first
uses eligible users. A zero denominator yields `null`, never `NaN` or `Infinity`, and renders as
`—`. Rounding is half-up to one decimal, applied identically to every rate. Counts stay integers.

**Variants** come from the assignment set, so a variant with zero eligible users still appears with
zeroed counts rather than vanishing from the report.

---

## Race handling

Every funnel response carries the `revision` it was computed from, taken from the same
`DataStore.snapshot()` as the data, so the stamp always describes the payload.

`GET /api/funnel` **computes first and sleeps afterwards**. Sleeping before computing would return
a slow but *fresh* response, which cannot exercise stale-response handling at all.

The client (`web/reportGuards.js`) classifies each response in this order:

1. `requestId !== latestRequestId` → **discard**. A newer request has been issued.
2. `responseSegment !== selectedSegment` → **discard**. Server-reported truth; deliberately
   redundant with (1) so a bug in the request counter cannot render one segment's numbers under
   another's label.
3. `responseRevision < knownRevision` → **refetch**. Computed before a change the client knows
   about; discarding alone would leave stale numbers on screen.
4. otherwise → **apply**.

**`classifyReport` must run before the response's revision is folded into the known revision.**
Fold first and `responseRevision < knownRevision` becomes unsatisfiable — the guard silently
disables itself while every other test still passes.

**Monotonic revision, with exactly one sanctioned exception.** The known revision never moves
backwards from a funnel response. But restarting the API resets the revision counter to 1
(documented existing behaviour), which would otherwise wedge the client permanently: every
response would classify as `refetch` and the report could never render again without a page
reload. So on exhausting the retry bound the client calls `resyncRevision()`, which reads
`overview` — never delayed, therefore authoritative. Only if *that* fresh read also reports a lower
revision does the client conclude the dataset was reset and adopt its revision. A stale funnel
response is never rendered, whatever the retry count.

**The report label is read from the response, not from current state.** After an exclusion or a
segment change the previous report stays visible until the new one lands; the meta line therefore
shows that report's own `segment` and `revision`, plus where it is heading
(`revision 1 · updating to revision 2…`). Labelling an old report with the newly selected segment
would mislabel stale data as current, which is worse than not labelling it.

---

## Running

```bash
npm start                          # API on :3001
python3 -m http.server 5173 -d web # static frontend, second terminal
npm test                           # 51 unit/integration tests (node:test, no dependencies)
npm run build                      # syntax-check every shipped module
npm run e2e                        # 10 Playwright browser tests
```

`npm run e2e` is deliberately **not** part of `npm test`: it lives outside `test/`, does not match
Node's test-discovery patterns, and Playwright is resolved from a global install rather than added
to `package.json`, so the graded suite stays dependency-free. It skips cleanly with
`# playwright not installed` where Playwright is absent, falls back to an installed Google Chrome
rather than downloading a browser build, and starts its own API and static servers on ports
3101/5273 so it never collides with a running dev server. Each test restarts the API and reloads
the page, so tests are independent and can be run individually.

**The race guards are mutation-checked, not merely observed to pass.** Disabling a guard must turn
a specific test red:

| Mutation | Test that must fail |
| --- | --- |
| route sleeps before computing | `a delayed report is computed before the delay…` (`test/routes.test.js`) |
| request-id + revision checks disabled | `a slow older report finishing last…`, `a stale response on the newest request refetches…`, `a server restart is resynced…` |
| request-id + segment checks disabled | `a slow report for the previous segment finishing last…` |

Note that disabling any *single* guard leaves the suite green: checks 1–3 are genuinely redundant
for these scenarios, which is the intended defence in depth rather than a coverage gap.

---

## Known limitations

- No persistence. All state is in memory and resets on restart, including exclusions and the
  revision counter (see the resync path above).
- The funnel is fixed at three steps; arbitrary configurable funnels are out of scope.
- Percentages carry no confidence intervals or significance testing.
- `delay_ms` is a local testing knob only, clamped to 0–5000ms.
