import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../server/http.js';
import { createStore } from '../server/domain.js';

async function withApp(fn) {
  const server=createServer(createStore());
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  try {await fn(`http://127.0.0.1:${server.address().port}`);} finally {await new Promise(resolve=>server.close(resolve));}
}
test('GET serves existing console and scoped records',async()=>withApp(async base=>{
  const page=await fetch(base+'/');assert.equal(page.status,200);assert.match(await page.text(),/FlagHarbor/);
  const flags=await (await fetch(base+'/api/flags?org=org-harbor')).json();assert.equal(flags.total,2);
  const denied=await fetch(base+'/api/flags/flag-search?org=org-harbor');assert.equal(denied.status,404);
}));
test('PATCH note updates record and rejects stale revision',async()=>withApp(async base=>{
  const url=base+'/api/flags/flag-search/note?org=org-cedar';
  const options={method:'PATCH',headers:{'content-type':'application/json'},body:JSON.stringify({note:'Updated',expectedRevision:2})};
  const ok=await fetch(url,options);assert.equal(ok.status,200);assert.equal((await ok.json()).revision,3);
  const stale=await fetch(url,options);assert.equal(stale.status,409);assert.equal((await stale.json()).error.code,'STALE_REVISION');
}));
test('bad JSON returns 400 without mutating store',async()=>withApp(async base=>{
  const res=await fetch(base+'/api/flags/flag-search/note?org=org-cedar',{method:'PATCH',body:'not json'});
  assert.equal(res.status,400);assert.equal((await res.json()).error.code,'INVALID_JSON');
}));
