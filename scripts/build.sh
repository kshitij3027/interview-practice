#!/usr/bin/env bash
set -euo pipefail
rm -rf build/classes
mkdir -p build/classes
javac --release 21 -d build/classes $(find src/main/java -name '*.java' | sort)
node --check web/api.js
node --check web/store.js
node --check web/app.js
printf 'Build verified: Java sources compiled and browser modules passed syntax checks.\n'
