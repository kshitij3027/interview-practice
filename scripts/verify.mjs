import assert from 'node:assert/strict';
import {loadFixtures} from '../src/fixtures.mjs';
import {makeStore} from '../src/store.mjs';
const data=loadFixtures();
const ids=new Set(data.cases.map(c=>c.id));
assert.equal(ids.size,data.cases.length);
for(const c of data.cases){assert.ok(['open','pending','resolved'].includes(c.status));assert.ok(['P0','P1','P2','P3'].includes(c.priority));assert.ok(Number.isSafeInteger(c.revision));assert.ok(Date.parse(c.openedAt)<Infinity)}
for(const e of data.events){assert.ok(ids.has(e.caseId));assert.ok(Number.isFinite(Date.parse(e.at)));assert.ok(e.eventId&&e.body)}
const store=makeStore(data); assert.equal(store.list().items.length,data.cases.length);
console.log(`Fixtures valid: ${data.cases.length} cases, ${data.events.length} timeline events, ${new Set(data.cases.map(c=>c.tenantId)).size} tenants`);
