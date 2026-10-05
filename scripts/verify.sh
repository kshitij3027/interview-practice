#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 queuepulse_cli.py validate --queues fixtures/queues.csv --events fixtures/events.csv --queries fixtures/queries.csv
