import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createStore, DomainError } from '../src/store.js';

const seed = JSON.parse(readFileSync(new URL('../fixtures/catalog.json', import.meta.url)));
const store = () => createStore(seed);

test('studio isolation, ordering, filtering and limit', () => {
  const s = store();
  const all = s.listAssets({ studio: 'atlas' });
  assert.equal(all.total, 4);
  assert.deepEqual(all.assets.map(a => a.id), ['A-101','A-102','A-103','A-104']);
  assert.deepEqual(s.listAssets({ studio: 'cedar', status: 'ready', limit: 1 }).assets.map(a => a.id), ['C-201']);
  assert.equal(s.listAssets({ studio: 'cedar', status: 'ready', limit: 1 }).total, 3);
  assert.equal(s.listAssets({ studio: 'atlas', q: 'EA RTH' }).total, 0);
  assert.equal(s.listAssets({ studio: 'atlas', q: 'earth' }).total, 2);
});

test('details copy protects canonical state and other studio stays hidden', () => {
  const s = store();
  const result = s.getAsset('A-101', 'atlas');
  result.asset.captions['en-US'][0].text = 'changed outside store';
  assert.equal(s.getAsset('A-101', 'atlas').asset.captions['en-US'][0].text, 'Welcome to the city.');
  assert.throws(() => s.getAsset('C-201', 'atlas'), e => e instanceof DomainError && e.status === 404);
});

test('note write increments once and identical normalized text is a no-op', () => {
  const s = store();
  const first = s.editNote('A-101', 'atlas', ' New review requested.  ', 3);
  assert.equal(first.asset.revision, 4);
  assert.equal(first.datasetRevision, 43);
  const again = s.editNote('A-101', 'atlas', 'New review requested.', 4);
  assert.equal(again.asset.revision, 4);
  assert.equal(again.datasetRevision, 43);
  assert.equal(s.getAsset('A-102', 'atlas').asset.revision, 1);
});

test('stale and malformed notes cannot mutate data', () => {
  const s = store();
  assert.throws(() => s.editNote('A-101', 'atlas', 'new', 2), e => e.code === 'STALE_REVISION');
  assert.throws(() => s.editNote('A-101', 'atlas', '  ', 3), e => e.code === 'INVALID_NOTE');
  assert.throws(() => s.editNote('A-101', 'atlas', 'okay', '3'), e => e.code === 'INVALID_REVISION');
  assert.equal(s.getAsset('A-101', 'atlas').datasetRevision, 42);
});

test('unsupported filters and limits rejected', () => {
  const s = store();
  assert.throws(() => s.listAssets({ studio: 'missing' }), e => e.status === 400);
  assert.throws(() => s.listAssets({ studio: 'atlas', status: 'gone' }), e => e.status === 400);
  assert.throws(() => s.listAssets({ studio: 'atlas', limit: 0 }), e => e.status === 400);
});
