#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 bundleport.py validate --releases fixtures/releases.csv --requirements fixtures/requirements.csv --conflicts fixtures/conflicts.csv --requests fixtures/requests.jsonl
