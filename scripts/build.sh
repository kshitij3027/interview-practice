#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ruby -c server.rb >/dev/null
for f in lib/*.rb test/*.rb; do ruby -c "$f" >/dev/null; done
for f in web/*.js; do node --check "$f"; done
echo "Build verification passed"
