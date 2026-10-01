#!/usr/bin/env bash
set -euo pipefail
rm -rf out
mkdir -p out
javac --release 21 -d out src/screenflow/*.java
node --check web/api.js
node --check web/store.js
node --check web/app.js
echo "build checks passed"
