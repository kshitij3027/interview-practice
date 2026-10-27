#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m compileall -q server.py permitlens tests scripts/check_fixtures.py
if command -v node >/dev/null 2>&1; then
  node --check frontend/app.js
  node --check frontend/api.js
else
  echo 'Node unavailable: frontend syntax check skipped; browser remains dependency-free.'
fi
echo 'Build/syntax verification passed.'
