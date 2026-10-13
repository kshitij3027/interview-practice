import test from 'node:test';
import assert from 'node:assert/strict';
import {baseScore, normalizeTerm, rankArticles} from '../src/search.js';
import {createStore} from '../src/store.js';

test('search normalization handles Unicode width and repeated whitespace', () => {
  assert.equal(normalizeTerm('  ＬＯＧＩＮ\t Access  '), 'login access');
});
test('only eligible articles appear; ordering does not depend on fixture input order', () => {
  const store=createStore();
  const result=store.search({tenantId:'orchid', query:'login', category:'all',limit:20});
  assert(result.results.length > 2);
  assert(!result.results.some(a => a.tenantId !== 'orchid' || !a.published));
  assert.deepEqual(result.results.map(x => x.id), [...result.results].sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).map(x=>x.id));
  assert(baseScore(result.results[0], 'login') > 0);
});
test('category and result limit preserve total count', () => {
  const store=createStore();
  const all=store.search({tenantId:'orchid', query:'account',category:'account',limit:20});
  const one=store.search({tenantId:'orchid', query:'account',category:'account',limit:1});
  assert(all.total>1);
  assert.equal(one.total,all.total);
  assert.equal(one.results.length,1);
});
test('blank searches remain deterministic and do not include archived material', () => {
  const store=createStore();
  const a=store.search({tenantId:'harbor',query:''});
  assert.deepEqual(a.results.map(x=>x.id),['hc-201','hc-202','hc-203']);
});
