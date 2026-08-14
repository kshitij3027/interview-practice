import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { DataStore } from '../src/dataStore.js';
import { ExperimentService } from '../src/experimentService.js';
import { createHandler } from '../src/routes.js';

async function withServer(fn) {
  const server = http.createServer(createHandler(new ExperimentService(new DataStore())));
  await new Promise(resolve => server.listen(0, resolve));
  const { port } = server.address();
  try { await fn(`http://127.0.0.1:${port}`); } finally { await new Promise(resolve => server.close(resolve)); }
}

test('GET /api/users exposes current dataset revision', async () => withServer(async base => {
  const response = await fetch(`${base}/api/users`);
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.revision, 1);
  assert.equal(body.users.length, 8);
}));

test('PATCH exclusion validates and mutates existing behavior', async () => withServer(async base => {
  const response = await fetch(`${base}/api/users/u-102/exclusion`, { method: 'PATCH', headers: {'content-type':'application/json'}, body: JSON.stringify({ excluded: true, reason: 'test account' }) });
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.revision, 2);
}));
