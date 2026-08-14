import test from 'node:test';
import assert from 'node:assert/strict';
import { DataStore, loadFixtureData } from '../src/dataStore.js';

test('fixture loader reads assignments and noisy event stream', () => {
  const data = loadFixtureData();
  assert.equal(data.assignments.length, 8);
  assert.ok(data.events.length > 20);
  assert.equal(data.events.filter(e => e.event_id === 'e-09').length, 2);
});

test('exclusion changes revision and is reflected in assignments', () => {
  const store = new DataStore();
  const before = store.revision;
  const result = store.excludeUser('u-100', 'internal QA');
  assert.equal(result.ok, true);
  assert.equal(store.revision, before + 1);
  assert.equal(store.listAssignments().find(u => u.user_id === 'u-100').excluded, true);
});

test('invalid exclusion reason does not mutate revision', () => {
  const store = new DataStore();
  const before = store.revision;
  const result = store.excludeUser('u-100', '   ');
  assert.deepEqual(result, { ok: false, code: 'invalid_reason' });
  assert.equal(store.revision, before);
});
