#!/usr/bin/env bash
set -euo pipefail
rm -rf build/test-classes
mkdir -p build/test-classes
javac --release 21 -d build/test-classes $(find src/main/java test/java -name '*.java' | sort)
java -cp build/test-classes redactdesk.StoreTest
java -cp build/test-classes redactdesk.RoutesTest
