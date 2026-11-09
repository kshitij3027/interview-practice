#!/usr/bin/env bash
set -euo pipefail
python3 transitsafe.py check --stations fixtures/stations.csv --fares fixtures/fares.csv --rides fixtures/rides.csv
python3 transitsafe.py plan --stations fixtures/stations.csv --fares fixtures/fares.csv --rides fixtures/rides.csv --queries fixtures/requests.jsonl > /dev/null
