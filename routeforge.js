#!/usr/bin/env node
import { loadCatalog, loadQueries } from './src/catalog.js';
import { RouteResolver } from './src/resolver.js';

function usage() {
  console.error('Usage:');
  console.error('  node routeforge.js validate --routes fixtures/routes.csv --queries fixtures/queries.jsonl');
  console.error('  node routeforge.js resolve  --routes fixtures/routes.csv --queries fixtures/queries.jsonl');
}

function parseArgs(argv) {
  if (argv.length < 1) return null;
  const command = argv[0];
  const options = {};
  for (let i = 1; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (!key?.startsWith('--') || value === undefined) return null;
    options[key.slice(2)] = value;
  }
  return { command, options };
}

const parsed = parseArgs(process.argv.slice(2));
if (!parsed || !['validate', 'resolve'].includes(parsed.command) || !parsed.options.routes || !parsed.options.queries) {
  usage();
  process.exit(2);
}

try {
  const catalog = loadCatalog(parsed.options.routes);
  const queries = loadQueries(parsed.options.queries);
  if (parsed.command === 'validate') {
    console.log(`validated ${catalog.routes.length} unique routes / ${queries.length} queries`);
    process.exit(0);
  }

  const resolver = new RouteResolver(catalog);
  for (const query of queries) {
    console.log(JSON.stringify(resolver.resolve(query)));
  }
} catch (err) {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
}
