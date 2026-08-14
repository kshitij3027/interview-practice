import test from 'node:test';
import assert from 'node:assert/strict';
import { classifyReport, nextRevision } from '../web/reportGuards.js';

// A response that should be applied; each test overrides only what it is about.
const good = {
  requestId: 5,
  latestRequestId: 5,
  responseSegment: 'all',
  selectedSegment: 'all',
  responseRevision: 3,
  knownRevision: 3
};

test('the newest response for the current segment is applied', () => {
  assert.equal(classifyReport(good), 'apply');
});

test('a response ahead of the known revision is applied', () => {
  // Nobody else moved the dataset; this response is simply the first to see revision 4.
  assert.equal(classifyReport({ ...good, responseRevision: 4 }), 'apply');
});

test('a superseded request is discarded', () => {
  assert.equal(classifyReport({ ...good, requestId: 4, latestRequestId: 5 }), 'discard');
});

test('a superseded request is discarded even when its revision is stale', () => {
  // Checks the ordering of the guards: request identity is decided before revision.
  assert.equal(
    classifyReport({ ...good, requestId: 4, latestRequestId: 5, responseRevision: 1 }),
    'discard'
  );
});

test('a response for a segment the user has left is discarded', () => {
  assert.equal(classifyReport({ ...good, responseSegment: 'all', selectedSegment: 'enterprise' }), 'discard');
});

test('a segment mismatch is discarded rather than refetched, even when also stale', () => {
  assert.equal(
    classifyReport({ ...good, responseSegment: 'all', selectedSegment: 'enterprise', responseRevision: 1 }),
    'discard'
  );
});

test('a response computed before a known exclusion triggers a refetch', () => {
  assert.equal(classifyReport({ ...good, responseRevision: 1, knownRevision: 2 }), 'refetch');
});

test('nextRevision never moves backwards and ignores unusable input', () => {
  assert.equal(nextRevision(3, 4), 4);
  assert.equal(nextRevision(4, 3), 4);
  assert.equal(nextRevision(4, 4), 4);
  assert.equal(nextRevision(0, 1), 1);
  assert.equal(nextRevision(3, null), 3);
  assert.equal(nextRevision(3, undefined), 3);
  assert.equal(nextRevision(3, NaN), 3);
  assert.equal(nextRevision(undefined, 2), 2);
});

test('folding the revision in before classifying would disable the staleness guard', () => {
  const stale = { ...good, responseRevision: 1, knownRevision: 2 };

  // Correct order: compare first, so the stale response is caught.
  assert.equal(classifyReport(stale), 'refetch');

  // Wrong order: fold the response's revision into the known revision first, and the guard
  // can never fire again — the comparison becomes `1 < 1`. This assertion exists to document
  // the failure mode, since it is silent and every other test still passes.
  const folded = { ...stale, knownRevision: nextRevision(stale.knownRevision, stale.responseRevision) };
  assert.equal(classifyReport(folded), 'refetch', 'nextRevision must not lower the known revision');

  const invertedFold = { ...stale, knownRevision: stale.responseRevision };
  assert.equal(classifyReport(invertedFold), 'apply');
});
