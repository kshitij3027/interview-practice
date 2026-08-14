import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { DataStore } from '../src/dataStore.js';
import { ExperimentService } from '../src/experimentService.js';
import { createHandler, MAX_DELAY_MS, parseDelayMs } from '../src/routes.js';

// `fn` also receives the service and the server, so a test can mutate the dataset while a
// request is in flight and synchronise on the server's own 'request' event.
async function withServer(fn) {
  const service = new ExperimentService(new DataStore());
  const server = http.createServer(createHandler(service));
  await new Promise(resolve => server.listen(0, resolve));
  const { port } = server.address();
  try { await fn(`http://127.0.0.1:${port}`, service, server); } finally { await new Promise(resolve => server.close(resolve)); }
}

const getJson = async (base, path) => {
  const response = await fetch(`${base}${path}`);
  return { status: response.status, body: await response.json() };
};

test('GET /api/users exposes current dataset revision', async () => withServer(async base => {
  const response = await fetch(`${base}/api/users`);
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.revision, 1);
  assert.equal(body.users.length, 8);
}));

test('GET /api/funnel returns the report stamped with its dataset revision', async () => withServer(async base => {
  const { status, body } = await getJson(base, '/api/funnel');
  assert.equal(status, 200);
  assert.equal(body.experiment, 'checkout-copy');
  assert.equal(body.revision, 1);
  assert.equal(body.segment, 'all');
  assert.deepEqual(body.steps, ['product_viewed', 'checkout_started', 'order_completed']);
  assert.equal(body.eligible_total, 8);
  assert.deepEqual(body.variants.control.steps, { product_viewed: 4, checkout_started: 4, order_completed: 2 });
  assert.deepEqual(body.variants.treatment.steps, { product_viewed: 4, checkout_started: 4, order_completed: 3 });
  // The `ok` discriminator is a service-internal detail; the HTTP status carries success.
  assert.equal('ok' in body, false);
}));

test('GET /api/funnel filters by segment and defaults to all', async () => withServer(async base => {
  const enterprise = await getJson(base, '/api/funnel?segment=enterprise');
  assert.equal(enterprise.status, 200);
  assert.equal(enterprise.body.segment, 'enterprise');
  assert.equal(enterprise.body.eligible_total, 4);
  assert.equal(enterprise.body.variants.treatment.steps.order_completed, 2);

  const omitted = await getJson(base, '/api/funnel');
  const explicit = await getJson(base, '/api/funnel?segment=all');
  assert.deepEqual(omitted.body, explicit.body);
}));

test('GET /api/funnel rejects an unknown segment', async () => withServer(async base => {
  const { status, body } = await getJson(base, '/api/funnel?segment=whales');
  assert.equal(status, 400);
  assert.deepEqual(body, { error: 'invalid_segment' });
}));

test('parseDelayMs bounds the delay and fails safe on malformed input', () => {
  assert.equal(parseDelayMs(null), 0);
  assert.equal(parseDelayMs(''), 0);
  assert.equal(parseDelayMs('250'), 250);
  assert.equal(parseDelayMs('250.9'), 250);
  assert.equal(parseDelayMs('abc'), 0);
  assert.equal(parseDelayMs('50abc'), 0); // stricter than parseInt, which would read 50
  assert.equal(parseDelayMs('-100'), 0);
  assert.equal(parseDelayMs('99999'), MAX_DELAY_MS);
  // Non-finite is malformed input, so no delay at all — not the ceiling.
  assert.equal(parseDelayMs('Infinity'), 0);
  assert.equal(parseDelayMs('NaN'), 0);
});

test('GET /api/funnel honours a delay and ignores a malformed one', async () => withServer(async base => {
  const startedAt = process.hrtime.bigint();
  const delayed = await getJson(base, '/api/funnel?delay_ms=120');
  const elapsedMs = Number(process.hrtime.bigint() - startedAt) / 1e6;
  assert.equal(delayed.status, 200);
  // Lower bound only: timers guarantee "not early", never "not late".
  assert.ok(elapsedMs >= 100, `expected at least 100ms, got ${elapsedMs}`);

  const malformed = await getJson(base, '/api/funnel?delay_ms=abc');
  assert.equal(malformed.status, 200);
  assert.deepEqual(malformed.body, (await getJson(base, '/api/funnel')).body);
}));

test('the delay ceiling reaches the transport, not just the parser', async () => withServer(async base => {
  // parseDelayMs('99999') === 5000 is unit-tested, but a route that passed the raw value
  // through would still satisfy that test and this endpoint would hang for 99 seconds.
  const startedAt = process.hrtime.bigint();
  const { status } = await getJson(base, '/api/funnel?delay_ms=99999');
  const elapsedMs = Number(process.hrtime.bigint() - startedAt) / 1e6;
  assert.equal(status, 200);
  assert.ok(elapsedMs < 10000, `expected the clamp to cap the wait, took ${Math.round(elapsedMs)}ms`);
  assert.ok(elapsedMs >= 4900, `expected roughly the 5s ceiling, took ${Math.round(elapsedMs)}ms`);
}));

test('a delayed report is computed before the delay, so it comes back stale', async () => withServer(async (base, service, server) => {
  // Synchronising on the server's 'request' event, not on funnel() itself. The handler is
  // already registered as the first 'request' listener, and listeners run in order, so by the
  // time this one fires the handler has run synchronously up to its first await. That is
  // race-free *and* discriminating: if the route ever slept before computing, the handler
  // would yield at the sleep, this listener would fire immediately, and the exclusion below
  // would land before the computation — flipping the assertions to revision 2.
  // (Synchronising on funnel() being called would instead make this test tautological: it
  // would wait for the computation under either ordering and could never fail.)
  const requestStarted = new Promise(resolve => server.once('request', resolve));

  const inFlight = fetch(`${base}/api/funnel?delay_ms=200`);
  await requestStarted;
  service.setExclusion('u-102', true, 'internal QA');
  const stale = await (await inFlight).json();

  // The slow response answers the dataset as of when it was asked — the server is right to
  // send it, and the client is the one that must not render it over newer state.
  assert.equal(stale.revision, 1);
  assert.deepEqual(stale.variants.treatment.steps, { product_viewed: 4, checkout_started: 4, order_completed: 3 });

  const fresh = await getJson(base, '/api/funnel');
  assert.equal(fresh.body.revision, 2);
  assert.deepEqual(fresh.body.variants.treatment.steps, { product_viewed: 3, checkout_started: 3, order_completed: 2 });
}));

test('the funnel route does not loosen method or path matching', async () => withServer(async base => {
  const posted = await fetch(`${base}/api/funnel`, { method: 'POST' });
  assert.equal(posted.status, 404);
  const nested = await fetch(`${base}/api/funnel/extra`);
  assert.equal(nested.status, 404);
}));

test('PATCH exclusion validates and mutates existing behavior', async () => withServer(async base => {
  const response = await fetch(`${base}/api/users/u-102/exclusion`, { method: 'PATCH', headers: {'content-type':'application/json'}, body: JSON.stringify({ excluded: true, reason: 'test account' }) });
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.revision, 2);
}));
