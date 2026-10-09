#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m compileall -q claimsignal claimsignal.py tests
python3 claimsignal.py validate --rules fixtures/rules.csv --cases fixtures/cases.jsonl
