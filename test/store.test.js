import { test } from 'node:test';
import assert from 'node:assert/strict';
import { OrderStore, ApiError } from '../src/store.js';
import { loadOrders } from '../src/model.js';

test('fixture loads and has distinct orders', () => {
  const orders = loadOrders();
  assert.equal(orders.length, 6);
  assert.equal(new Set(orders.map((o) => o.id)).size, orders.length);
});

test('order listing uses filters, descending instant and safe copies', () => {
  const store = new OrderStore();
  const { orders } = store.list({ status: 'delivered', search: 'cedar' });
  assert.deepEqual(orders.map(({ id }) => id), ['ORD-205']);
  assert.deepEqual(store.list().orders.map(({ id }) => id), ['ORD-204','ORD-202','ORD-203','ORD-205','ORD-201','ORD-206']);
  const detail = store.detail('ORD-201');
  detail.order.lines[0].quantity = 900;
  assert.equal(store.detail('ORD-201').order.lines[0].quantity, 3);
});

test('note changes once, trim-only no-op, stale rejection leaves state alone', () => {
  const store = new OrderStore();
  const original = store.detail('ORD-201');
  const changed = store.updateNote('ORD-201', { expectedRevision: 3, note: '  Checked  ' });
  assert.equal(changed.order.note, 'Checked');
  assert.equal(changed.order.revision, 4);
  assert.equal(changed.datasetRevision, original.datasetRevision + 1);
  const unchanged = store.updateNote('ORD-201', { expectedRevision: 4, note: ' Checked ' });
  assert.deepEqual(unchanged, changed);
  assert.throws(() => store.updateNote('ORD-201', { expectedRevision: 3, note: 'bad' }), (err) => err instanceof ApiError && err.status === 409);
  assert.deepEqual(store.detail('ORD-201'), changed);
});

test('reject unknown order, invalid note and filters', () => {
  const store = new OrderStore();
  assert.throws(() => store.detail('ORD-999'), { status: 404 });
  assert.throws(() => store.list({ status: 'other' }), { status: 400 });
  assert.throws(() => store.updateNote('ORD-201', { expectedRevision: 3, note: 7 }), { status: 400 });
});
