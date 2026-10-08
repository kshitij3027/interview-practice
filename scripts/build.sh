#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for path in server.js lib/*.js public/*.js tests/*.js; do node --check "$path"; done
printf 'JavaScript syntax checks passed\n'
