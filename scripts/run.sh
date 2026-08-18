#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/build.sh
exec java --add-modules jdk.httpserver -cp out fulfill.App 3001
