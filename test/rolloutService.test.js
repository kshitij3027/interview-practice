import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../src/dataStore.js';
import { applyRollout, listCohorts, previewRollout } from '../src/rolloutService.js';

const falsyCoercible = [null, '', '   ', false, true, []];

function selectedIds(preview) {
  return preview.body.selected.map(entry => entry.id);
}

test('lists cohorts', () => {
  const result = listCohorts(createStore());
  assert.equal(result.status, 200);
  assert.equal(result.body.cohorts.length, 4);
});

test('rejects a missing cohort id', () => {
  const result = previewRollout(createStore(), { percentage: 30 });
  assert.equal(result.status, 400);
  assert.equal(result.body.error, 'cohort_id_required');
});

test('rejects an unknown cohort id', () => {
  const result = previewRollout(createStore(), { cohortId: 'missing', percentage: 30 });
  assert.equal(result.status, 404);
  assert.equal(result.body.error, 'cohort_not_found');
});

test('rejects a non-integer, negative or >100 percentage', () => {
  for (const percentage of [-1, 101, 10.5, 'abc', NaN, Infinity, undefined, {}, []]) {
    const result = previewRollout(createStore(), { cohortId: 'c-pro-us', percentage });
    assert.equal(result.status, 400, `percentage ${String(percentage)} should be rejected`);
    assert.equal(result.body.error, 'percentage_invalid');
  }
});

test('rejects falsy-coercible percentages', () => {
  for (const percentage of falsyCoercible) {
    const result = previewRollout(createStore(), { cohortId: 'c-pro-us', percentage });
    assert.equal(result.status, 400, `percentage ${String(percentage)} should be rejected`);
    assert.equal(result.body.error, 'percentage_invalid');
  }
});

test('rejects a percentage that is absent entirely', () => {
  const result = previewRollout(createStore(), { cohortId: 'c-pro-us' });
  assert.equal(result.status, 400);
  assert.equal(result.body.error, 'percentage_invalid');
});

test('accepts a numeric string percentage', () => {
  const result = previewRollout(createStore(), { cohortId: 'c-pro-us', percentage: '30' });
  assert.equal(result.status, 200);
  assert.equal(result.body.inputSnapshot.percentage, 30);
});

test('accepts 0 and 100', () => {
  assert.equal(previewRollout(createStore(), { cohortId: 'c-pro-us', percentage: 0 }).status, 200);
  assert.equal(previewRollout(createStore(), { cohortId: 'c-pro-us', percentage: 100 }).status, 200);
});

test('rejects non-array excludeIds', () => {
  const result = previewRollout(createStore(), { cohortId: 'c-pro-us', percentage: 30, excludeIds: 'acct-101' });
  assert.equal(result.status, 400);
  assert.equal(result.body.error, 'exclude_ids_invalid');
});

test('preview returns a normalized inputSnapshot', () => {
  const result = previewRollout(createStore(), {
    cohortId: 'c-pro-us',
    percentage: 30,
    excludeIds: [' acct-101 ', '', 'acct-101']
  });
  assert.equal(result.status, 200);
  assert.deepEqual(result.body.inputSnapshot, {
    cohortId: 'c-pro-us',
    percentage: 30,
    excludeIds: ['acct-101']
  });
});

test('preview does not mutate', () => {
  const store = createStore();
  const before = store.snapshot();
  const result = previewRollout(store, { cohortId: 'c-large-ent', percentage: 100, excludeIds: [] });
  const after = store.snapshot();
  assert.equal(result.status, 200);
  assert.deepEqual(after.flag.overrides, before.flag.overrides);
  assert.equal(after.flag.revision, before.flag.revision);
  assert.equal(after.datasetRevision, before.datasetRevision);
});

test('apply requires requestId and expectedRevision', () => {
  let result = applyRollout(createStore(), {
    cohortId: 'c-pro-us',
    percentage: 30,
    expectedRevision: 1
  });
  assert.equal(result.status, 400);
  assert.equal(result.body.error, 'request_id_required');

  result = applyRollout(createStore(), {
    requestId: 'req-missing-revision',
    cohortId: 'c-pro-us',
    percentage: 30
  });
  assert.equal(result.status, 400);
  assert.equal(result.body.error, 'expected_revision_required');

  for (const expectedRevision of falsyCoercible) {
    result = applyRollout(createStore(), {
      requestId: 'req-bad-revision',
      cohortId: 'c-pro-us',
      percentage: 30,
      expectedRevision
    });
    assert.equal(result.status, 400, `revision ${String(expectedRevision)} should be rejected`);
    assert.equal(result.body.error, 'expected_revision_required');
  }
});

test('apply maps stale to 409 with currentRevision', () => {
  const store = createStore();
  store.setOverride('acct-101', true, 1);
  const result = applyRollout(store, {
    requestId: 'req-stale',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  assert.equal(result.status, 409);
  assert.deepEqual(result.body, { error: 'stale', currentRevision: 2 });
});

test('apply maps a reused requestId with different inputs to 409', () => {
  const store = createStore();
  const first = applyRollout(store, {
    requestId: 'req-conflict',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  assert.equal(first.status, 200);
  const conflict = applyRollout(store, {
    requestId: 'req-conflict',
    cohortId: 'c-large-ent',
    percentage: 50,
    excludeIds: [],
    expectedRevision: 1
  });
  assert.equal(conflict.status, 409);
  assert.deepEqual(conflict.body, { error: 'request_id_conflict' });
});

test('preview then apply the snapshot at the same revision writes exactly the previewed selected set', () => {
  const store = createStore();
  const preview = previewRollout(store, { cohortId: 'c-large-ent', percentage: 100, excludeIds: ['acct-108'] });
  assert.equal(preview.status, 200);
  const applied = applyRollout(store, {
    ...preview.body.inputSnapshot,
    requestId: 'req-preview-apply',
    expectedRevision: preview.body.basedOnRevision
  });
  assert.equal(applied.status, 200);
  assert.deepEqual(applied.body.appliedAccountIds, selectedIds(preview));
});

test('apply ignores a client-supplied accountIds field', () => {
  const withExtra = applyRollout(createStore(), {
    requestId: 'req-extra',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1,
    accountIds: ['acct-999', 'acct-103']
  });
  const withoutExtra = applyRollout(createStore(), {
    requestId: 'req-no-extra',
    cohortId: 'c-large-ent',
    percentage: 100,
    excludeIds: [],
    expectedRevision: 1
  });
  assert.equal(withExtra.status, 200);
  assert.deepEqual(withExtra.body, withoutExtra.body);
});
