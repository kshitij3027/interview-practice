#!/usr/bin/env bash
set -euo pipefail
python3 gatequeue.py validate \
  --workflows fixtures/workflows.csv \
  --tasks fixtures/tasks.csv \
  --dependencies fixtures/dependencies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.jsonl
