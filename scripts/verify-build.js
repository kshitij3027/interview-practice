import { execFileSync } from 'node:child_process';
const files=['server.js','src/dataStore.js','src/flagService.js','src/http.js','src/routes.js','web/api.js','web/store.js','web/app.js'];
for (const f of files) execFileSync(process.execPath,['--check',f],{stdio:'inherit'});
console.log(`Verified syntax for ${files.length} JavaScript runtime modules`);
