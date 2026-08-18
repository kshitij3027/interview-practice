#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf out-test && mkdir -p out-test
javac --add-modules jdk.httpserver -d out-test src/*.java test/*.java
java -ea --add-modules jdk.httpserver -cp out-test fulfill.TestRunner
