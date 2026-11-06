#!/usr/bin/env bash
set -euo pipefail
python3 relay.py --help >/dev/null
python3 relay.py --hubs fixtures/hubs.csv --services fixtures/services.csv --requests fixtures/requests.jsonl > /dev/null
