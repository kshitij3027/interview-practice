import test from 'node:test';
import assert from 'node:assert/strict';
import {makeStore} from '../src/store.mjs';
import {loadFixtures} from '../src/fixtures.mjs';

const make=()=>makeStore(loadFixtures());
test('fixture-backed list has deterministic newest-first order',()=>{
  const items=make().list().items;
  assert.equal(items.length,10);
  assert.equal(items[0].id,'C-203');
});
test('filters isolate tenant, status and case-insensitive query',()=>{
  const s=make();
  assert.deepEqual(s.list({tenant:'south',status:'open',q:'LOGIN'}).items.map(c=>c.id),['C-201']);
  assert.deepEqual(s.list({tenant:'north',status:'open',q:'acme'}).items.map(c=>c.id),['C-106','C-104','C-101']);
});
test('details are defensive copies, activity is chronological',()=>{
  const s=make();const a=s.get('C-101');
  assert.deepEqual(a.activity.map(e=>e.eventId),['EV-01','EV-04','EV-77']);
  a.case.note='tamper';a.activity.pop();
  assert.equal(s.get('C-101').case.note,'Customer investigating logs');
  assert.equal(s.get('C-101').activity.length,3);
});
test('note mutation increments case and dataset once; no-op is unchanged',()=>{
  const s=make();const before=s.get('C-101');
  const changed=s.updateNote('C-101',{note:'  Updated  ',expectedRevision:3});
  assert.equal(changed.case.revision,4);assert.equal(changed.datasetRevision,before.datasetRevision+1);
  const same=s.updateNote('C-101',{note:'Updated',expectedRevision:4});
  assert.equal(same.changed,false);assert.equal(same.datasetRevision,changed.datasetRevision);
});
test('stale note and invalid data leave state intact',()=>{
  const s=make();
  assert.throws(()=>s.updateNote('C-102',{note:'something',expectedRevision:0}),e=>e.status===409);
  assert.throws(()=>s.updateNote('C-102',{note:99,expectedRevision:1}),e=>e.status===400);
  assert.equal(s.get('C-102').case.revision,1);
});
test('missing cases return a typed error',()=>{
  assert.throws(()=>make().get('absent'),e=>e.status===404);
});
