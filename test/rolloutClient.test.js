import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../src/dataStore.js';
import { normalizeExcludeIds } from '../src/rollout.js';
import { previewRollout } from '../src/rolloutService.js';
import {
  canApply,
  isPreviewDiverged,
  isPreviewStale,
  normalizeExcludeText,
  normalizeRolloutForm,
  sameInputs
} from '../web/store.js';

function clientState({ form, preview, flagRevision = 1, busy = null } = {}) {
  return {
    flag: { revision: flagRevision },
    rollout: {
      form: form ?? { cohortId: 'c-pro-us', percentage: '30', excludeText: 'acct-101' },
      preview: preview === undefined ? {
        basedOnRevision: 1,
        selected: [{ id: 'acct-101' }],
        inputSnapshot: { cohortId: 'c-pro-us', percentage: 30, excludeIds: ['acct-101'] }
      } : preview,
      busy
    }
  };
}

test('normalizeExcludeText trims, drops blanks and dedupes', () => {
  assert.deepEqual(normalizeExcludeText('a, ,a , b'), ['a', 'b']);

  for (const text of [
    '',
    ' acct-101 ',
    'acct-101,acct-102',
    'acct-101, ,acct-101, acct-103 ',
    ' <img src=x onerror=alert(1)> , acct-999 '
  ]) {
    assert.deepEqual(normalizeExcludeText(text), normalizeExcludeIds(text.split(',')));
  }
});

test('normalizeRolloutForm coerces a string percentage', () => {
  assert.deepEqual(normalizeRolloutForm({
    cohortId: ' c-pro-us ',
    percentage: '30',
    excludeText: ' acct-101 '
  }), {
    cohortId: 'c-pro-us',
    percentage: 30,
    excludeIds: ['acct-101']
  });
});

test('normalizeRolloutForm returns null for blank or invalid percentage', () => {
  for (const percentage of ['', '  ', 'abc', '-1', '101', '10.5']) {
    assert.equal(normalizeRolloutForm({ cohortId: 'c-pro-us', percentage, excludeText: '' }), null);
  }
});

test('normalizeRolloutForm returns null for a blank cohort', () => {
  assert.equal(normalizeRolloutForm({ cohortId: ' ', percentage: '30', excludeText: '' }), null);
});

test('sameInputs ignores exclusion whitespace and duplicates after normalization', () => {
  assert.equal(sameInputs(
    normalizeRolloutForm({ cohortId: 'c-pro-us', percentage: '30', excludeText: 'acct-101, acct-101' }),
    { cohortId: 'c-pro-us', percentage: 30, excludeIds: ['acct-101'] }
  ), true);
});

test('sameInputs detects percentage, cohort and exclusion changes', () => {
  const snapshot = { cohortId: 'c-pro-us', percentage: 30, excludeIds: ['acct-101'] };
  assert.equal(sameInputs({ ...snapshot, percentage: 31 }, snapshot), false);
  assert.equal(sameInputs({ ...snapshot, cohortId: 'c-large-ent' }, snapshot), false);
  assert.equal(sameInputs({ ...snapshot, excludeIds: ['acct-101', 'acct-102'] }, snapshot), false);
});

test('isPreviewStale reflects revision movement', () => {
  assert.equal(isPreviewStale(clientState({ flagRevision: 2 })), true);
  assert.equal(isPreviewStale(clientState({ flagRevision: 1 })), false);
});

test('isPreviewDiverged is false immediately after a real preview', () => {
  const preview = previewRollout(createStore(), {
    cohortId: 'c-pro-us',
    percentage: '30',
    excludeIds: [' acct-101 ', 'acct-101']
  });
  assert.equal(preview.status, 200);
  assert.equal(isPreviewDiverged(clientState({
    preview: preview.body,
    form: { cohortId: 'c-pro-us', percentage: '30', excludeText: 'acct-101' },
    flagRevision: preview.body.basedOnRevision
  })), false);
});

test('isPreviewDiverged is true after editing the form', () => {
  assert.equal(isPreviewDiverged(clientState({
    form: { cohortId: 'c-pro-us', percentage: '40', excludeText: 'acct-101' }
  })), true);
});

test('canApply covers blockers and the ready case', () => {
  const cases = [
    ['no preview', clientState({ preview: null }), false],
    ['busy', clientState({ busy: 'preview' }), false],
    ['stale', clientState({ flagRevision: 2 }), false],
    ['diverged', clientState({ form: { cohortId: 'c-pro-us', percentage: '40', excludeText: 'acct-101' } }), false],
    ['ready', clientState(), true]
  ];
  for (const [name, s, expected] of cases) {
    assert.equal(canApply(s), expected, name);
  }
});

test('canApply returns true again once the form is restored to the snapshot values', () => {
  const s = clientState({ form: { cohortId: 'c-pro-us', percentage: '40', excludeText: 'acct-101' } });
  assert.equal(canApply(s), false);
  s.rollout.form = { cohortId: 'c-pro-us', percentage: '30', excludeText: 'acct-101, acct-101' };
  assert.equal(canApply(s), true);
});
