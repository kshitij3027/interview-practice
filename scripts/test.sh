#!/usr/bin/env bash
set -euo pipefail
rm -rf out-test
mkdir -p out-test
javac --release 21 -d out-test src/screenflow/*.java test/screenflow/StarterTest.java
java -cp out-test screenflow.StarterTest
