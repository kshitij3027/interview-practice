import test from 'node:test';
import assert from 'node:assert/strict';
import {createApp} from '../src/server.js';

test('live API serves search, detail, note update, and the static application', async () => {
  const app=createApp();
  await new Promise(resolve=>app.listen(0,'127.0.0.1',resolve));
  const base=`http://127.0.0.1:${app.address().port}`;
  try {
    const health=await (await fetch(base+'/api/health')).json();
    assert.deepEqual(health,{ok:true});
    const list=await (await fetch(base+'/api/articles?tenantId=orchid&q=login')).json();
    assert(list.results.length > 0);
    const a=await (await fetch(base+'/api/articles/oc-101?tenantId=orchid')).json();
    const patch=await fetch(base+'/api/articles/oc-101/note',{method:'PATCH',headers:{'content-type':'application/json'},body:JSON.stringify({tenantId:'orchid',expectedRevision:a.revision,note:'Reviewed'})});
    assert.equal(patch.status,200);
    assert.equal((await patch.json()).note,'Reviewed');
    const page=await fetch(base+'/');
    assert.equal(page.status,200);
    assert.match(await page.text(),/FindFix/);
  } finally {await new Promise(resolve=>app.close(resolve));}
});
