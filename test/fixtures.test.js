import test from 'node:test';
import assert from 'node:assert/strict';
import { loadFixtures } from '../src/fixtures.js';

test('fixtures load and expose candidate runs plus observations', () => {
  const data = loadFixtures();
  assert.equal(data.suites.length, 4);
  assert.ok(data.runs.length >= 10);
  assert.ok(data.cases.length >= 15);
  assert.ok(data.observations.length >= 30);
  assert.ok(data.runs.some(r => r.id === 'run-support-cand-44'));
  assert.ok(data.observations.some(o => o.attempt > 1));
});
