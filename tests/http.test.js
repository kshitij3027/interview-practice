import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../server/http.js';
import { createStore } from '../server/store.js';
test('health, list, detail and revision-protected note endpoint',async t=>{
  const server=createServer(createStore());
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(()=>new Promise(resolve=>server.close(resolve)));
  const base='http://127.0.0.1:'+server.address().port;
  assert.equal((await (await fetch(base+'/api/health')).json()).ok,true);
  assert.equal((await (await fetch(base+'/api/shipments?site=east')).json()).items.length,2);
  assert.equal((await (await fetch(base+'/api/shipments/SH-101')).json()).shipment.revision,3);
  const options={method:'PATCH',headers:{'content-type':'application/json'},body:JSON.stringify({expectedRevision:3,note:'Inspected'})};
  const updated=await fetch(base+'/api/shipments/SH-101/note',options);
  assert.equal(updated.status,200);
  assert.equal((await updated.json()).shipment.operatorNote,'Inspected');
  const stale=await fetch(base+'/api/shipments/SH-101/note',options);
  assert.equal(stale.status,409);
  assert.equal((await stale.json()).error,'stale_revision');
});
test('browser shell and modules served',async t=>{
  const server=createServer();
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(()=>new Promise(resolve=>server.close(resolve)));
  const base='http://127.0.0.1:'+server.address().port;
  assert.match(await (await fetch(base)).text(),/ThermoTrace/);
  for(const name of ['app.js','list.js','detail.js','api-client.js','detail_view.js','style.css'])
    assert.equal((await fetch(base+'/'+name)).status,200);
});
