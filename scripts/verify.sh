#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 costcanopy.py check --centers fixtures/centers.csv --operations fixtures/operations.jsonl
