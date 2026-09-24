#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m compileall -q flagdesk tests
node --check static/api.js
node --check static/app.js
python3 -m json.tool fixtures/flags.json >/dev/null
python3 -m json.tool fixtures/subjects.json >/dev/null
echo "Build and fixture verification passed"
