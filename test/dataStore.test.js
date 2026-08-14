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

test('snapshot returns assignments, events and the matching revision together', () => {
  const store = new DataStore();
  const before = store.snapshot();
  assert.equal(before.revision, 1);
  assert.equal(before.assignments.length, 8);
  assert.ok(before.events.length > 20);
  assert.equal(before.assignments.every(a => 'excluded' in a), true);

  store.excludeUser('u-100', 'internal QA');
  const after = store.snapshot();
  assert.equal(after.revision, 2);
  assert.equal(after.assignments.find(a => a.user_id === 'u-100').excluded, true);

  // The earlier snapshot is a point-in-time read, not a live view of the store.
  assert.equal(before.revision, 1);
  assert.equal(before.assignments.find(a => a.user_id === 'u-100').excluded, false);
});

test('snapshot hands out copies that cannot corrupt the store', () => {
  const store = new DataStore();
  const snapshot = store.snapshot();
  snapshot.events.pop();
  snapshot.assignments[0].variant = 'tampered';
  assert.equal(store.snapshot().events.length, snapshot.events.length + 1);
  assert.notEqual(store.snapshot().assignments[0].variant, 'tampered');
});

test('invalid exclusion reason does not mutate revision', () => {
  const store = new DataStore();
  const before = store.revision;
  const result = store.excludeUser('u-100', '   ');
  assert.deepEqual(result, { ok: false, code: 'invalid_reason' });
  assert.equal(store.revision, before);
});
