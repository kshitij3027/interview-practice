#!/usr/bin/env bash
set -euo pipefail
node --check suggest.js
node --check src/read.js
node --check src/csv.js
node --check src/normalize.js
node --check src/catalog.js
node --check src/queries.js
node --check src/suggester.js
node --check tests/starter.test.js
