#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m compileall -q src server.py
node --check web/api.js
node --check web/store.js
node --check web/app.js
echo "Build verification passed"
