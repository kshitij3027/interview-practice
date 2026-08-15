import test from'node:test';import assert from'node:assert/strict';import{createStore}from'../src/dataStore.js';
test('starter data loads',()=>{const s=createStore();assert.equal(s.listAccounts().length,8);assert.equal(s.getFlag().revision,1)});
test('override increments revisions',()=>{const s=createStore();const r=s.setOverride('acct-101',true,1);assert.equal(r.flag.revision,2);assert.equal(r.datasetRevision,2)});
test('stale override rejected',()=>{const s=createStore();s.setOverride('acct-101',true,1);assert.equal(s.setOverride('acct-103',true,1).error,'stale')});