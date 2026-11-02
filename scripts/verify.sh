#!/usr/bin/env bash
set -euo pipefail
python3 cacheflow.py validate --tenants fixtures/tenants.csv --objects fixtures/objects.csv --events fixtures/events.jsonl --capacity-kb 12
