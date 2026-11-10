import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore, listFlags, getFlag, listCustomers, editNote } from '../server/domain.js';

test('lists only organization flags sorted, counts before limit', () => {
  const store = createStore();
  const data = listFlags(store,{orgId:'org-cedar',limit:2});
  assert.equal(data.total, 3);
  assert.deepEqual(data.flags.map(flag => flag.id), ['flag-audit','flag-reports']);
});
test('search and enabled filter do not affect another tenant', () => {
  const store = createStore();
  const data = listFlags(store,{orgId:'org-cedar',search:'REPORT',status:'enabled'});
  assert.deepEqual(data.flags.map(flag=>flag.id), ['flag-reports']);
  assert.throws(()=>getFlag(store,'org-cedar','flag-care'),{code:'NOT_FOUND'});
  assert.deepEqual(listCustomers(store,'org-harbor').map(c=>c.id),['h-001','h-002','h-003']);
});
test('note edits check revision, trim, and do not advance for no-op', () => {
  const store = createStore();
  const old = getFlag(store,'org-cedar','flag-search');
  assert.equal(editNote(store,'org-cedar',old.id,{note:`  ${old.note} `,expectedRevision:old.revision}).revision,old.revision);
  const fresh = editNote(store,'org-cedar',old.id,{note:'  Reviewed  ',expectedRevision:old.revision});
  assert.equal(fresh.note,'Reviewed');assert.equal(fresh.revision,old.revision+1);
  assert.equal(store.datasetRevision,2);
  assert.throws(()=>editNote(store,'org-cedar',old.id,{note:'stale',expectedRevision:old.revision}),{code:'STALE_REVISION'});
});
test('malformed filters and missing organizations are structured errors',()=>{
  const store=createStore();
  assert.throws(()=>listFlags(store,{orgId:'org-cedar',limit:0}),{code:'INVALID_QUERY'});
  assert.throws(()=>listCustomers(store,'missing'),{status:404});
});
