# Phase 3 — HTTP route (`GET /api/funnel`) with a bounded test delay

Goal: expose `ExperimentService.funnel()` over HTTP, and add the bounded `delay_ms` knob that
makes stale-response behaviour reproducible locally (AC 1, AC 10). Still no frontend work —
Phase 4 consumes this endpoint.

Files touched:

| File | Change |
| --- | --- |
| `src/routes.js` | new `GET /api/funnel` branch; exported `parseDelayMs`; local `sleep` |
| `test/routes.test.js` | endpoint contract, validation, delay clamping, staleness ordering |

Not touched: `src/funnel.js`, `src/experimentService.js`, `src/dataStore.js` (Phases 1–2 are
frozen), `src/http.js`, `server.js`, everything under `web/`. No new module, so
`scripts/verify-build.js` stays at 9 modules.

---

## 1. Endpoint contract

```
GET /api/funnel?segment=<all|self-serve|enterprise>&delay_ms=<0..5000>
```

| Case | Status | Body |
| --- | --- | --- |
| valid (or omitted) segment | 200 | the `funnel()` response, minus the internal `ok` flag |
| unknown segment | 400 | `{ "error": "invalid_segment" }` |
| any `delay_ms` value | never errors | parsed, clamped, or ignored — see §3 |
| `POST`/`PUT` on the path | 404 | `{ "error": "not_found" }` |

Both query parameters are optional: `?` with nothing, `?segment=all`, and no query string at all
must all behave identically.

### Wiring in `src/routes.js`

Matching stays hand-rolled and in the existing style — a `req.method` + `url.pathname` check
placed alongside the `/api/overview` and `/api/users` branches, before the exclusion regex:

```js
if (req.method === 'GET' && url.pathname === '/api/funnel') {
  const result = service.funnel({ segment: url.searchParams.get('segment') ?? 'all' });
  if (!result.ok) return sendJson(res, 400, { error: result.code });
  const { ok, ...body } = result;
  await sleep(parseDelayMs(url.searchParams.get('delay_ms')));
  return sendJson(res, 200, body);
}
```

Notes:

- `searchParams.get()` returns `null` when absent, hence the `?? 'all'` — Phase 2 already
  accepts `undefined`/`null` and defaults, so this is belt-and-braces rather than required.
- The `ok` flag is a service-internal discriminator and is stripped from the wire response; the
  HTTP status already carries success/failure. `revision`, `segment`, `steps`, `eligible_total`
  and `variants` go out as-is.
- `400` for an unknown segment matches how the exclusion route reports validation failures
  (`invalid_reason` → 400), so the client sees one error convention.

---

## 2. Ordering: compute → sleep → respond

**This is the load-bearing detail of Phase 3.** The delay is applied *after* `service.funnel()`
has already computed and stamped its revision, not before.

- Sleeping **before** computing would produce a slow but *fresh* response — it would read the
  dataset as it exists after the delay, so an exclusion made during the wait would already be
  reflected. That is useless for testing AC 11.
- Sleeping **after** computing produces a genuinely stale response: it carries the revision and
  numbers from *before* the exclusion, and arrives after the client has already learned about a
  newer revision. That is precisely the condition the Phase 4 guard must survive.

Concretely, with a 3s delay: request the report → exclude a user 0.5s later → 2.5s after that,
a response arrives claiming `revision: 1` and still counting the excluded user. The backend is
*correct* to send it (it answers the dataset as of when it was asked); the client must not
render it.

`sleep` is a local helper in `routes.js`:

```js
const sleep = ms => (ms > 0 ? new Promise(resolve => setTimeout(resolve, ms)) : Promise.resolve());
```

Zero-delay requests take no timer detour, so the common path is unchanged. `handler` is already
`async`, so no signature change is needed.

---

## 3. `delay_ms` parsing

```js
export const MAX_DELAY_MS = 5000;

export function parseDelayMs(raw) {
  const value = Number(raw);
  if (!Number.isFinite(value) || value <= 0) return 0;
  return Math.min(Math.trunc(value), MAX_DELAY_MS);
}
```

Rules, all of which fail *safe* rather than erroring (AC 10 asks for a bounded knob, not a
validated API surface — a malformed debug parameter must never break the report):

| Input | Result | Why |
| --- | --- | --- |
| `null` (absent), `''` | `0` | `Number(null)` is `0`, `Number('')` is `0` |
| `'250'` | `250` | ordinary case |
| `'250.9'` | `250` | truncated to an integer |
| `'abc'`, `'50abc'` | `0` | `Number()` yields `NaN` — deliberately stricter than `parseInt`, which would read `'50abc'` as `50` |
| `'-100'` | `0` | negatives clamp to zero |
| `'99999'` | `5000` | bounded so a stray parameter cannot pin a connection open |
| `'Infinity'`, `'NaN'` | `0` | non-finite is malformed input, and malformed input means no delay — **not** the ceiling. `Number.isFinite(Infinity)` is `false`, so the guard catches it before the clamp |

**Why `parseDelayMs` is exported.** Testing the 5000ms ceiling end-to-end would mean a 5-second
test. Exporting the pure function lets the clamping rules be asserted instantly in a unit test,
while one small integration test (`delay_ms=120`) proves the value is actually honoured by the
route. This keeps the suite fast without leaving the bound untested.

---

## 4. Test plan — `test/routes.test.js`

The file's existing `withServer` helper is reused unchanged. One addition is needed: the current
helper builds its own `DataStore`/`ExperimentService` internally, so a test cannot reach the
service to mutate state mid-request. It gains an optional second argument exposing the service
(`fn(base, service)`) — a strictly additive change; the two existing tests keep working
untouched.

1. **Report contract.** `GET /api/funnel` → 200; body has `revision: 1`, `segment: 'all'`,
   `experiment: 'checkout-copy'`, the three-name `steps` array, `eligible_total: 8`, and the
   oracle counts (control `4/4/4/2`, treatment `4/4/4/3`). Assert `ok` is **absent** from the
   wire body.
2. **Segment parameter.** `?segment=enterprise` → 200 with `segment: 'enterprise'` and
   `eligible_total: 4`; treatment shows `order_completed: 2`.
3. **Omitted vs explicit `all`.** No query string deep-equals `?segment=all`.
4. **Invalid segment.** `?segment=whales` → 400, `{ error: 'invalid_segment' }`.
5. **Delay parsing (unit, on the exported function).** The whole table in §3, in one test. No
   HTTP, no timers.
6. **Delay is honoured (integration).** `?delay_ms=120` → 200, and measured elapsed time is
   `>= 100`. A loose lower bound, since timers only guarantee "not early"; asserting an upper
   bound would make the test flaky on a loaded machine.
7. **Malformed delay does not break the report.** `?delay_ms=abc` → 200 with a body deep-equal
   to the no-delay response.
8. **A delayed response is genuinely stale — the ordering proof.** Assert that a response
   returned after an exclusion still carries `revision: 1` and still counts `u-102`
   (treatment `4/4/4/3`), while a fresh request immediately afterwards returns `revision: 2` and
   treatment `3/3/3/2`.

   **The exclusion must not run until the handler has started.** Creating a `fetch` promise does
   not mean the server handler has run yet — Node may not have scheduled it. If the exclusion
   lands first, the delayed response legitimately carries `revision: 2` and the test fails for a
   reason unrelated to the ordering under test. So the test needs an explicit synchronisation
   point rather than an assumption about scheduling.

   The synchronisation point is the **server's `request` event**, not `funnel()` being called:

   ```js
   const requestStarted = new Promise(resolve => server.once('request', resolve));

   const inFlight = fetch(`${base}/api/funnel?delay_ms=200`);
   await requestStarted;
   service.setExclusion('u-102', true, 'internal QA');
   const stale = await (await inFlight).json();
   ```

   `createHandler` is registered as the first `request` listener and listeners run in order, so
   by the time this one fires the handler has already run synchronously up to its first `await`.
   Under the correct ordering that means the snapshot is taken and the revision stamped, so the
   exclusion is unambiguously later — race-free.

   **Why not synchronise on `funnel()` itself.** Wrapping `service.funnel` and resolving when it
   is called looks like the tighter guarantee, but it makes the test *tautological*: it waits for
   the computation under either ordering, so a route that slept before computing would still see
   the exclusion land after the compute, and the test could never fail. Verified by mutation —
   with a `funnel()` spy the inverted route passes; with the `request` event it fails, because
   the handler yields at the sleep, the listener fires immediately, and the exclusion lands
   before the computation.

   **This test fails if the delay is ever moved before the computation** — the response would
   come back with `revision: 2`. It is the regression guard for §2 and the fixture that Phase 4's
   client guard is written against.
9. **Unknown methods and paths still 404.** `POST /api/funnel` → 404, so the new branch does not
   loosen method matching.
10. **Existing endpoints unaffected.** The two current tests must pass unmodified (AC 15).

Test 8 costs ~200ms and contains no sleeping of its own: the ordering is established by the
`request` event, not by timing. It needs both the service (to mutate mid-flight) and the server
(to synchronise on), which is why `withServer` now passes `fn(base, service, server)`.

**Test 8 must be mutation-checked, not merely observed to pass.** Invert the route to sleep
before computing and confirm the test goes red; restore and confirm it goes green. A guard for a
race is worthless unless it has been seen to fail.

---

## 5. Risks and how the tests catch them

| Risk | Caught by |
| --- | --- |
| Delay applied before computing, making delayed responses fresh and AC 11 untestable | test 8 |
| Unbounded `delay_ms` pinning a connection open | test 5 (ceiling) |
| `parseInt` silently accepting `'50abc'` as 50 | test 5 |
| Non-finite input reaching the clamp and becoming a 5s delay instead of none | test 5 (`'Infinity'` → `0`) |
| A malformed debug parameter breaking the report entirely | test 7 |
| Leaking the internal `ok` flag onto the wire | test 1 |
| New branch loosening method matching for other routes | test 9 |

---

## 6. Exit criteria

- `npm test` green: 34 existing + ~8 new = **~42 tests**, with all Phase 1–2 tests unmodified.
- `npm run build` green, still 9 modules.
- Suite runtime stays well under a second aside from the two deliberate sub-300ms delay tests.
- `git diff` touches only `src/routes.js` and `test/routes.test.js`.
- Manual check: `npm start`, then
  `curl 'localhost:3001/api/funnel?segment=enterprise&delay_ms=1000'` returns after ~1s with the
  expected body.

Phase 4 then consumes this endpoint from the browser, using `revision` and the echoed `segment`
to discard stale responses.
