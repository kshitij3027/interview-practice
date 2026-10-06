#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q app tests
for f in web/*.js; do node --check "$f"; done
