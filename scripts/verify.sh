#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 compat_plan.py validate --packages fixtures/packages.csv --versions fixtures/versions.csv --dependencies fixtures/dependencies.csv --installed fixtures/installed.csv --requests fixtures/requests.jsonl
