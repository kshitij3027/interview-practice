#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
node --input-type=module <<'JS'
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createStore,listFlags,listCustomers} from './server/domain.js';
const seed=JSON.parse(readFileSync('fixtures/workspace.json','utf8'));
const store=createStore(seed);
assert.equal(store.organizations.length,3);
assert.equal(store.flags.length,6);
assert.equal(store.customers.length,11);
for(const org of store.organizations){assert.equal(listFlags(store,{orgId:org.id}).total,seed.flags.filter(x=>x.orgId===org.id).length);assert.ok(listCustomers(store,org.id).length);}
console.log('Fixture checks passed: 3 organizations, 6 feature flags, 11 customers');
JS
