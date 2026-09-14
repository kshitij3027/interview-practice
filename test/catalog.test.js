import test from 'node:test';
import assert from 'node:assert/strict';
import { buildCatalog } from '../src/catalog.js';
import { parseCsv, recordsFromCsv } from '../src/csv.js';
import { normalizeHost, parsePathPattern, parseRequestPath } from '../src/patterns.js';

test('CSV parser handles quoted commas and escaped quotes', () => {
  const rows = parseCsv('a,b\n"x,y","say ""hi"""\n');
  assert.deepEqual(rows, [['a', 'b'], ['x,y', 'say "hi"']]);
});

test('exact duplicate route definitions are deduplicated', () => {
  const rows = recordsFromCsv('route_id,host_pattern,method,path_pattern,priority,upstream\nr1,api.example.com,GET,/x/{id},5,a\nr1,api.example.com,GET,/x/{id},5,a\n');
  const catalog = buildCatalog(rows);
  assert.equal(catalog.routes.length, 1);
});

test('conflicting reuse of a route id fails validation', () => {
  const rows = recordsFromCsv('route_id,host_pattern,method,path_pattern,priority,upstream\nr1,api.example.com,GET,/x,5,a\nr1,api.example.com,GET,/y,5,a\n');
  assert.throws(() => buildCatalog(rows), /conflicting definitions/);
});

test('path patterns enforce final multi-segment wildcard and unique params', () => {
  assert.deepEqual(parsePathPattern('/teams/{team}/members/*').segments.map((s) => s.kind), ['literal', 'param', 'literal', 'single']);
  assert.throws(() => parsePathPattern('/a/**/b'), /final segment/);
  assert.throws(() => parsePathPattern('/a/{id}/b/{id}'), /duplicate path parameter/);
});

test('hosts are case-insensitive and a terminal dot is ignored', () => {
  assert.equal(normalizeHost('API.Example.COM.'), 'api.example.com');
});

test('request paths must already be canonical', () => {
  assert.deepEqual(parseRequestPath('/a/b'), ['a', 'b']);
  assert.throws(() => parseRequestPath('/a//b'), /invalid canonical/);
  assert.throws(() => parseRequestPath('/a/'), /invalid canonical/);
});
