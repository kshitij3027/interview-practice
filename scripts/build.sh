#!/usr/bin/env bash
set -euo pipefail
for file in src/*.js public/*.js scripts/verify.js; do
  node --check "$file"
done
node scripts/verify.js
