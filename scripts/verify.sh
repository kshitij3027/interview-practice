#!/usr/bin/env bash
set -euo pipefail
bash scripts/build.sh
bash scripts/test.sh
python3 signalwatch.py check --tenants fixtures/tenants.csv --signatures fixtures/signatures.csv
python3 signalwatch.py scan --tenants fixtures/tenants.csv --signatures fixtures/signatures.csv --events fixtures/invalid_only.jsonl
