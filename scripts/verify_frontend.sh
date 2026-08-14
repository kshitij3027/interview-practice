#!/usr/bin/env bash
set -euo pipefail
for file in frontend/src/*.js; do node --check "$file"; done
test -f frontend/index.html
test -f frontend/src/styles.css
echo "frontend syntax/build baseline OK"
