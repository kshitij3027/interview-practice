#!/usr/bin/env bash
set -euo pipefail
./scripts/build.sh
exec java -cp build/classes redactdesk.Main
