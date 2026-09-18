#!/usr/bin/env bash
set -euo pipefail
./scripts/test.sh
./scripts/build.sh
java -cp out signalmesh.Main validate \
  --accounts fixtures/accounts.csv \
  --policies fixtures/policies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.csv
