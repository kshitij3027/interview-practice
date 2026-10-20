import {execFileSync} from 'node:child_process';
for (const p of ['src/fixtures.mjs','src/errors.mjs','src/store.mjs','src/routes.mjs','src/server.mjs','web/api.js','web/app.js','tests/store.test.mjs','tests/http.test.mjs']) {
  execFileSync(process.execPath,['--check',p],{stdio:'pipe'});
}
console.log('Source and browser JavaScript syntax passed');
