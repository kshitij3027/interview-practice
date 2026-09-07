#!/usr/bin/env sh
set -eu
python3 -m compileall -q migration bridge_plan.py tests
python3 bridge_plan.py validate --schemas fixtures/schemas.csv --adapters fixtures/adapters.csv --requests fixtures/requests.jsonl
