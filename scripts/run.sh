#!/usr/bin/env bash
set -euo pipefail
./scripts/build.sh
exec java -cp out screenflow.Main "${PORT:-8080}"
