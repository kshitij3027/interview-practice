#!/usr/bin/env bash
set -euo pipefail
python3 locker_search.py validate --lockers fixtures/lockers.csv --queries fixtures/queries.jsonl
