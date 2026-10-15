import { spawnSync } from 'node:child_process';
for (const file of ['src/data.mjs','src/store.mjs','src/http.mjs','src/validation.mjs','web/app.js','tests/starter.test.mjs','scripts/check.mjs','scripts/verify.mjs']) {
  const result = spawnSync(process.execPath, ['--check', file], { stdio: 'inherit' });
  if (result.status !== 0) process.exit(result.status || 1);
}
console.log('JavaScript syntax/build checks passed');
