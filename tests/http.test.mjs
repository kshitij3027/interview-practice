import test from 'node:test';
import assert from 'node:assert/strict';
import {createRouter} from '../src/routes.mjs';
import {makeStore} from '../src/store.mjs';

const request=(method,url,body)=>({method,url,json:async()=>body});
test('router serves health, filtered list, detail and note update',async()=>{
  const route=createRouter(makeStore());
  assert.equal((await route(request('GET','/api/health'))).ok,true);
  assert.equal((await route(request('GET','/api/cases?tenant=south&status=open'))).items.length,2);
  assert.equal((await route(request('GET','/api/cases/C-101'))).case.id,'C-101');
  assert.equal((await route(request('PATCH','/api/cases/C-101/note',{note:'  New  ',expectedRevision:3}))).case.note,'New');
});
test('bad filter and bounded artificial delay are rejected',async()=>{
  const route=createRouter(makeStore());
  await assert.rejects(()=>route(request('GET','/api/cases?tenant=unknown')),e=>e.status===400);
  await assert.rejects(()=>route(request('GET','/api/cases/C-101?delayMs=2000')),e=>e.status===400);
});
