#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for file in src/*.js web/*.js tests/*.js; do node --check "$file"; done
printf 'JavaScript syntax checks passed\n'
