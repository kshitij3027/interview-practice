#!/usr/bin/env bash
set -euo pipefail
python3 velocity_rank.py validate \
  --clients fixtures/clients.csv \
  --policies fixtures/policies.csv \
  --events fixtures/events.csv \
  --queries fixtures/queries.jsonl
