import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore, paidMinutes, DomainError } from '../src/domain.js';

test('starter loads employees and shift records', () => {
  const store = createStore();
  assert.equal(store.employees().employees.length, 3);
  assert.equal(store.listShifts().shifts.length, 11);
  assert.equal(store.getShift('sh-301').shift.paidMinutes, 450);
});

test('list filters by employee and status without changing the detail view', () => {
  const store = createStore();
  assert.equal(store.listShifts({ employeeId: 'emp-22', status: 'draft' }).shifts.length, 1);
  assert.equal(store.listShifts({ q: 'overnight' }).shifts[0].id, 'sh-306');
  assert.equal(store.getShift('sh-306').shift.employee.name, 'Operator 2');
});

test('list sorts by actual start instant, latest first', () => {
  const shifts = createStore().listShifts().shifts;
  assert.equal(shifts[0].id, 'sh-307');
  assert.equal(shifts.at(-1).id, 'sh-301');
});

test('notes are trimmed and increment relevant revisions once', async () => {
  const store = createStore();
  const old = store.getShift('sh-301');
  const changed = await store.saveNote('sh-301', { expectedRevision: 2, note: '  Checked by lead  ' });
  assert.equal(changed.shift.note, 'Checked by lead');
  assert.equal(changed.shift.revision, 3);
  assert.equal(changed.datasetRevision, old.datasetRevision + 1);
  assert.equal(store.getShift('sh-302').shift.revision, 1);
});

test('identical notes do not increment revisions', async () => {
  const store = createStore();
  const response = await store.saveNote('sh-301', { expectedRevision: 2, note: '  Stock count  ' });
  assert.equal(response.changed, false);
  assert.equal(response.datasetRevision, 1);
});

test('stale notes are rejected without side effects', async () => {
  const store = createStore();
  await store.saveNote('sh-302', { expectedRevision: 1, note: 'Prepared' });
  await assert.rejects(store.saveNote('sh-302', { expectedRevision: 1, note: 'Too late' }), (error) => {
    assert.equal(error.status, 409);
    return true;
  });
  assert.equal(store.getShift('sh-302').shift.note, 'Prepared');
});

test('malformed inputs and unknown shifts receive appropriate errors', async () => {
  const store = createStore();
  assert.throws(() => store.listShifts({ status: 'active' }), DomainError);
  assert.throws(() => store.getShift('missing'), (error) => error.status === 404);
  await assert.rejects(store.saveNote('sh-301', { expectedRevision: 2, note: 5 }), (error) => error.status === 400);
});

test('paid time excludes saved unpaid breaks without modifying shift', () => {
  const shift = createStore().getShift('sh-309').shift;
  assert.equal(paidMinutes(shift), 460);
  assert.equal(shift.breaks.length, 1);
});
