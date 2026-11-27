import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {normalize} from '../catalog.mjs';
const fixture = () => JSON.parse(readFileSync(new URL('../fixtures/batch.json', import.meta.url), 'utf8'));
test('fixture normalizes delivery retries', () => {
  const batch = normalize(fixture());
  assert.equal(batch.reviewers.length, 7);
  assert.equal(batch.documents.length, 11);
  assert.deepEqual(batch.documents.find(d => d.id === 'D-017').eligible, ['Lena','Otto']);
});
test('conflicting reviewer declarations rejected', () => {
  const raw = fixture(); raw.reviewers.at(-1).capacity = 2;
  assert.throws(() => normalize(raw), /conflicting/);
});
test('invalid eligibility rejected', () => {
  const raw = fixture(); raw.documents[0].eligible.push('Ana');
  assert.throws(() => normalize(raw), /eligibility/);
});
test('noninteger capacity rejected', () => {
  const raw = fixture(); raw.reviewers[0].capacity = true;
  assert.throws(() => normalize(raw), /reviewer/);
});
test('empty input is valid', () => assert.deepEqual(normalize({reviewers:[],documents:[]}), {reviewers:[],documents:[]}));
test('CLI emits one JSON object', () => {
  const r = spawnSync(process.execPath, ['cli.mjs','fixtures/batch.json'], {encoding:'utf8'});
  assert.equal(r.status, 0, r.stderr); assert.equal(r.stdout.trim().split('\n').length, 1);
  assert.equal(typeof JSON.parse(r.stdout).status, 'string');
});
test('CLI failure emits no stdout', () => {
  const r = spawnSync(process.execPath, ['cli.mjs','missing.json'], {encoding:'utf8'});
  assert.notEqual(r.status, 0); assert.equal(r.stdout, ''); assert.ok(r.stderr);
});
