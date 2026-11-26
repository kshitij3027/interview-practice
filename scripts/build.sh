#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
find src public tests -name '*.php' -exec php -l {} \;
node --input-type=module --check < public/app.js
node --input-type=module --check < public/api.js
node --check tests/smoke.mjs
