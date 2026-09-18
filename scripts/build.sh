#!/usr/bin/env bash
set -euo pipefail
rm -rf out
mkdir -p out
javac --release 21 -d out $(find src/main/java -name '*.java' -print)
