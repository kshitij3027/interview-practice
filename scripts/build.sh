#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf out && mkdir -p out
javac --add-modules jdk.httpserver -d out src/*.java
node --check web/api.js
node --check web/store.js
node --check web/app.js
echo "Build verified"
