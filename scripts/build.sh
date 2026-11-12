#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m compileall -q app tests
if command -v node >/dev/null 2>&1; then node --check public/app.js; fi
echo 'Build/syntax checks passed'
