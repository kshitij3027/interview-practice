import { execFileSync } from 'node:child_process';
const files = ['server.js','src/dataStore.js','src/experimentService.js','src/funnel.js','src/http.js','src/routes.js','web/api.js','web/store.js','web/reportGuards.js','web/app.js'];
for (const file of files) execFileSync(process.execPath, ['--check', file], { stdio: 'inherit' });
console.log(`Verified syntax for ${files.length} JavaScript modules.`);
