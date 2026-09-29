import test from 'node:test';
import assert from 'node:assert/strict';
import { loadFixtures } from '../src/fixtures.js';
import { SuiteStore } from '../src/store.js';

function makeStore() { return new SuiteStore(loadFixtures()); }

test('lists suites in deterministic owner/name order', () => {
  const store = makeStore();
  const ids = store.listSuites().map(s => s.id);
  assert.deepEqual(ids, ['support-reply', 'invoice-extraction', 'search-grounding', 'moderation-triage']);
});

test('filters by owner and status', () => {
  const store = makeStore();
  assert.deepEqual(store.listSuites({ owner: 'cx-ai', status: 'active' }).map(s => s.id), ['support-reply']);
  assert.deepEqual(store.listSuites({ status: 'paused' }).map(s => s.id), ['moderation-triage']);
});

test('note update trims value and increments revisions once', () => {
  const store = makeStore();
  const before = store.getSuite('search-grounding');
  const result = store.updateNote('search-grounding', { note: '  inspect citation misses  ', expectedRevision: before.revision });
  assert.equal(result.status, 200);
  assert.equal(result.body.changed, true);
  assert.equal(result.body.suite.note, 'inspect citation misses');
  assert.equal(result.body.suite.revision, before.revision + 1);
  assert.equal(result.body.suite.datasetRevision, before.datasetRevision + 1);
});

test('saving same normalized note is a no-op', () => {
  const store = makeStore();
  const before = store.getSuite('support-reply');
  const result = store.updateNote('support-reply', { note: '  ' + before.note + '  ', expectedRevision: before.revision });
  assert.equal(result.status, 200);
  assert.equal(result.body.changed, false);
  assert.equal(result.body.suite.revision, before.revision);
  assert.equal(result.body.suite.datasetRevision, before.datasetRevision);
});

test('stale note write fails without mutation', () => {
  const store = makeStore();
  const before = store.getSuite('invoice-extraction');
  const result = store.updateNote('invoice-extraction', { note: 'new note', expectedRevision: before.revision - 1 });
  assert.equal(result.status, 409);
  assert.equal(store.getSuite('invoice-extraction').note, before.note);
  assert.equal(store.getSuite('invoice-extraction').revision, before.revision);
});
