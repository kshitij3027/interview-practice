import { loadCatalog, loadQueries } from '../src/catalog.js';
import { parseMethod, normalizeHost, parseRequestPath } from '../src/patterns.js';

const catalog = loadCatalog('fixtures/routes.csv');
const queries = loadQueries('fixtures/queries.jsonl');
for (const q of queries) {
  parseMethod(q.method);
  normalizeHost(q.host);
  parseRequestPath(q.path);
}
if (catalog.routes.length !== 16) throw new Error(`expected 16 unique routes, got ${catalog.routes.length}`);
if (queries.length !== 12) throw new Error(`expected 12 queries, got ${queries.length}`);
console.log(`fixture verification passed: ${catalog.routes.length} unique routes / ${queries.length} queries`);
