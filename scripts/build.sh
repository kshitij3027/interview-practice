#!/usr/bin/env bash
set -euo pipefail
node --check src/validation.js
node --check src/store.js
node --check src/http.js
node --check src/server.js
node --check public/app.js
node -e 'JSON.parse(require("fs").readFileSync("fixtures/grants.json","utf8")); JSON.parse(require("fs").readFileSync("fixtures/review_cycle.json","utf8")); console.log("fixture parse passed")'
