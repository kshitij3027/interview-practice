#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q app tests
if command -v node >/dev/null 2>&1; then
  for f in public/*.js; do node --check "$f"; done
else
  echo 'Node unavailable; browser JavaScript syntax check skipped'
fi
printf 'Python compilation and browser JavaScript syntax checks passed\n'
