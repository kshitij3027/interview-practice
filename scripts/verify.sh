#!/usr/bin/env bash
set -euo pipefail
python3 -B freshclaim.py check --lots fixtures/lots.csv
python3 -B freshclaim.py assess --lots fixtures/lots.csv --requests fixtures/requests.jsonl > /dev/null
