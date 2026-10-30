#!/usr/bin/env bash
set -euo pipefail
bash scripts/build.sh
bash scripts/test.sh
python3 signalgate.py check --regions fixtures/regions.csv --signatures fixtures/signatures.csv --requests fixtures/requests.jsonl
