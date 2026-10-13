import test from 'node:test';
import assert from 'node:assert/strict';
import {createStore} from '../src/store.js';

test('note edit increments article and tenant exactly once, including no-op', () => {
  const store=createStore();
  const current=store.article('orchid','oc-101');
  const edit=store.updateNote({tenantId:'orchid',id:'oc-101',expectedRevision:current.revision,note:'  Check identity  '});
  assert.equal(edit.note,'Check identity');
  assert.equal(edit.revision,current.revision+1);
  assert.equal(edit.tenantRevision,current.tenantRevision+1);
  const noop=store.updateNote({tenantId:'orchid',id:'oc-101',expectedRevision:edit.revision,note:'Check identity'});
  assert.deepEqual(noop,edit);
});
test('stale note edit never changes the object', () => {
  const store=createStore();
  const current=store.article('harbor','hc-201');
  assert.throws(()=>store.updateNote({tenantId:'harbor',id:'hc-201',expectedRevision:current.revision+5,note:'bad'}), {status:409});
  assert.deepEqual(store.article('harbor','hc-201'),current);
});
test('an article cannot be retrieved from another tenant', () => {
  const store=createStore();
  assert.throws(()=>store.article('harbor','oc-101'), {status:404});
});
