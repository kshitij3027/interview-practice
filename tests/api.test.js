import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createServer } from '../src/server.js';

async function withServer(fn) {
  const server = createServer();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  try { await fn(`http://127.0.0.1:${server.address().port}`); }
  finally { await new Promise((resolve) => server.close(resolve)); }
}

test('health endpoint and browser shell are served', async () => withServer(async (base) => {
  const health = await fetch(`${base}/health`);
  assert.equal(health.status, 200);
  assert.deepEqual(await health.json(), { ok: true });
  const page = await fetch(base);
  assert.equal(page.status, 200);
  assert.match(await page.text(), /ShiftPay/);
  assert.match(await (await fetch(`${base}/app.js`)).text(), /loadDetail/);
}));

test('list/detail note flow remains consistent through HTTP', async () => withServer(async (base) => {
  const before = await (await fetch(`${base}/api/shifts?employeeId=emp-23`)).json();
  assert.equal(before.shifts.length, 2);
  const note = await fetch(`${base}/api/shifts/sh-309/note`, {
    method: 'PATCH', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ note: ' Test pass ', expectedRevision: 2 }),
  });
  assert.equal(note.status, 200);
  const result = await note.json();
  assert.equal(result.shift.note, 'Test pass');
  assert.equal(result.shift.revision, 3);
  const after = await (await fetch(`${base}/api/shifts/sh-309`)).json();
  assert.equal(after.shift.note, 'Test pass');
}));

test('bad JSON, missing shift, and stale mutation have structured errors', async () => withServer(async (base) => {
  const bad = await fetch(`${base}/api/shifts/sh-301/note`, { method: 'PATCH', body: '{bad' });
  assert.equal(bad.status, 400);
  assert.equal((await bad.json()).error.code, 'invalid_json');
  const absent = await fetch(`${base}/api/shifts/missing`);
  assert.equal(absent.status, 404);
  const conflict = await fetch(`${base}/api/shifts/sh-301/note`, {
    method: 'PATCH', body: JSON.stringify({ note: 'New', expectedRevision: 0 }),
  });
  assert.equal(conflict.status, 409);
  assert.equal((await conflict.json()).error.currentRevision, 2);
}));
