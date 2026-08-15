import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../src/dataStore.js';

function ids(entries) {
  return entries.map(entry => entry.id);
}

function diffNewKeys(before, after) {
  return Object.keys(after).filter(key => !Object.prototype.hasOwnProperty.call(before, key)).sort();
}

test('cohorts load from the fixture', () => {
  const cohorts = createStore().listCohorts();
  assert.equal(cohorts.length, 4);
  assert.equal(cohorts.find(c => c.cohortId === 'c-apac').plan, null);
});

test('apply sets true overrides for exactly the selected accounts', () => {
  const store = createStore();
  const preview = store.calculateRollout({ cohortId: 'c-large-ent', percentage: 100, excludeIds: [] });
  const applied = store.applyRollout({
    requestId: 'req-1',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: preview.basedOnRevision
  });
  assert.deepEqual(applied.appliedAccountIds, ids(preview.selected));
  for (const id of applied.appliedAccountIds) assert.equal(applied.flag.overrides[id], true);
});

test('apply increments the flag revision exactly once', () => {
  const store = createStore();
  const before = store.snapshot();
  const preview = store.calculateRollout({ cohortId: 'c-large-ent', percentage: 100, excludeIds: [] });
  assert.equal(preview.selected.length >= 2, true);
  const applied = store.applyRollout({
    requestId: 'req-2',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: before.flag.revision
  });
  assert.equal(applied.flag.revision, before.flag.revision + 1);
  assert.equal(applied.datasetRevision, before.datasetRevision + 1);
});

test('apply does not touch non-selected accounts', () => {
  const store = createStore();
  const before = store.getFlag().overrides;
  const preview = store.calculateRollout({ cohortId: 'c-large-ent', percentage: 100, excludeIds: [] });
  store.applyRollout({
    requestId: 'req-3',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const after = store.getFlag().overrides;
  assert.deepEqual(diffNewKeys(before, after), ids(preview.selected));
  for (const [id, value] of Object.entries(before)) assert.equal(after[id], value);
});

test('stale apply changes nothing', () => {
  const store = createStore();
  const before = store.snapshot();
  const result = store.applyRollout({
    requestId: 'req-4',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: before.flag.revision - 1
  });
  const after = store.snapshot();
  assert.equal(result.error, 'stale');
  assert.deepEqual(after.flag.overrides, before.flag.overrides);
  assert.equal(after.flag.revision, before.flag.revision);
  assert.equal(after.datasetRevision, before.datasetRevision);
});

test('replaying the same requestId returns the recorded result', () => {
  const store = createStore();
  const first = store.applyRollout({
    requestId: 'req-5',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const afterFirst = store.snapshot();
  const second = store.applyRollout({
    requestId: 'req-5',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const afterSecond = store.snapshot();
  assert.deepEqual(second.appliedAccountIds, first.appliedAccountIds);
  assert.equal(second.replayed, true);
  assert.equal(afterSecond.flag.revision, afterFirst.flag.revision);
  assert.deepEqual(afterSecond.flag.overrides, afterFirst.flag.overrides);
});

test('replaying after an intervening manual override still does not re-apply', () => {
  const store = createStore();
  store.applyRollout({
    requestId: 'req-6',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  store.setOverride('acct-101', true, 2);
  const afterManual = store.snapshot();
  const replay = store.applyRollout({
    requestId: 'req-6',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const afterReplay = store.snapshot();
  assert.equal(replay.replayed, true);
  assert.equal(afterReplay.flag.revision, afterManual.flag.revision);
  assert.deepEqual(afterReplay.flag.overrides, afterManual.flag.overrides);
});

test('reusing a requestId with different inputs is rejected', () => {
  const store = createStore();
  store.applyRollout({
    requestId: 'req-7',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const beforeConflict = store.snapshot();
  const conflict = store.applyRollout({
    requestId: 'req-7',
    cohortId: 'c-large-ent',
    percentage: 50,
    excludeIds: [],
    expectedRevision: 1
  });
  const afterConflict = store.snapshot();
  assert.equal(conflict.error, 'request_id_conflict');
  assert.deepEqual(afterConflict.flag.overrides, beforeConflict.flag.overrides);
  assert.equal(afterConflict.flag.revision, beforeConflict.flag.revision);
  assert.equal(afterConflict.datasetRevision, beforeConflict.datasetRevision);
});

test('unknown cohort is rejected without mutating', () => {
  const store = createStore();
  const before = store.snapshot();
  const result = store.applyRollout({
    requestId: 'req-8',
    cohortId: 'missing',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const after = store.snapshot();
  assert.equal(result.error, 'cohort_not_found');
  assert.deepEqual(after.flag.overrides, before.flag.overrides);
  assert.equal(after.flag.revision, before.flag.revision);
  assert.equal(after.datasetRevision, before.datasetRevision);
});

test('apply with an empty selection still increments once', () => {
  const store = createStore();
  const before = store.snapshot();
  const preview = store.calculateRollout({ cohortId: 'c-apac', percentage: 0, excludeIds: [] });
  assert.deepEqual(preview.selected, []);
  const result = store.applyRollout({
    requestId: 'req-9',
    cohortId: 'c-apac',
    percentage: 0,
    excludeIds: [],
    expectedRevision: 1
  });
  assert.deepEqual(result.appliedAccountIds, []);
  assert.equal(result.flag.revision, before.flag.revision + 1);
  assert.equal(result.datasetRevision, before.datasetRevision + 1);
});

test('manual setOverride still works after a rollout', () => {
  const store = createStore();
  store.applyRollout({
    requestId: 'req-10',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  const result = store.setOverride('acct-101', false, 2);
  assert.equal(result.flag.overrides['acct-101'], false);
  assert.equal(result.flag.revision, 3);
});
