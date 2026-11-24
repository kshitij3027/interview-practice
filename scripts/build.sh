#!/usr/bin/env bash
set -euo pipefail
for f in server.rb lib/*.rb test/*.rb; do ruby -c "$f"; done
for f in public/*.js; do node --input-type=module --check < "$f"; done
