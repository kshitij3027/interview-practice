#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m compileall -q server tests
if command -v node >/dev/null; then for file in public/*.js; do node --check "$file"; done; fi
