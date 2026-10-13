import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createStore} from '../src/store.js';
const fixture=JSON.parse(readFileSync(new URL('../fixtures/catalog.json',import.meta.url),'utf8'));
assert.equal(new Set(fixture.tenants.map(x=>x.id)).size,fixture.tenants.length);
assert.equal(new Set(fixture.articles.map(x=>x.id)).size,fixture.articles.length);
for(const a of fixture.articles){
  assert(fixture.tenants.some(t=>t.id===a.tenantId));
  assert(['account','security','billing'].includes(a.category));
  assert(typeof a.published==='boolean' && Number.isSafeInteger(a.revision));
}
const store=createStore();
for(const t of fixture.tenants){
  const x=store.search({tenantId:t.id,query:'login',limit:50});
  assert(x.results.every(a=>a.tenantId===t.id&&a.published));
}
console.log(`verified ${fixture.tenants.length} tenants / ${fixture.articles.length} articles; baseline search and isolation valid`);
