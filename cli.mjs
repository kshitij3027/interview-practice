import {readFileSync} from 'node:fs';
import {normalize} from './catalog.mjs';
import {plan} from './planner.mjs';
try {
  if (process.argv.length !== 3) throw new Error('usage: node cli.mjs BATCH.json');
  const batch = normalize(JSON.parse(readFileSync(process.argv[2], 'utf8')));
  console.log(JSON.stringify(plan(batch)));
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
