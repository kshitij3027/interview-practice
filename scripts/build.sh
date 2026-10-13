#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for f in src/*.js web/*.js tests/*.js scripts/verify.js; do node --check "$f"; done
node -e "JSON.parse(require('fs').readFileSync('fixtures/catalog.json','utf8'))"
echo 'Syntax/build and fixture JSON checks passed'
