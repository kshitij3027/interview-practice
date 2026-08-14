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

test('funnel report stamps the revision of the dataset it was computed from', () => {
  const service = new ExperimentService(new DataStore());
  const report = service.funnel({ segment: 'all' });
  assert.equal(report.ok, true);
  assert.equal(report.experiment, 'checkout-copy');
  assert.equal(report.revision, 1);
  assert.equal(report.segment, 'all');
  assert.deepEqual(report.steps, ['product_viewed', 'checkout_started', 'order_completed']);
  assert.equal(report.eligible_total, 8);
  assert.equal(report.variants.control.eligible, 4);
  assert.deepEqual(report.variants.control.steps, { product_viewed: 4, checkout_started: 4, order_completed: 2 });
  assert.equal(report.variants.treatment.eligible, 4);
  assert.deepEqual(report.variants.treatment.steps, { product_viewed: 4, checkout_started: 4, order_completed: 3 });
});

test('funnel does not hand out the shared steps constant', () => {
  const service = new ExperimentService(new DataStore());
  service.funnel().steps.push('tampered');
  assert.deepEqual(service.funnel().steps, ['product_viewed', 'checkout_started', 'order_completed']);
});

test('funnel defaults to the all segment and filters when given one', () => {
  const service = new ExperimentService(new DataStore());
  assert.deepEqual(service.funnel(), service.funnel({ segment: 'all' }));
  assert.deepEqual(service.funnel({ segment: undefined }), service.funnel({ segment: 'all' }));
  assert.equal(service.funnel({ segment: 'enterprise' }).eligible_total, 4);
  assert.equal(service.funnel({ segment: 'self-serve' }).eligible_total, 4);
});

test('funnel rejects an unknown segment without touching the dataset', () => {
  const service = new ExperimentService(new DataStore());
  assert.deepEqual(service.funnel({ segment: 'whales' }), { ok: false, code: 'invalid_segment' });
  assert.equal(service.overview().revision, 1);
});

test('excluding a user moves the revision and the funnel numbers together', () => {
  const service = new ExperimentService(new DataStore());
  const before = service.funnel({ segment: 'all' });

  service.setExclusion('u-102', true, 'internal QA');
  const after = service.funnel({ segment: 'all' });
  assert.equal(after.revision, before.revision + 1);
  assert.equal(after.eligible_total, before.eligible_total - 1);
  assert.equal(after.variants.treatment.eligible, 3);
  assert.deepEqual(after.variants.treatment.steps, { product_viewed: 3, checkout_started: 3, order_completed: 2 });

  // Same content as the baseline, but never the same revision: the staleness guard in the
  // client depends on revisions never repeating for different datasets.
  service.setExclusion('u-102', false);
  const restored = service.funnel({ segment: 'all' });
  assert.equal(restored.revision, before.revision + 2);
  assert.deepEqual(restored.variants, before.variants);
});

test('service can exclude and include a user', () => {
  const service = new ExperimentService(new DataStore());
  assert.equal(service.setExclusion('u-101', true, 'employee').ok, true);
  assert.equal(service.users().users.find(u => u.user_id === 'u-101').excluded, true);
  assert.equal(service.setExclusion('u-101', false).ok, true);
  assert.equal(service.users().users.find(u => u.user_id === 'u-101').excluded, false);
});
