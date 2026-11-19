import {readFileSync} from 'node:fs';import assert from 'node:assert/strict';
import {makeCatalog} from '../server/catalog.js';
const db=makeCatalog();assert.equal(db.organizations.length,3);assert.equal(db.sessions.length,6);
for(const s of db.sessions){assert.ok(db.organizations.some(o=>o.id===s.orgId));assert.ok(Number.isInteger(s.capacity)&&s.capacity>0);assert.ok(s.people.every(p=>['confirmed','waiting','cancelled'].includes(p.status)));assert.ok(new Set(s.people.map(p=>p.id)).size===s.people.length);assert.ok(s.people.filter(p=>p.status==='confirmed').length<=s.capacity);}
const html=readFileSync(new URL('../public/index.html',import.meta.url),'utf8');assert.match(html,/app\.js/);console.log(`Fixtures valid: ${db.organizations.length} organizations, ${db.sessions.length} sessions, ${db.sessions.reduce((n,s)=>n+s.people.length,0)} registrations.`);
