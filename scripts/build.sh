#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for f in src/*.js public/*.js tests/*.test.js; do node --check "$f"; done
printf 'All JavaScript syntax checks passed.\n'
