import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createApp } from '../src/server.js';

async function start() {
  const server = createApp();
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  return { server, url: `http://127.0.0.1:${server.address().port}` };
}

test('healthy app serves browser and filtered API', async (t) => {
  const { server, url } = await start();
  t.after(() => server.close());
  assert.deepEqual(await (await fetch(`${url}/api/health`)).json(), { ok: true });
  const html = await (await fetch(url)).text();
  assert.match(html, /ReturnCredit/);
  const list = await (await fetch(`${url}/api/orders?status=cancelled`)).json();
  assert.deepEqual(list.orders.map((o) => o.id), ['ORD-204']);
});

test('note API returns current revision and does not change on stale write', async (t) => {
  const { server, url } = await start(); t.after(() => server.close());
  const api = (revision, note) => fetch(`${url}/api/orders/ORD-205/note`, { method: 'PATCH', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ expectedRevision: revision, note }) });
  assert.equal((await api(5, '  Reviewed  ')).status, 200);
  const stale = await api(5, 'Overwrite');
  assert.equal(stale.status, 409);
  assert.equal((await stale.json()).currentRevision, 6);
  assert.equal((await (await fetch(`${url}/api/orders/ORD-205`)).json()).order.note, 'Reviewed');
});
