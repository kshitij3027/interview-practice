import test from 'node:test';
import assert from 'node:assert/strict';
import { DataStore } from '../src/dataStore.js';
import { ExperimentService } from '../src/experimentService.js';

test('overview summarizes variants without transforming raw events', () => {
  const service = new ExperimentService(new DataStore());
  const overview = service.overview();
  assert.equal(overview.assignment_count, 8);
  assert.equal(overview.variants.control.assigned, 4);
  assert.equal(overview.variants.treatment.assigned, 4);
  assert.ok(overview.raw_event_count > overview.assignment_count);
});

test('service can exclude and include a user', () => {
  const service = new ExperimentService(new DataStore());
  assert.equal(service.setExclusion('u-101', true, 'employee').ok, true);
  assert.equal(service.users().users.find(u => u.user_id === 'u-101').excluded, true);
  assert.equal(service.setExclusion('u-101', false).ok, true);
  assert.equal(service.users().users.find(u => u.user_id === 'u-101').excluded, false);
});
