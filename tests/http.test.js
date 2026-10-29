import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createApp } from '../src/server.js';

async function withServer(run) {
  const { server } = createApp();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  try { await run(`http://127.0.0.1:${server.address().port}`); }
  finally { await new Promise((resolve, reject) => server.close(e => e ? reject(e) : resolve())); }
}

test('HTTP catalog, detail and static UI are working', async () => withServer(async base => {
  const list = await fetch(`${base}/api/assets?studio=atlas&status=ready`);
  assert.equal(list.status, 200);
  assert.equal((await list.json()).total, 2);
  const other = await fetch(`${base}/api/assets/C-201?studio=atlas`);
  assert.equal(other.status, 404);
  const page = await fetch(base);
  assert.equal(page.status, 200);
  assert.match(await page.text(), /CaptionGate/);
}));

test('HTTP note conflict, no-op and preservation of captions', async () => withServer(async base => {
  const url = `${base}/api/assets/A-101/note?studio=atlas`;
  const patch = body => fetch(url, { method:'PATCH', headers:{'content-type':'application/json'}, body:JSON.stringify(body) });
  const changed = await patch({ note:' Translation reviewed ', expectedRevision:3 });
  assert.equal(changed.status, 200);
  assert.equal((await changed.json()).asset.revision, 4);
  const stale = await patch({ note:' overwritten ', expectedRevision:3 });
  assert.equal(stale.status, 409);
  assert.equal((await stale.json()).error.code, 'STALE_REVISION');
  const unchanged = await patch({ note:'Translation reviewed', expectedRevision:4 });
  assert.equal((await unchanged.json()).datasetRevision, 43);
  const detail = await (await fetch(`${base}/api/assets/A-101?studio=atlas`)).json();
  assert.equal(detail.asset.captions['en-US'].length, 2);
}));

test('HTTP invalid query is structured 400', async () => withServer(async base => {
  const response = await fetch(`${base}/api/assets?studio=atlas&limit=abc`);
  assert.equal(response.status, 400);
  assert.equal((await response.json()).error.code, 'INVALID_LIMIT');
}));
