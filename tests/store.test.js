import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../server/store.js';
test('filters and deterministic ordering',()=>{
  const store=createStore();
  assert.deepEqual(store.list({site:'west'}).items.map(s=>s.id),['SH-101','SH-103','SH-105']);
  assert.equal(store.list({state:'closed'}).items.length,1);
  assert.equal(store.list({search:'cold kit f'}).items[0].id,'SH-106');
});
test('note no-op, change and stale revision',()=>{
  const store=createStore();
  const before=store.detail('SH-101');
  const same=store.setNote('SH-101',{expectedRevision:3,note:'  Verify loading seal  '});
  assert.equal(same.changed,false);
  assert.equal(same.datasetRevision,before.datasetRevision);
  const result=store.setNote('SH-101',{expectedRevision:3,note:'Checked'});
  assert.equal(result.changed,true);
  assert.equal(result.shipment.revision,4);
  assert.equal(result.datasetRevision,2);
  assert.throws(()=>store.setNote('SH-101',{expectedRevision:3,note:'Stale'}),{code:'stale_revision'});
});
test('detail copy does not expose store state',()=>{
  const store=createStore();
  const one=store.detail('SH-101');
  one.shipment.operatorNote='bad';
  assert.equal(store.detail('SH-101').shipment.operatorNote,'Verify loading seal');
});
