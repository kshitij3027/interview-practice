import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { createStore } from '../src/dataStore.js';
import { makeHandler } from '../src/routes.js';

async function withServer(fn, store = createStore()) {
  const server = http.createServer(makeHandler(store));
  await new Promise(resolve => server.listen(0, resolve));
  try {
    return await fn(`http://127.0.0.1:${server.address().port}`);
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
}

async function get(base, path, options = {}) {
  const res = await fetch(base + path, options);
  const body = res.status === 204 ? null : await res.json();
  return { status: res.status, body, headers: res.headers };
}

async function post(base, path, body) {
  const res = await fetch(base + path, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: typeof body === 'string' ? body : JSON.stringify(body)
  });
  return { status: res.status, body: await res.json(), headers: res.headers };
}

function ids(entries) {
  return entries.map(entry => entry.id);
}

function overrideIds(accounts, value = true) {
  return accounts.filter(account => account.override === value).map(account => account.id).sort();
}

test('GET cohorts returns the fixture cohorts', () => withServer(async base => {
  const res = await get(base, '/api/flags/smart-compose/cohorts');
  assert.equal(res.status, 200);
  assert.equal(res.body.cohorts.length, 4);
  assert.equal(res.body.cohorts.find(cohort => cohort.cohortId === 'c-apac').plan, null);
}));

test('preview returns all five buckets and a normalized snapshot', () => withServer(async base => {
  const res = await post(base, '/api/flags/smart-compose/rollout/preview', {
    cohortId: 'c-pro-us',
    percentage: '30',
    excludeIds: [' acct-101 ', '', 'acct-101', 'acct-999']
  });
  assert.equal(res.status, 200);
  for (const key of ['selected', 'eligibleNotSelected', 'explicitlyOverridden', 'excluded', 'unknownExclusions']) {
    assert.ok(Array.isArray(res.body[key]), `${key} should be present`);
  }
  assert.deepEqual(res.body.inputSnapshot, {
    cohortId: 'c-pro-us',
    percentage: 30,
    excludeIds: ['acct-101', 'acct-999']
  });
}));

test('preview rejects malformed JSON', () => withServer(async base => {
  const res = await post(base, '/api/flags/smart-compose/rollout/preview', '{"cohortId":');
  assert.equal(res.status, 400);
  assert.equal(res.body.error, 'invalid_json');
}));

test('preview rejects an empty body', () => withServer(async base => {
  const res = await post(base, '/api/flags/smart-compose/rollout/preview', {});
  assert.equal(res.status, 400);
  assert.equal(res.body.error, 'cohort_id_required');
}));

test('preview rejects a non-object body', () => withServer(async base => {
  for (const body of ['5', '[1,2]']) {
    const res = await post(base, '/api/flags/smart-compose/rollout/preview', body);
    assert.equal(res.status, 400);
    assert.equal(res.body.error, 'cohort_id_required');
  }
}));

test('preview rejects an absent percentage', () => withServer(async base => {
  const res = await post(base, '/api/flags/smart-compose/rollout/preview', { cohortId: 'c-pro-us' });
  assert.equal(res.status, 400);
  assert.equal(res.body.error, 'percentage_invalid');
}));

test('preview rejects an unknown cohort', () => withServer(async base => {
  const res = await post(base, '/api/flags/smart-compose/rollout/preview', { cohortId: 'missing', percentage: 30 });
  assert.equal(res.status, 404);
  assert.equal(res.body.error, 'cohort_not_found');
}));

test('preview does not mutate', () => withServer(async base => {
  const before = await get(base, '/api/flags/smart-compose/accounts');
  const preview = await post(base, '/api/flags/smart-compose/rollout/preview', {
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: []
  });
  const after = await get(base, '/api/flags/smart-compose/accounts');
  assert.equal(preview.status, 200);
  assert.deepEqual(after.body, before.body);
}));

test('unknown method on a rollout path falls through to 404', () => withServer(async base => {
  const res = await get(base, '/api/flags/smart-compose/rollout/apply');
  assert.equal(res.status, 404);
  assert.equal(res.body.error, 'not_found');
}));

test('OPTIONS preflight allows POST and content-type', () => withServer(async base => {
  const res = await get(base, '/api/flags/smart-compose/rollout/apply', { method: 'OPTIONS' });
  assert.equal(res.status, 204);
  assert.match(res.headers.get('access-control-allow-methods'), /POST/);
  assert.match(res.headers.get('access-control-allow-headers'), /content-type/);
}));

test('apply writes exactly the previewed selected set', () => withServer(async base => {
  const before = await get(base, '/api/flags/smart-compose/accounts');
  const preview = await post(base, '/api/flags/smart-compose/rollout/preview', {
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: []
  });
  const apply = await post(base, '/api/flags/smart-compose/rollout/apply', {
    ...preview.body.inputSnapshot,
    requestId: 'req-write-selected',
    expectedRevision: preview.body.basedOnRevision
  });
  const after = await get(base, '/api/flags/smart-compose/accounts');
  const selected = ids(preview.body.selected).sort();

  assert.equal(apply.status, 200);
  assert.deepEqual(apply.body.appliedAccountIds.sort(), selected);
  assert.deepEqual(overrideIds(after.body.accounts), [...new Set([...overrideIds(before.body.accounts), ...selected])].sort());
  for (const account of after.body.accounts.filter(account => !selected.includes(account.id))) {
    assert.equal(account.override, before.body.accounts.find(beforeAccount => beforeAccount.id === account.id).override);
  }
}));

test('apply increments the flag revision exactly once', () => withServer(async base => {
  const before = await get(base, '/api/flags/smart-compose/accounts');
  const preview = await post(base, '/api/flags/smart-compose/rollout/preview', {
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: []
  });
  assert.equal(preview.body.selected.length >= 2, true);
  const apply = await post(base, '/api/flags/smart-compose/rollout/apply', {
    ...preview.body.inputSnapshot,
    requestId: 'req-revision-once',
    expectedRevision: before.body.flag.revision
  });
  assert.equal(apply.status, 200);
  assert.equal(apply.body.flag.revision, before.body.flag.revision + 1);
  assert.equal(apply.body.datasetRevision, before.body.datasetRevision + 1);
}));

test('accounts endpoint reflects the rollout', () => withServer(async base => {
  const preview = await post(base, '/api/flags/smart-compose/rollout/preview', {
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: []
  });
  const apply = await post(base, '/api/flags/smart-compose/rollout/apply', {
    ...preview.body.inputSnapshot,
    requestId: 'req-accounts-reflect',
    expectedRevision: preview.body.basedOnRevision
  });
  const accounts = await get(base, '/api/flags/smart-compose/accounts');
  assert.equal(apply.status, 200);
  assert.deepEqual(overrideIds(accounts.body.accounts), ['acct-102', ...apply.body.appliedAccountIds].sort());
  assert.equal(accounts.body.flag.revision, apply.body.flag.revision);
  assert.equal(accounts.body.datasetRevision, apply.body.datasetRevision);
}));

test('stale apply changes nothing', () => withServer(async base => {
  const manual = await post(base, '/api/flags/smart-compose/override', {
    accountId: 'acct-101',
    enabled: true,
    expectedRevision: 1
  });
  assert.equal(manual.status, 200);
  const before = await get(base, '/api/flags/smart-compose/accounts');
  const res = await post(base, '/api/flags/smart-compose/rollout/apply', {
    requestId: 'req-stale',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: before.body.flag.revision - 1
  });
  const after = await get(base, '/api/flags/smart-compose/accounts');
  assert.equal(res.status, 409);
  assert.deepEqual(res.body, { error: 'stale', currentRevision: before.body.flag.revision });
  assert.deepEqual(after.body, before.body);
}));

test('replaying the same requestId does not re-apply', () => withServer(async base => {
  const first = await post(base, '/api/flags/smart-compose/rollout/apply', {
    requestId: 'req-replay',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const afterFirst = await get(base, '/api/flags/smart-compose/accounts');
  const second = await post(base, '/api/flags/smart-compose/rollout/apply', {
    requestId: 'req-replay',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const afterSecond = await get(base, '/api/flags/smart-compose/accounts');
  assert.equal(first.status, 200);
  assert.equal(second.status, 200);
  assert.equal(second.body.replayed, true);
  assert.equal(afterSecond.body.flag.revision, afterFirst.body.flag.revision);
  assert.deepEqual(afterSecond.body, afterFirst.body);
}));

test('replay still works after an intervening manual override', () => withServer(async base => {
  const first = await post(base, '/api/flags/smart-compose/rollout/apply', {
    requestId: 'req-replay-after-manual',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  assert.equal(first.status, 200);
  const manual = await post(base, '/api/flags/smart-compose/override', {
    accountId: 'acct-101',
    enabled: true,
    expectedRevision: first.body.flag.revision
  });
  const afterManual = await get(base, '/api/flags/smart-compose/accounts');
  const replay = await post(base, '/api/flags/smart-compose/rollout/apply', {
    requestId: 'req-replay-after-manual',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const afterReplay = await get(base, '/api/flags/smart-compose/accounts');
  assert.equal(manual.status, 200);
  assert.equal(replay.status, 200);
  assert.equal(replay.body.replayed, true);
  assert.equal(afterReplay.body.flag.revision, manual.body.flag.revision);
  assert.deepEqual(afterReplay.body, afterManual.body);
}));

test('reusing a requestId with different inputs is rejected', () => withServer(async base => {
  const first = await post(base, '/api/flags/smart-compose/rollout/apply', {
    requestId: 'req-conflict',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const beforeConflict = await get(base, '/api/flags/smart-compose/accounts');
  const conflict = await post(base, '/api/flags/smart-compose/rollout/apply', {
    requestId: 'req-conflict',
    cohortId: 'c-large-ent',
    percentage: 50,
    excludeIds: [],
    expectedRevision: 1
  });
  const afterConflict = await get(base, '/api/flags/smart-compose/accounts');
  assert.equal(first.status, 200);
  assert.equal(conflict.status, 409);
  assert.deepEqual(conflict.body, { error: 'request_id_conflict' });
  assert.deepEqual(afterConflict.body, beforeConflict.body);
}));

test('apply ignores a client-supplied accountIds field', () => withServer(async base => {
  const withExtra = await post(base, '/api/flags/smart-compose/rollout/apply', {
    requestId: 'req-extra',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1,
    accountIds: ['acct-999', 'acct-103']
  });
  const withoutExtra = await withServer(innerBase => post(innerBase, '/api/flags/smart-compose/rollout/apply', {
    requestId: 'req-no-extra',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  }));
  const accounts = await get(base, '/api/flags/smart-compose/accounts');
  assert.equal(withExtra.status, 200);
  assert.deepEqual(withExtra.body, withoutExtra.body);
  assert.equal(accounts.body.accounts.find(account => account.id === 'acct-103').override, null);
}));

test('concurrent applies with different requestIds: exactly one wins', () => withServer(async base => {
  const before = await get(base, '/api/flags/smart-compose/accounts');
  const input = { cohortId: 'c-large-ent', percentage: 100, excludeIds: [], expectedRevision: before.body.flag.revision };
  const results = await Promise.all([
    post(base, '/api/flags/smart-compose/rollout/apply', { ...input, requestId: 'req-concurrent-a' }),
    post(base, '/api/flags/smart-compose/rollout/apply', { ...input, requestId: 'req-concurrent-b' })
  ]);
  const after = await get(base, '/api/flags/smart-compose/accounts');
  assert.deepEqual(results.map(result => result.status).sort((a, b) => a - b), [200, 409]);
  assert.equal(after.body.flag.revision, before.body.flag.revision + 1);
  assert.equal(results.find(result => result.status === 409).body.currentRevision, after.body.flag.revision);
}));

test('concurrent applies with the same requestId: one applies, one replays', () => withServer(async base => {
  const before = await get(base, '/api/flags/smart-compose/accounts');
  const input = {
    requestId: 'req-concurrent-same',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: before.body.flag.revision
  };
  const results = await Promise.all([
    post(base, '/api/flags/smart-compose/rollout/apply', input),
    post(base, '/api/flags/smart-compose/rollout/apply', input)
  ]);
  const after = await get(base, '/api/flags/smart-compose/accounts');
  assert.deepEqual(results.map(result => result.status), [200, 200]);
  assert.equal(results.filter(result => result.body.replayed === false).length, 1);
  assert.equal(results.filter(result => result.body.replayed === true).length, 1);
  assert.equal(after.body.flag.revision, before.body.flag.revision + 1);
}));

test('concurrent apply and manual override: exactly one succeeds', () => withServer(async base => {
  const before = await get(base, '/api/flags/smart-compose/accounts');
  const results = await Promise.all([
    post(base, '/api/flags/smart-compose/rollout/apply', {
      requestId: 'req-concurrent-manual',
      cohortId: 'c-large-ent',
      percentage: 100,
      excludeIds: [],
      expectedRevision: before.body.flag.revision
    }),
    post(base, '/api/flags/smart-compose/override', {
      accountId: 'acct-101',
      enabled: true,
      expectedRevision: before.body.flag.revision
    })
  ]);
  const after = await get(base, '/api/flags/smart-compose/accounts');
  assert.deepEqual(results.map(result => result.status).sort((a, b) => a - b), [200, 409]);
  assert.equal(after.body.flag.revision, before.body.flag.revision + 1);
}));

test('a throwing store yields 500, not a hung request', () => withServer(async base => {
  const res = await get(base, '/api/flags/smart-compose/accounts');
  assert.equal(res.status, 500);
  assert.deepEqual(res.body, { error: 'internal_error' });
}, {
  getFlag() {
    return { overrides: {} };
  },
  listAccounts() {
    throw new Error('boom');
  },
  snapshot() {
    return { datasetRevision: 1 };
  }
}));

test('existing override endpoint still enforces stale protection after a rollout', () => withServer(async base => {
  const rollout = await post(base, '/api/flags/smart-compose/rollout/apply', {
    requestId: 'req-before-override',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const ok = await post(base, '/api/flags/smart-compose/override', {
    accountId: 'acct-101',
    enabled: true,
    expectedRevision: rollout.body.flag.revision
  });
  const stale = await post(base, '/api/flags/smart-compose/override', {
    accountId: 'acct-103',
    enabled: true,
    expectedRevision: rollout.body.flag.revision
  });
  assert.equal(rollout.status, 200);
  assert.equal(ok.status, 200);
  assert.equal(stale.status, 409);
  assert.equal(stale.body.currentRevision, ok.body.flag.revision);
}));
