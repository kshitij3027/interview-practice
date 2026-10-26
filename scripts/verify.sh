#!/usr/bin/env bash
set -euo pipefail
python3 aidlink.py check --depots fixtures/depots.csv --clinics fixtures/clinics.csv --lanes fixtures/lanes.csv --requests fixtures/requests.jsonl
